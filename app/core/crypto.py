import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings


def _fernet_key() -> bytes:
    configured_key = settings.PROVIDER_CONFIG_ENCRYPTION_KEY.strip()
    if configured_key:
        return configured_key.encode()

    digest = hashlib.sha256(settings.JWT_SECRET.encode()).digest()
    return base64.urlsafe_b64encode(digest)


_fernet = Fernet(_fernet_key())


def encrypt_secret(value: str | None) -> str | None:
    if not value:
        return None

    return _fernet.encrypt(value.encode()).decode()


def decrypt_secret(value: str | None) -> str:
    if not value:
        return ""

    try:
        return _fernet.decrypt(value.encode()).decode()
    except InvalidToken:
        return ""
