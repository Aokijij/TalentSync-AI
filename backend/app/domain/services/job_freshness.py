from datetime import datetime, timedelta

from app.domain.services.external_job_content import admission_reasons

FRESH_HOURS = 72


def externally_available(job, now=None):
    if getattr(job, "source_kind", "internal") != "external":
        return True
    now = now or datetime.utcnow()
    if not ((getattr(job, "external_content", None) or {}).get("admission") or {}).get("clarity_passed"):
        return False
    if admission_reasons(getattr(job, "external_published_at", None), getattr(job, "skills", []), now=now):
        return False
    checked = getattr(job, "external_verified_at", None)
    return bool(getattr(job, "external_check_state", "pending") == "verified" and checked and checked >= now - timedelta(hours=FRESH_HOURS)
                and (not job.expires_at or job.expires_at > now))
