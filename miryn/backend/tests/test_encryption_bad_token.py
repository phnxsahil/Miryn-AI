from cryptography.fernet import Fernet

from app.config import settings
from app.core.encryption import decrypt_text, encrypt_text


def test_decrypt_returns_none_for_invalid_token(monkeypatch):
    monkeypatch.setattr(settings, "ENCRYPTION_KEY", Fernet.generate_key().decode())
    assert decrypt_text("not-valid-ciphertext") is None


def test_decrypt_returns_none_for_token_from_another_key(monkeypatch):
    monkeypatch.setattr(settings, "ENCRYPTION_KEY", Fernet.generate_key().decode())
    token = encrypt_text("private line")
    monkeypatch.setattr(settings, "ENCRYPTION_KEY", Fernet.generate_key().decode())
    assert decrypt_text(token) is None
