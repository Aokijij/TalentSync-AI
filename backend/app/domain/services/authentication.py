"""RFC 6238 TOTP primitives; never use email as an MFA factor."""
import base64
import hashlib
import hmac
import secrets
import struct
import time


def token_digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def generate_totp_secret() -> str:
    return base64.b32encode(secrets.token_bytes(20)).decode().rstrip("=")


def totp(secret: str, counter: int) -> str:
    key = base64.b32decode(secret + "=" * (-len(secret) % 8))
    digest = hmac.new(key, struct.pack(">Q", counter), hashlib.sha1).digest()
    offset = digest[-1] & 15
    number = struct.unpack(">I", digest[offset:offset + 4])[0] & 0x7fffffff
    return f"{number % 1_000_000:06d}"


def verify_totp(secret: str, code: str, last_counter: int | None = None, *, now: float | None = None) -> int | None:
    counter = int((time.time() if now is None else now) // 30)
    if len(code) != 6 or not code.isdigit():
        return None
    for value in (counter, counter - 1, counter + 1):
        if value >= 0 and (last_counter is None or value > last_counter) and hmac.compare_digest(totp(secret, value), code):
            return value
    return None
