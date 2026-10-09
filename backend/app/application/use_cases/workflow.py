from datetime import datetime, timedelta
from uuid import uuid4

from app.application.errors import UseCaseError
from app.application.use_cases.events import record_event
from app.application.use_cases.jobs import ensure_job_access
from app.domain.entities.enums import ApplicationStatus, UserRole
from app.domain.services.blind_hiring import candidate_alias, identity_hidden
from app.domain.services.pipeline import stages_for

FINAL = {ApplicationStatus.REJECTED, ApplicationStatus.HIRED, ApplicationStatus.ACCEPTED}


def transition(db, row, actor_id, *, previous_status=None, previous_stage=None, source="company", now=None):
    now = now or datetime.utcnow()
    if source == "company" and row.first_response_at is None:
        row.first_response_at = now
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
        member = db.organizations.member_for_user(user.id) if user.role == UserRole.COMPANY else None
        if member and member.role == "interviewer" and row.job_id not in member.assigned_job_ids:
            raise UseCaseError(status_code=403, detail="Este proceso no pertenece a tus asignaciones")
    return row


def timeline(db, user, application_id):
    row = accessible_application(db, user, application_id)
    member = db.organizations.member_for_user(user.id) if user.role == UserRole.COMPANY else None
    history = [{"id": item.id, "at": item.created_at, "type": item.event_type, **item.details}
               for item in reversed(db.events.for_entity("application", row.id, 500))
               if item.event_type in {"application.transition", "application.deadline_released", "application.withdrawn", "application.feedback_shared"}]
    return {"job_title": row.job.title, "company_name": row.job.company.name, "job_id": row.job_id, "application_id": row.id, "can_manage": user.role != UserRole.CANDIDATE and (member is None or member.role != "interviewer"), "version": row.version, "status": row.status.value, "stage": row.pipeline_stage,
            "stage_title": next((stage["title"] for stage in stages_for(row.job) if stage["id"] == row.pipeline_stage), "En seguimiento"),
            "interview_at": row.interview_at, "job_description": row.job.description, "job_requirements": row.job.requirements,
            "response_due_at": row.response_due_at, "released_at": row.released_at, "feedback": row.candidate_feedback,
            "events": history, "created_at": row.created_at, "response_days": row.job.response_days,
            "candidate_name": (candidate_alias(row.job_id, row.user_id) if identity_hidden(row.job, row) else row.user.name) if user.role != UserRole.CANDIDATE else None,
            "can_evaluate": user.role == UserRole.COMPANY and not row.released_at and row.status not in FINAL,
            "interview_evaluations": list(reversed(row.interview_evaluations or [])) if user.role != UserRole.CANDIDATE else []}


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


def evaluate_interview(db, user, application_id, payload):
    row = accessible_application(db, user, application_id)
    if user.role != UserRole.COMPANY or row.released_at or row.status in FINAL:
        raise UseCaseError(status_code=409, detail="Este proceso no admite nuevas evaluaciones de entrevista")
    row.interview_evaluations = [*(row.interview_evaluations or []), {"id": uuid4().hex, "at": datetime.utcnow().isoformat(), **payload, "author": user.name, "author_id": user.id}]
    record_event(db, "interview.evaluation_added", "application", row.id, actor_user_id=user.id, details={"job_id": row.job_id})
    company = row.job.company
    if company.owner_user_id != user.id:
        db.add(db.notifications.new(user_id=company.owner_user_id, type="interview_evaluation", title="Nueva evaluación de entrevista",
            body=f"{user.name} añadió una evaluación interna al proceso de {row.job.title}.", action_url=f"/procesos/{row.id}"))
    db.commit()
    return timeline(db, user, application_id)
