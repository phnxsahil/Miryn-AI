from fastapi import APIRouter, HTTPException, status, Request, Depends
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from postgrest import APIError as PostgrestAPIError
import logging
import secrets
from datetime import datetime
from app.core.database import get_db, has_sql, get_sql_session
from app.core.security import get_password_hash, verify_password, create_access_token, get_current_user_id, get_user_id_from_token
from app.core.cache import redis_client
from app.core.audit import log_event
from app.config import settings
from app.schemas.auth import SignupRequest, LoginRequest, TokenResponse, UserOut, ForgotPasswordRequest, ResetPasswordRequest

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


@router.post("/signup", response_model=UserOut)
def signup(payload: SignupRequest, request: Request):
    client_host = _client_host(request)
    if has_sql():
        with get_sql_session() as session:
            try:
                result = session.execute(
                    text(
                        """
                        INSERT INTO users (email, password_hash)
                        VALUES (:email, :password_hash)
                        RETURNING id, email
                        """
                    ),
                    {"email": payload.email, "password_hash": get_password_hash(payload.password)},
                ).mappings().first()
            except IntegrityError as exc:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered") from exc

            if not result:
                result = session.execute(
                    text("SELECT id, email FROM users WHERE email = :email LIMIT 1"),
                    {"email": payload.email},
                ).mappings().first()

            if not result:
                raise HTTPException(status_code=500, detail="Failed to create user")

        log_event(
            event_type="auth.signup",
            user_id=str(result["id"]),
            path=str(request.url.path),
            method=request.method,
            status_code=200,
            ip=client_host,
            user_agent=request.headers.get("user-agent"),
        )

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
    return {"id": str(created.get("id")), "email": created.get("email")}


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

        token = create_access_token(subject=str(user["id"]))
        log_event(
            event_type="auth.login",
            user_id=user["id"],
            path=str(request.url.path),
            method=request.method,
            status_code=200,
            ip=client_host,
            user_agent=request.headers.get("user-agent"),
        )
        return TokenResponse(access_token=token)

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

    token = create_access_token(subject=str(user["id"]))
    log_event(
        event_type="auth.login",
        user_id=user["id"],
        path=str(request.url.path),
        method=request.method,
        status_code=200,
        ip=client_host,
        user_agent=request.headers.get("user-agent"),
    )
    return TokenResponse(access_token=token)


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(request: Request):
    auth_header = request.headers.get("authorization", "")
    if not auth_header.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing authentication token")
    token = auth_header.split(" ", 1)[1].strip()
    user_id = get_user_id_from_token(token)
    new_token = create_access_token(subject=str(user_id))
    return TokenResponse(access_token=new_token)


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
        logger.info("Reset token for %s: %s", email, token)

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
