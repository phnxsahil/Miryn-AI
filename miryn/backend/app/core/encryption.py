import base64
import hashlib
import logging
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken

from app.config import settings


logger = logging.getLogger(__name__)


def _normalize_key(raw_key: str) -> Optional[bytes]:
    trimmed = (raw_key or "").strip()
    if not trimmed:
        return None
    candidate = trimmed.encode("utf-8")
    if len(trimmed) == 44:
        try:
            base64.urlsafe_b64decode(candidate)
            return candidate
        except Exception:
            pass
    digest = hashlib.sha256(candidate).digest()
    return base64.urlsafe_b64encode(digest)


def _get_fernet() -> Optional[Fernet]:
    key = settings.ENCRYPTION_KEY
    if not key:
        return None
    try:
        normalized = _normalize_key(key)
        if not normalized:
            return None
        return Fernet(normalized)
    except Exception as exc:
        logger.warning("Invalid ENCRYPTION_KEY: %s", exc)
        return None


def encrypt_text(plain: str) -> Optional[str]:
    if plain is None:
        return None
    f = _get_fernet()
    if not f:
        return None
    token = f.encrypt(plain.encode("utf-8"))
    return token.decode("utf-8")


def decrypt_text(token: Optional[str]) -> Optional[str]:
    if not token:
        return None
    f = _get_fernet()
    if not f:
        return None
    try:
        return f.decrypt(token.encode("utf-8")).decode("utf-8")
    except InvalidToken:
        logger.warning("Failed to decrypt token")
        return None
