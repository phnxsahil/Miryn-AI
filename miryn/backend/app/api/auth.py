from fastapi import APIRouter, HTTPException, status, Request, Depends
from uuid import uuid4
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from postgrest import APIError as PostgrestAPIError
import logging
import secrets
from datetime import datetime
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from app.core.database import get_db, has_sql, get_sql_session
from app.core.security import get_password_hash, verify_password, create_access_token, create_refresh_token, get_current_user_id, get_user_id_from_refresh_token
from app.core.cache import redis_client
from app.core.audit import log_event
from app.config import settings
from app.services.email_service import send_password_reset, send_welcome_email
from app.schemas.auth import SignupRequest, LoginRequest, TokenResponse, UserOut, ForgotPasswordRequest, ResetPasswordRequest, GoogleLoginRequest, PasswordUpdate, SessionOut, RefreshTokenRequest

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger(__name__)

LOGIN_GUARD_SCRIPT = """
local attempts = redis.call('INCR', KEYS[1])
if attempts == 1 then
  redis.call('EXPIRE', KEYS[1], ARGV[1])
end
return attempts
"""


def _client_host(request: Request) -> str:
    if request.client and request.client.host:
        return request.client.host
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return "unknown"


def _login_guard(key: str):
    try:
        attempts = redis_client.eval(
            LOGIN_GUARD_SCRIPT,
            1,
            key,
            settings.LOGIN_ATTEMPT_WINDOW_SECONDS,
        )
    except Exception:
        # Fail open if Redis is unavailable
        return

    if int(attempts) > settings.LOGIN_ATTEMPT_LIMIT:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Try again later.",
        )


def _is_unique_violation(exc: Exception) -> bool:
    code = getattr(exc, "code", None)
    if code == "23505":
        return True

    for attr in ("details", "message", "hint"):
        val = getattr(exc, attr, None)
        if isinstance(val, str) and ("23505" in val or "duplicate key" in val.lower()):
            return True

    args0 = exc.args[0] if getattr(exc, "args", None) else None
    if isinstance(args0, dict):
        code = args0.get("code") or args0.get("error") or args0.get("status_code")
        if str(code) == "23505":
            return True
        msg = args0.get("message") or args0.get("details") or ""
        if isinstance(msg, str) and ("23505" in msg or "duplicate key" in msg.lower()):
            return True

    if "23505" in str(exc) or "duplicate key" in str(exc).lower():
        return True

    return False


def _issue_token_response(user_id: str, email: str | None = None, is_new: bool = False) -> TokenResponse:
    access_token = create_access_token(subject=user_id)
    refresh_token = create_refresh_token(subject=user_id)
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        refresh_expires_in=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        is_new=is_new,
        user={"id": user_id, "email": email} if email else {"id": user_id},
    )


def _default_notification_preferences() -> dict[str, bool]:
    return {
        "checkin_reminders": True,
        "weekly_digest": True,
        "browser_push": False,
    }


def _store_google_profile(user_id: str, idinfo: dict) -> None:
    """Keep the Google display name and avatar on the profile.

    The COALESCE on the SQL path and the presence checks on the Supabase path
    mean a name typed at signup is never overwritten by whatever Google returns.
    """
    full_name = str(idinfo.get("name") or "").strip() or None
    avatar_url = str(idinfo.get("picture") or "").strip() or None
    if not full_name and not avatar_url:
        return

    try:
        if has_sql():
            with get_sql_session() as session:
                session.execute(
                    text(
                        """
                        INSERT INTO user_profiles (user_id, full_name, avatar_url)
                        VALUES (:user_id, :full_name, :avatar_url)
                        ON CONFLICT (user_id) DO UPDATE
                        SET full_name = COALESCE(user_profiles.full_name, EXCLUDED.full_name),
                            avatar_url = COALESCE(user_profiles.avatar_url, EXCLUDED.avatar_url)
                        """
                    ),
                    {"user_id": user_id, "full_name": full_name, "avatar_url": avatar_url},
                )
            return

        db = get_db()
        existing = (
            db.table("user_profiles")
            .select("user_id, full_name, avatar_url")
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )
        row = (existing.data or [None])[0]
        if not row:
            db.table("user_profiles").insert(
                {"user_id": user_id, "full_name": full_name, "avatar_url": avatar_url}
            ).execute()
            return

        patch: dict[str, str] = {}
        if full_name and not row.get("full_name"):
            patch["full_name"] = full_name
        if avatar_url and not row.get("avatar_url"):
            patch["avatar_url"] = avatar_url
        if patch:
            db.table("user_profiles").update(patch).eq("user_id", user_id).execute()
    except Exception as exc:
        logger.warning("Could not store Google profile for %s: %s", user_id, exc)


