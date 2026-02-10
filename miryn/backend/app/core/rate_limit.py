from typing import Optional
import logging
import hashlib
import ipaddress
import jwt
from jwt import InvalidTokenError
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.cache import redis_client
from app.config import settings


logger = logging.getLogger(__name__)

RATE_LIMIT_SCRIPT = """
local current = redis.call('INCR', KEYS[1])
if current == 1 then
    redis.call('EXPIRE', KEYS[1], ARGV[1])
end
return current
"""


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.limit = settings.RATE_LIMIT_PER_MINUTE

    async def dispatch(self, request: Request, call_next):
        identifier = self._get_identifier(request)
        key = f"rl:{identifier}"

        try:
            current = redis_client.eval(RATE_LIMIT_SCRIPT, 1, key, 60)
        except Exception as exc:
            logger.warning("Rate limiter unavailable, allowing request: %s", exc)
            return await call_next(request)

        if int(current) > self.limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded",
            )

        response = await call_next(request)
        return response

    def _get_identifier(self, request: Request) -> str:
        user_id = self._extract_user_id(request)
        if user_id:
            return f"user:{user_id}"

        client_ip = self._get_client_ip(request)
        return f"ip:{client_ip}"

    def _get_client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            for part in forwarded.split(","):
                candidate = part.strip()
                if self._is_valid_ip(candidate):
                    return candidate

        host = request.client.host if request.client and request.client.host else None
        if self._is_valid_ip(host):
            return host  # type: ignore[arg-type]

        fingerprint_source = f"{request.headers.get('user-agent','unknown')}|{request.url.hostname or 'unknown'}"
        fingerprint = hashlib.sha256(fingerprint_source.encode("utf-8")).hexdigest()[:10]
        return f"unknown-{fingerprint}"

    @staticmethod
    def _is_valid_ip(value: Optional[str]) -> bool:
        if not value:
            return False
        try:
            ipaddress.ip_address(value)
            return True
        except ValueError:
            return False

    def _extract_user_id(self, request: Request) -> Optional[str]:
        auth_header = request.headers.get("authorization")
        if not auth_header or not auth_header.lower().startswith("bearer "):
            return None
        token = auth_header.split(" ", 1)[1].strip()
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        except InvalidTokenError:
            return None
        user_id = payload.get("sub")
        return str(user_id) if user_id else None
