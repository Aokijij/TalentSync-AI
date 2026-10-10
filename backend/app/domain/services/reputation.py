from datetime import datetime, timedelta


def company_health(company, *, now=None):
    now = now or datetime.utcnow()
    cutoff = now - timedelta(days=90)
    rows = [application for job in company.jobs for application in job.applications if application.created_at >= cutoff]
    eligible = [row for row in rows if getattr(row, "first_response_at", None) or row.resolution_reason == "response_deadline"]
    missed = sum(row.resolution_reason == "response_deadline" for row in eligible)
    confirmed = sum(row.status in {"confirmed", "appealed"} and row.created_at >= cutoff for row in getattr(company, "incidents", []))
    return health_from_counts(len(eligible), missed, confirmed)


def health_from_counts(eligible, missed, confirmed):
    score = round(max(0, 100 * (eligible - missed + 5) / (eligible + 5) - min(40, confirmed * 10)), 1) if eligible or confirmed else None
    reduced = (eligible >= 5 and score is not None and score < 60) or confirmed >= 2
    return {"score": score, "window_days": 90, "measured_processes": eligible, "missed_deadlines": missed,
            "confirmed_incidents": confirmed, "visibility_reduced": reduced, "sufficient_response_sample": eligible >= 5,
            "method": "response-trust-v1", "notice": "Índice de comportamiento en esta plataforma. Denuncias pendientes no afectan el resultado. Cinco observaciones previas suavizan muestras pequeñas."}
