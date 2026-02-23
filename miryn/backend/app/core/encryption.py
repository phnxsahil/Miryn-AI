import base64
import hashlib
import logging
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken

from app.config import settings


logger = logging.getLogger(__name__)


def _normalize_key(raw_key: str) -> Optional[bytes]:
    """
    Normalize a raw encryption key string into a 44-byte URL-safe base64 key suitable for Fernet, or return None when no key is provided.
    
    Parameters:
        raw_key (str): The raw key string (e.g., from configuration); may include surrounding whitespace.
    
    Returns:
        Optional[bytes]: A 44-byte URL-safe base64-encoded key as bytes suitable for constructing a Fernet instance, or `None` if `raw_key` is empty after trimming.
    """
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
    """
    Get a Fernet cipher initialized from the configured encryption key, or None if no valid key is available.
    
    Returns:
        Fernet: A Fernet instance created from the normalized `ENCRYPTION_KEY`.
        `None` if `ENCRYPTION_KEY` is missing, normalization fails, or the key is invalid.
    """
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
    """
    Encrypts a text string using the configured Fernet encryption key.
    
    If `plain` is None or a usable encryption key is not available, the function returns None.
    
    Parameters:
        plain (str): The plaintext to encrypt.
    
    Returns:
        Optional[str]: The encrypted token as a UTF-8 string, or `None` if encryption could not be performed.
    """
    if plain is None:
        return None
    f = _get_fernet()
    if not f:
        return None
    token = f.encrypt(plain.encode("utf-8"))
    return token.decode("utf-8")


def decrypt_text(token: Optional[str]) -> Optional[str]:
    """
    Decrypts a Fernet token string to plaintext.
    
    Parameters:
        token (Optional[str]): UTF-8 string containing a Fernet token to decrypt.
    
    Returns:
        Optional[str]: Decrypted plaintext string, or `None` if `token` is empty, the encryption key is unavailable, or decryption fails.
    """
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