def _get_full_name(user_id: str) -> str | None:
    try:
        if has_sql():
            with get_sql_session() as session:
                row = session.execute(
                    text("SELECT full_name FROM user_profiles WHERE user_id = :user_id LIMIT 1"),
                    {"user_id": user_id},
                ).mappings().first()
                return row.get("full_name") if row else None

        db = get_db()
        res = (
            db.table("user_profiles")
            .select("full_name")
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )
        row = (res.data or [None])[0]
        return row.get("full_name") if row else None
    except Exception as exc:
        logger.warning("Could not read profile for %s: %s", user_id, exc)
        return None


@router.get("/config")
def auth_config():
    """Which sign-in providers this deployment can actually finish.

    The frontend renders the Google button from a public client id, which says
    nothing about whether the server holds the matching id needed to verify the
    token. This lets the two sides agree before a user clicks.
    """
    return {"providers": {"google": bool(settings.GOOGLE_CLIENT_ID)}}


@router.post("/signup", response_model=UserOut)
def signup(payload: SignupRequest, request: Request):
    client_host = _client_host(request)
    if has_sql():
        with get_sql_session() as session:
            try:
                session.execute(
                    text(
                        """
                        INSERT INTO users (id, email, password_hash)
                        VALUES (:id, :email, :password_hash)
                        """
                    ),
                    {"id": str(uuid4()), "email": payload.email, "password_hash": get_password_hash(payload.password)},
                )
            except IntegrityError as exc:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered") from exc

            result = session.execute(
                text("SELECT id, email FROM users WHERE email = :email LIMIT 1"),
                {"email": payload.email},
            ).mappings().first()

            if not result:
                raise HTTPException(status_code=500, detail="Failed to create user")

            # The name is asked once, at signup; onboarding skips its name step
            # when a profile already carries one.
            if payload.full_name:
                try:
                    session.execute(
                        text(
                            """
                            INSERT INTO user_profiles (user_id, full_name)
                            VALUES (:user_id, :full_name)
                            ON CONFLICT (user_id) DO UPDATE SET full_name = EXCLUDED.full_name
                            """
                        ),
                        {"user_id": str(result["id"]), "full_name": payload.full_name},
                    )
                except Exception as exc:
                    logger.warning("Could not store full name for %s: %s", result["id"], exc)

        log_event(
            event_type="auth.signup",
            user_id=str(result["id"]),
            path=str(request.url.path),
            method=request.method,
            status_code=200,
            ip=client_host,
            user_agent=request.headers.get("user-agent"),
        )

        send_welcome_email(payload.email)

        return {"id": str(result["id"]), "email": result["email"]}

    db = get_db()
    try:
        user = (
            db.table("users")
            .insert({
                "email": payload.email,
                "password_hash": get_password_hash(payload.password),
            })
            .execute()
        )
    except PostgrestAPIError as exc:
        if _is_unique_violation(exc):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered") from exc
        raise

    if not getattr(user, "data", None):
        raise HTTPException(status_code=500, detail="Failed to create user")

    log_event(
        event_type="auth.signup",
        user_id=str(user.data[0].get("id")),
        path=str(request.url.path),
        method=request.method,
        status_code=200,
        ip=client_host,
        user_agent=request.headers.get("user-agent"),
    )

    created = user.data[0]

    if payload.full_name:
        try:
            db.table("user_profiles").insert(
                {"user_id": str(created.get("id")), "full_name": payload.full_name}
            ).execute()
        except Exception as exc:
            logger.warning("Could not store full name for %s: %s", created.get("id"), exc)

    return {"id": str(created.get("id")), "email": created.get("email")}


