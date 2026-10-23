"""Small, persistent observations of explicit operations; never probe on a status GET."""
from datetime import datetime

from app.application.errors import UseCaseError

PROVIDERS = {"youtube", "microsoft_learn", "sena", "sapiencia", "jsearch", "adzuna", "jooble"}
ERRORS = {"rate_limit": "Se alcanzó la cuota o el límite de consultas.", "provider_error": "La última operación no pudo completarse. Revisa la fuente desde su sección.", "partial": "La actualización fue parcial; se conservaron los últimos datos disponibles."}


def observed(db, provider, operation):
    if provider not in PROVIDERS:
        raise ValueError("Unknown integration")
    try:
        result = operation()
    except UseCaseError as failure:
        # Invalid user input is not evidence that a provider is down.
        if failure.status_code == 429 or failure.status_code >= 500:
            record(db, provider, "rate_limit" if failure.status_code == 429 else "provider_error")
        raise
    if isinstance(result, dict) and "checked" in result and not result.get("checked") and not result.get("failed"):
        return result  # Nothing was checked; keep the previous observation date.
    partial = isinstance(result, dict) and (result.get("warning") or result.get("failed"))
    record(db, provider, "partial" if partial else "")
    return result


def record(db, provider, error_code=""):
    now = datetime.utcnow()
    key = "integration:" + provider
    row = db.learning.source_snapshot(key)
    previous = row.content if row else {}
    content = {"last_success_at": previous.get("last_success_at") if error_code else now.isoformat() + "Z", "error_code": error_code}
    if row is None:
        row = db.learning.new_source_snapshot(id=key, content=content, fetched_at=now, attempted_at=now)
        db.add(row)
    else:
        row.content, row.attempted_at = content, now
        if not error_code:
            row.fetched_at = now
    row.error = ERRORS.get(error_code, "")
    db.commit()


def observations(db):
    result = {}
    for provider in sorted(PROVIDERS):
        row = db.learning.source_snapshot("integration:" + provider)
        if row:
            result[provider] = {"last_success_at": row.content.get("last_success_at"), "last_attempt_at": row.attempted_at.isoformat() + "Z", "last_error": ERRORS.get(row.content.get("error_code"), "")}
    # Older public-source caches also contain useful evidence, not credentials.
    sapiencia = db.learning.source_snapshot("sapiencia")
    if sapiencia and "sapiencia" not in result:
        result["sapiencia"] = {"last_success_at": None if sapiencia.error else sapiencia.fetched_at.isoformat() + "Z", "last_attempt_at": sapiencia.attempted_at.isoformat() + "Z", "last_error": ERRORS["provider_error"] if sapiencia.error else ""}
    return result
