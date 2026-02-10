from fastapi import APIRouter, HTTPException, status, Request
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from postgrest import APIError as PostgrestAPIError
from app.core.database import get_db, has_sql, get_sql_session
from app.core.security import get_password_hash, verify_password, create_access_token
from app.core.cache import redis_client
from app.core.audit import log_event
from app.config import settings
from app.schemas.auth import SignupRequest, LoginRequest, TokenResponse, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])

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

        log_event(
            event_type="auth.signup",
            user_id=result["id"],
            path=str(request.url.path),
            method=request.method,
            status_code=200,
            ip=client_host,
            user_agent=request.headers.get("user-agent"),
        )

        return result

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
        if getattr(exc, "code", "") == "23505":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered") from exc
        raise

    log_event(
        event_type="auth.signup",
        user_id=user.data[0]["id"],
        path=str(request.url.path),
        method=request.method,
        status_code=200,
        ip=client_host,
        user_agent=request.headers.get("user-agent"),
    )

    return user.data[0]


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request):
    client_host = _client_host(request)
    key = f"login:{payload.email}" if payload.email else f"login:{client_host}"
    _login_guard(key)

    if has_sql():
        with get_sql_session() as session:
            user = session.execute(
                text("SELECT id, email, password_hash FROM users WHERE email = :email LIMIT 1"),
                {"email": payload.email},
            ).mappings().first()

        if not user or not user.get("password_hash"):
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
        .select("id, email, password_hash")
        .eq("email", payload.email)
        .limit(1)
        .execute()
    )

    if not response.data:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    user = response.data[0]
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
