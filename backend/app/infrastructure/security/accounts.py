from app.infrastructure.security.jwt import create_access_token
from app.infrastructure.security.passwords import hash_password, verify_password


class AccountSecurity:
    hash_password = staticmethod(hash_password)
    verify_password = staticmethod(verify_password)
    create_access_token = staticmethod(create_access_token)
