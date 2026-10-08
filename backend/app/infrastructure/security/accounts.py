import base64
import hashlib

from cryptography.fernet import Fernet

from app.core.config import settings
from app.infrastructure.security.jwt import create_access_token
from app.infrastructure.security.passwords import hash_password, verify_password


class AccountSecurity:
    hash_password = staticmethod(hash_password)
    verify_password = staticmethod(verify_password)
    create_access_token = staticmethod(create_access_token)

    @staticmethod
    def _cipher():
        key = hashlib.sha256(("talentsync:mfa:" + settings.secret_key).encode()).digest()
        return Fernet(base64.urlsafe_b64encode(key))

    def encrypt_secret(self, value):
        return self._cipher().encrypt(value.encode()).decode()

    def decrypt_secret(self, value):
        return self._cipher().decrypt(value.encode()).decode()
