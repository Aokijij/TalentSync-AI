from datetime import datetime, timedelta

from app.application.errors import UseCaseError
from app.application.use_cases.events import record_event
from app.application.use_cases.jobs import ensure_job_access
from app.domain.entities.enums import ApplicationStatus, UserRole

FINAL = {ApplicationStatus.REJECTED, ApplicationStatus.HIRED, ApplicationStatus.ACCEPTED}


def transition(db, row, actor_id, *, previous_status=None, previous_stage=None, source="company", now=None):
    now = now or datetime.utcnow()
    row.response_due_at = None if row.status in FINAL or row.released_at else now + timedelta(days=row.job.response_days)
    row.reminder_sent_at = None
    record_event(db, "application.transition", "application", row.id, actor_user_id=actor_id, details={
        "status": row.status.value, "previous_status": previous_status.value if previous_status else None,
        "stage": row.pipeline_stage, "previous_stage": previous_stage, "job_id": row.job_id,
        "source": source, "deadline": row.response_due_at.isoformat() if row.response_due_at else None})


def accessible_application(db, user, application_id):
    row = db.applications.get(application_id)
    if row is None:
        raise UseCaseError(status_code=404, detail="Postulación no encontrada")
    if user.role == UserRole.CANDIDATE:
        if row.user_id != user.id:
            raise UseCaseError(status_code=403, detail="No puedes consultar este proceso")
    else:
        ensure_job_access(db, row.job, user)
    return row


def timeline(db, user, application_id):
    row = accessible_application(db, user, application_id)
    history = [{"id": item.id, "at": item.created_at, "type": item.event_type, **item.details}
               for item in reversed(db.events.for_entity("application", row.id, 500))
               if item.event_type in {"application.transition", "application.deadline_released", "application.withdrawn", "application.feedback_shared"}]
    return {"application_id": row.id, "version": row.version, "status": row.status.value, "stage": row.pipeline_stage,
            "response_due_at": row.response_due_at, "released_at": row.released_at, "feedback": row.candidate_feedback,
            "events": history, "created_at": row.created_at, "response_days": row.job.response_days}


def withdraw(db, user, application_id):
    row = accessible_application(db, user, application_id)
    if row.status in FINAL or row.released_at:
        raise UseCaseError(status_code=409, detail="Este proceso ya finalizó")
    row.released_at = datetime.utcnow()
    row.response_due_at = None
    row.status = ApplicationStatus.REJECTED
    row.resolution_reason = "candidate_withdrawn"
    record_event(db, "application.withdrawn", "application", row.id, actor_user_id=user.id, details={"source": "candidate", "job_id": row.job_id})
    db.commit()
    return {"message": "Postulación retirada; el historial se conserva"}


def deadline_cycle(db, *, now=None):
    now = now or datetime.utcnow()
    released = 0
    reminders = 0
    for row in db.applications.approaching_deadlines(now + timedelta(days=1)):
        if row.response_due_at <= now:
            if not db.applications.claim_deadline(row, now):
                continue
            row.candidate_feedback = {"source": "system", "reason_code": "response_deadline",
                "message": "La empresa no comunicó un avance dentro del plazo. El proceso se cerró por vencimiento; esto no evalúa tu capacidad.",
                "created_at": now.isoformat()}
            record_event(db, "application.deadline_released", "application", row.id, details={"job_id": row.job_id, "company_id": row.job.company_id, "reason_code": "response_deadline"})
            for recipient in [row.user_id, row.job.company.owner_user_id]:
                db.add(db.notifications.new(user_id=recipient, type="application_deadline", title="Proceso cerrado por falta de respuesta",
                    body=f"Venció el plazo de {row.job.title}. El cierre quedó registrado en el historial.", action_url=f"/procesos/{row.id}"))
            released += 1
        elif row.reminder_sent_at is None:
            row.reminder_sent_at = now
            db.add(db.notifications.new(user_id=row.job.company.owner_user_id, type="application_deadline_reminder",
                title="Un plazo de respuesta está por vencer", body=f"Actualiza el proceso de {row.job.title} antes de {row.response_due_at.isoformat()} UTC.",
                action_url=f"/procesos/{row.id}"))
            reminders += 1
    if released or reminders:
        db.commit()
    return {"released": released, "reminders": reminders}