@router.post("/google", response_model=TokenResponse)
def google_auth(payload: GoogleLoginRequest, request: Request):
    client_host = _client_host(request)
    try:
        idinfo = id_token.verify_oauth2_token(
            payload.id_token, google_requests.Request(), settings.GOOGLE_CLIENT_ID
        )
        email = idinfo["email"]
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Google token"
        ) from exc

    user_id = None
    is_new = False
    if has_sql():
        with get_sql_session() as session:
            user = session.execute(
                text("SELECT id, is_deleted FROM users WHERE email = :email LIMIT 1"),
                {"email": email},
            ).mappings().first()

            if user:
                if user.get("is_deleted"):
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Account is deleted",
                    )
                user_id = str(user["id"])
            else:
                # Create new user
                is_new = True
                try:
                    new_user = session.execute(
                        text(
                            """
                            INSERT INTO users (email)
                            VALUES (:email)
                            RETURNING id
                            """
                        ),
                        {"email": email},
                    ).mappings().first()
                    if new_user:
                        user_id = str(new_user["id"])
                        session.commit()
                except IntegrityError:
                    # Fallback in case of race condition
                    is_new = False
                    user = session.execute(
                        text("SELECT id FROM users WHERE email = :email LIMIT 1"),
                        {"email": email},
                    ).mappings().first()
                    if user:
                        user_id = str(user["id"])

    else:
        db = get_db()
        response = (
            db.table("users")
            .select("id, is_deleted")
            .eq("email", email)
            .limit(1)
            .execute()
        )

        if response.data:
            user = response.data[0]
            if user.get("is_deleted"):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Account is deleted",
                )
            user_id = str(user["id"])
        else:
            # Create new user
            is_new = True
            try:
                new_user_res = db.table("users").insert({"email": email}).execute()
                if new_user_res.data:
                    user_id = str(new_user_res.data[0]["id"])
            except PostgrestAPIError as exc:
                if _is_unique_violation(exc):
                    is_new = False
                    user_res = db.table("users").select("id").eq("email", email).limit(1).execute()
                    if user_res.data:
                        user_id = str(user_res.data[0]["id"])
                else:
                    raise

    if not user_id:
        raise HTTPException(status_code=500, detail="Failed to authenticate user")

    _store_google_profile(user_id, idinfo)

    log_event(
        event_type="auth.google",
        user_id=user_id,
        path=str(request.url.path),
        method=request.method,
        status_code=200,
        ip=client_host,
        user_agent=request.headers.get("user-agent"),
    )
    return _issue_token_response(user_id=user_id, email=email, is_new=is_new)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request):
    client_host = _client_host(request)
    key = f"login:{payload.email}" if payload.email else f"login:{client_host}"
    _login_guard(key)

    if has_sql():
        with get_sql_session() as session:
            user = session.execute(
                text("SELECT id, email, password_hash, is_deleted FROM users WHERE email = :email LIMIT 1"),
                {"email": payload.email},
            ).mappings().first()

        if not user or not user.get("password_hash"):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        if user.get("is_deleted"):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

        if not verify_password(payload.password, user["password_hash"]):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

        log_event(
            event_type="auth.login",
            user_id=user["id"],
            path=str(request.url.path),
            method=request.method,
            status_code=200,
            ip=client_host,
            user_agent=request.headers.get("user-agent"),
        )
        return _issue_token_response(user_id=str(user["id"]), email=str(user["email"]))

    db = get_db()

    response = (
        db.table("users")
        .select("id, email, password_hash, is_deleted")
        .eq("email", payload.email)
        .limit(1)
        .execute()
    )

    if not response.data:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    user = response.data[0]
    if user.get("is_deleted"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.get("password_hash") or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    log_event(
        event_type="auth.login",
        user_id=user["id"],
        path=str(request.url.path),
        method=request.method,
        status_code=200,
        ip=client_host,
        user_agent=request.headers.get("user-agent"),
    )
    return _issue_token_response(user_id=str(user["id"]), email=str(user["email"]))


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(request: Request, payload: RefreshTokenRequest | None = None):
    refresh_token_value = payload.refresh_token if payload else None

    if not refresh_token_value:
        auth_header = request.headers.get("authorization", "")
        if auth_header.lower().startswith("bearer "):
            refresh_token_value = auth_header.split(" ", 1)[1].strip()

    if not refresh_token_value:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing refresh token")

    user_id = get_user_id_from_refresh_token(refresh_token_value)

    email = None
    if has_sql():
        with get_sql_session() as session:
            user = session.execute(
                text("SELECT id, email, is_deleted FROM users WHERE id = :user_id LIMIT 1"),
                {"user_id": user_id},
            ).mappings().first()
            if not user or user.get("is_deleted"):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Account not available")
            email = str(user["email"])
    else:
        db = get_db()
        res = db.table("users").select("id, email, is_deleted").eq("id", user_id).limit(1).execute()
        user = res.data[0] if res.data else None
        if not user or user.get("is_deleted"):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Account not available")
        email = str(user["email"])

    return _issue_token_response(user_id=str(user_id), email=email)


@router.post("/forgot-password")
def forgot_password(payload: ForgotPasswordRequest):
    email = payload.email
    user_id = None

    if has_sql():
        with get_sql_session() as session:
            row = session.execute(
                text("SELECT id FROM users WHERE email = :email LIMIT 1"),
                {"email": email},
            ).mappings().first()
            if row:
                user_id = str(row.get("id"))
    else:
        db = get_db()
        response = (
            db.table("users")
            .select("id")
            .eq("email", email)
            .limit(1)
            .execute()
        )
        if response.data:
            user_id = str(response.data[0].get("id"))

    if user_id:
        token = secrets.token_urlsafe(32)
        key = f"pwreset:{token}"
        try:
            redis_client.setex(key, 900, user_id)
        except Exception:
            pass
        send_password_reset(email, token)

    return {"message": "If this email exists a reset link was sent"}


@router.post("/reset-password")
def reset_password(payload: ResetPasswordRequest):
    key = f"pwreset:{payload.token}"
    user_id = None
    try:
        user_id = redis_client.get(key)
    except Exception:
        user_id = None

    if not user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token")

    if has_sql():
        with get_sql_session() as session:
            session.execute(
                text("UPDATE users SET password_hash = :hash WHERE id = :user_id"),
                {"hash": get_password_hash(payload.new_password), "user_id": user_id},
            )
    else:
        db = get_db()
        db.table("users").update({"password_hash": get_password_hash(payload.new_password)}).eq("id", user_id).execute()

    try:
        redis_client.delete(key)
    except Exception:
        pass

    return {"message": "Password updated successfully"}


@router.delete("/account")
def delete_account(user_id: str = Depends(get_current_user_id)):
    anonymized = f"deleted_{user_id}@deleted.miryn"
    if has_sql():
        with get_sql_session() as session:
            session.execute(
                text(
                    """
                    UPDATE users
                    SET is_deleted = true,
                        deleted_at = NOW(),
                        email = :email
                    WHERE id = :user_id
                    """
                ),
                {"email": anonymized, "user_id": user_id},
            )
    else:
        db = get_db()
        db.table("users").update(
            {"is_deleted": True, "deleted_at": datetime.utcnow().isoformat(), "email": anonymized}
        ).eq("id", user_id).execute()

    return {"message": "Account deleted"}


@router.get("/me")
def get_me(user_id: str = Depends(get_current_user_id)):
    if has_sql():
        try:
            with get_sql_session() as session:
                user = session.execute(
                    text("SELECT id, email, password_hash, notification_preferences, data_retention FROM users WHERE id = :user_id"),
                    {"user_id": user_id},
                ).mappings().first()
        except Exception as exc:
            logger.warning("Extended /auth/me query failed, falling back to base user query: %s", exc)
            with get_sql_session() as session:
                user = session.execute(
                    text("SELECT id, email, password_hash FROM users WHERE id = :user_id"),
                    {"user_id": user_id},
                ).mappings().first()
    else:
        db = get_db()
        try:
            res = db.table("users").select("id, email, password_hash, notification_preferences, data_retention").eq("id", user_id).single().execute()
            user = res.data
        except Exception as exc:
            logger.warning("Extended Supabase /auth/me query failed, falling back to base user query: %s", exc)
            res = db.table("users").select("id, email, password_hash").eq("id", user_id).single().execute()
            user = res.data

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "id": str(user["id"]),
        "email": user["email"],
        "full_name": _get_full_name(user_id),
        "has_password": user["password_hash"] is not None,
        "notification_preferences": user.get("notification_preferences") or _default_notification_preferences(),
        "data_retention": user.get("data_retention") or "forever",
        "encryption_enabled": settings.ENCRYPTION_KEY is not None and len(settings.ENCRYPTION_KEY) > 0
    }


