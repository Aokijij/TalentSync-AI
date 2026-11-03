"""Small, persistent observations of explicit operations; never probe on a status GET."""
from datetime import datetime

from app.application.errors import UseCaseError

PROVIDERS = {"youtube", "microsoft_learn", "sena", "sapiencia", "jsearch", "adzuna", "jooble", "greenhouse", "lever", "ashby", "getonboard", "external_jobs", "mail", "calendar", "social_google", "social_github", "social_linkedin", "sso_workspace", "sso_entra", "github_projects", "codewars"}
ERRORS = {"rate_limit": "Se alcanzó la cuota o el límite de consultas.", "provider_error": "La última operación no pudo completarse. Revisa la fuente desde su sección.", "partial": "La actualización fue parcial; se conservaron los últimos datos disponibles."}


def health_observations(db):
    snapshot = db.learning.source_snapshot("integration-health")
    return {row["provider"]: row for row in snapshot.content} if snapshot else {}


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


def record(db, provider, error_code="", *, commit=True, operation="query"):
    if provider not in PROVIDERS:
        raise ValueError("Unknown integration")
    now = datetime.utcnow()
    operation = operation if operation in {"query", "token_refresh", "mail_accepted", "calendar_sync", "calendar_connect", "identity_exchange", "availability_check"} else "query"
    db.learning.record_integration(provider, now, error_code, ERRORS.get(error_code, ""), operation)
    if commit:
        db.commit()


def observations(db):
    # Recover actual operations performed before observation hooks were added.
    # Only aggregated timestamps are returned, never identities or message bodies.
    historical = getattr(db.accounts, "integration_history", None)
    result = historical() if historical else {}
    for provider in sorted(PROVIDERS):
        row = db.learning.source_snapshot("integration:" + provider)
        if row:
            result[provider] = {"last_success_at": row.content.get("last_success_at"), "last_attempt_at": row.attempted_at.isoformat() + "Z", "last_error": ERRORS.get(row.content.get("error_code"), ""), "operation": row.content.get("operation", "query")}
    # Older public-source caches also contain useful evidence, not credentials.
    sapiencia = db.learning.source_snapshot("sapiencia")
    if sapiencia and "sapiencia" not in result:
        result["sapiencia"] = {"last_success_at": None if sapiencia.error else sapiencia.fetched_at.isoformat() + "Z", "last_attempt_at": sapiencia.attempted_at.isoformat() + "Z", "last_error": ERRORS["provider_error"] if sapiencia.error else ""}
    return result
