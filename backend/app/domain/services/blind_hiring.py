import hashlib


def candidate_alias(job_id, user_id):
    code = hashlib.sha256(f"{job_id}:{user_id}".encode()).hexdigest()[:8].upper()
    return f"Talento {code}"


def identity_hidden(job, application=None):
    # Consent is scoped to this vacancy: being recommended or invited is insufficient.
    return application is None or application.job_id != job.id