@router.patch("/password")
def update_password(payload: PasswordUpdate, user_id: str = Depends(get_current_user_id)):
    if has_sql():
        with get_sql_session() as session:
            user = session.execute(
                text("SELECT password_hash FROM users WHERE id = :user_id"),
                {"user_id": user_id},
            ).mappings().first()
            
            if not user or not user["password_hash"] or not verify_password(payload.current_password, user["password_hash"]):
                raise HTTPException(status_code=400, detail="Invalid current password")
            
            session.execute(
                text("UPDATE users SET password_hash = :hash WHERE id = :user_id"),
                {"hash": get_password_hash(payload.new_password), "user_id": user_id},
            )
            session.commit()
    else:
        db = get_db()
        res = db.table("users").select("password_hash").eq("id", user_id).single().execute()
        user = res.data
        if not user or not user["password_hash"] or not verify_password(payload.current_password, user["password_hash"]):
            raise HTTPException(status_code=400, detail="Invalid current password")
        
        db.table("users").update({"password_hash": get_password_hash(payload.new_password)}).eq("id", user_id).execute()
        
    return {"message": "Password updated"}


@router.get("/sessions", response_model=list[SessionOut])
def get_sessions(user_id: str = Depends(get_current_user_id)):
    if has_sql():
        with get_sql_session() as session:
            rows = session.execute(
                text(
                    """
                    SELECT ip, created_at as timestamp
                    FROM audit_logs
                    WHERE user_id = :user_id AND event_type = 'auth.login'
                    ORDER BY created_at DESC
                    LIMIT 5
                    """
                ),
                {"user_id": user_id},
            ).mappings().all()
            return [dict(row) for row in rows]
    else:
        db = get_db()
        res = db.table("audit_logs").select("ip, created_at").eq("user_id", user_id).eq("event_type", "auth.login").order("created_at", desc=True).limit(5).execute()
        return [{"ip": r["ip"], "timestamp": r["created_at"]} for r in (res.data or [])]
