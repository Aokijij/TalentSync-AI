from datetime import datetime, timedelta

from app.domain.services.external_job_content import admission_reasons

FRESH_HOURS = 72


def verification_method(job, now=None):
    """Manual source reviews never masquerade as successful API checks."""
    now = now or datetime.utcnow()
    checked = getattr(job, "external_verified_at", None)
    state = getattr(job, "external_check_state", "pending")
    if state == "verified" and checked and now - timedelta(hours=FRESH_HOURS) <= checked <= now:
        return "automatic"
    reviewed = getattr(job, "external_manual_verified_at", None)
    until = getattr(job, "external_manual_verified_until", None)
    last_check = getattr(job, "external_checked_at", None)
    if (reviewed and until and reviewed <= now < until
            and getattr(job, "external_manual_verified_by", None)
            and getattr(job, "external_manual_source_url", None) == job.external_url
            and not (state == "closed" and last_check and last_check >= reviewed)):
        return "manual"
    return "unconfirmed"


def externally_available(job, now=None, *, ignore_moderation=False):
    if not ignore_moderation and getattr(job, "moderation_status", "automatic") == "held":
        return False
    if getattr(job, "source_kind", "internal") != "external":
        return True
    now = now or datetime.utcnow()
    if not ((getattr(job, "external_content", None) or {}).get("admission") or {}).get("clarity_passed"):
        return False
    if admission_reasons(getattr(job, "external_published_at", None), getattr(job, "skills", []), now=now):
        return False
    return bool(verification_method(job, now) != "unconfirmed"
                and (not job.expires_at or job.expires_at > now))
