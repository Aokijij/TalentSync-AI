from datetime import datetime, timedelta

from app.application.ports.unit_of_work import UnitOfWork


def maintain_job_catalog(
    db: UnitOfWork,
    *,
    now: datetime | None = None,
    max_age_days: int = 60,
    min_skills: int = 3,
) -> dict[str, int]:
    now = now or datetime.utcnow()
    cutoff = now - timedelta(days=max_age_days)
    expired = 0
    for job in db.jobs.active_external():
        if job.created_at < cutoff or len(job.skills or []) < min_skills:
            job.status = "closed"
            expired += 1

    notifications = 0
    reminder_since = now - timedelta(days=7)
    for job in db.jobs.company_attention_jobs(now - timedelta(days=14)):
        owner_id = job.company.owner_user_id
        action_url = f"/empresa/vacantes/{job.id}/candidatos"
        age_days = max(0, (now - job.created_at).days)
        if not job.applications:
            notifications += _notify_once(
                db,
                user_id=owner_id,
                notification_type="job_no_applications",
                title=f"{job.title} aún no recibe postulaciones",
                body=(
                    f"La vacante lleva {age_days} días publicada. Revisa el título, "
                    "los requisitos y el rango salarial para mejorar su alcance."
                ),
                action_url=action_url,
                since=reminder_since,
            )
        if age_days >= 30:
            notifications += _notify_once(
                db,
                user_id=owner_id,
                notification_type="job_stale",
                title=f"Revisa la vigencia de {job.title}",
                body=(
                    f"Esta vacante lleva {age_days} días activa. Confirma si continúa "
                    "abierta, actualízala o ciérrala para mantener el catálogo al día."
                ),
                action_url=action_url,
                since=reminder_since,
            )
    if expired or notifications:
        db.commit()
    return {"closed_external_jobs": expired, "notifications_created": notifications}


def _notify_once(
    db: UnitOfWork,
    *,
    user_id: int,
    notification_type: str,
    title: str,
    body: str,
    action_url: str,
    since: datetime,
) -> int:
    if db.notifications.find_recent(
        user_id, notification_type, action_url, since
    ):
        return 0
    db.add(
        db.notifications.new(
            user_id=user_id,
            type=notification_type,
            title=title,
            body=body,
            action_url=action_url,
        )
    )
    return 1
