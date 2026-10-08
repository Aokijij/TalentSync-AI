import hashlib
from uuid import UUID

PROVIDERS = {"workspace", "entra"}


def canonical_uuid(value):
    try:
        return isinstance(value, str) and str(UUID(value)) == value
    except (ValueError, AttributeError):
        return False


def authority_fingerprint(provider, boundary, client_id):
    return hashlib.sha256(f"{provider}:{boundary}:{client_id}".encode()).hexdigest()


def entra_subject(value):
    parts = value.split(":") if isinstance(value, str) else []
    return len(parts) == 2 and all(canonical_uuid(part) for part in parts)
