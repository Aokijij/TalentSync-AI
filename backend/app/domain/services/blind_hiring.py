import hashlib


def candidate_alias(job_id, user_id):
    code = hashlib.sha256(f"{job_id}:{user_id}".encode()).hexdigest()[:8].upper()
    return f"Talento {code}"


def identity_hidden(job, application=None):
    return bool(getattr(job, "blind_hiring", False) and not (application and getattr(application, "identity_revealed_at", None)))
