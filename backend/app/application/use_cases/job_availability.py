import time
from datetime import datetime, timedelta

from app.application.errors import UseCaseError
from app.application.use_cases.integration_observations import record
from app.domain.services.job_freshness import externally_available

REASONS = {"source_api": "La fuente original publica esta oferta.", "structured_date": "Vigencia publicada en la oferta original.",
           "source_removed": "La fuente retiró la oferta.", "expired": "La fecha de cierre ya pasó.", "source_unavailable": "No se pudo consultar la fuente; no implica que la oferta esté cerrada.",
           "unconfirmed": "La fuente no aporta evidencia suficiente de vigencia.", "robots_disallowed": "La fuente no permite la comprobación automática.", "redirected": "El enlace dirige a otra página y no confirma esta oferta."}


def check_job(db, job, gateway, *, now=None):
    if job.source_kind != "external":
        raise UseCaseError(status_code=422, detail="Esta comprobación corresponde a vacantes externas")
    now = now or datetime.utcnow()
    if job.expires_at and job.expires_at <= now:
        state, reason, valid_until = "closed", "expired", None
    else:
        result = gateway.check(job.external_url, now=now)
        state, reason, valid_until = result.state, result.reason, result.valid_until
    job.external_check_state, job.external_checked_at, job.external_check_reason = state, now, reason
    job.external_next_check_at = now + timedelta(hours=24 if state == "verified" else 6)
    if state == "verified":
        job.external_verified_at = now
        if valid_until:
            job.expires_at = min(filter(None, (job.expires_at, valid_until)))
    if state == "closed":
        job.status = "closed"
    record(db, "external_jobs", "provider_error" if state == "unavailable" else "", commit=False, operation="availability_check")
    db.commit()
    return {"id": job.id, "state": state, "reason": REASONS.get(reason, REASONS["unconfirmed"]), "checked_at": now, "available": externally_available(job, now)}


def check_due(db, gateway, *, limit=20, budget_seconds=45):
    started = time.monotonic()
    counts = {"checked": 0, "verified": 0, "closed": 0, "unknown": 0, "unavailable": 0}
    for job in db.jobs.due_external(datetime.utcnow(), min(max(limit, 1), 50)):
        if time.monotonic() - started >= budget_seconds:
            break
        result = check_job(db, job, gateway)
        counts["checked"] += 1
        counts[result["state"]] += 1
    return counts
