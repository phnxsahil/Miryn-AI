from app.core import encryption
from app.config import settings


def test_encrypt_decrypt_roundtrip():
    original_key = settings.ENCRYPTION_KEY
    try:
        settings.ENCRYPTION_KEY = "test_key_123"
        plain = "secret payload"
        token = encryption.encrypt_text(plain)
        assert token is not None
        decoded = encryption.decrypt_text(token)
        assert decoded == plain
    finally:
        settings.ENCRYPTION_KEY = original_key
