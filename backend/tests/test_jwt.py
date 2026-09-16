from datetime import datetime, timedelta, timezone

import jwt

from app.core.config import settings
from app.infrastructure.security.jwt import create_access_token, decode_access_token


def test_jwt_round_trip_and_invalid_tokens():
    claims = decode_access_token(create_access_token("42", "candidate"))
    assert claims["sub"] == "42"
    assert claims["role"] == "candidate"
    assert decode_access_token("not-a-valid-token") is None
    expired = jwt.encode({"sub": "42", "exp": datetime.now(timezone.utc) - timedelta(seconds=1)}, settings.secret_key, algorithm="HS256")
    assert decode_access_token(expired) is None
    forged = jwt.encode({"sub": "42"}, "different-secret-key-at-least-32-characters", algorithm="HS256")
    assert decode_access_token(forged) is None
    wrong_algorithm = jwt.encode({"sub": "42"}, settings.secret_key * 2, algorithm="HS512")
    assert decode_access_token(wrong_algorithm) is None
