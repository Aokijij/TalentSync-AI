from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.application.errors import UseCaseError
from app.application.use_cases.events import record_event
from app.application.use_cases.jobs import ensure_job_access
from app.domain.entities.enums import ApplicationStatus, UserRole
from app.domain.services.blind_hiring import candidate_alias, identity_hidden
from app.domain.services.interview_calendar import interview_calendar, utc
from app.domain.services.pipeline import stage_id_for, stages_for
from app.domain.services.response_deadlines import (
    EXTENSION_LIMIT,
    EXTENSION_WORKDAYS,
    PAUSE_WORKDAYS,
    add_workdays,
    deadline_view,
    interview_deadline,
    reset_response,
)

FINAL = {ApplicationStatus.REJECTED, ApplicationStatus.HIRED, ApplicationStatus.ACCEPTED}


def transition(db, row, actor_id, *, previous_status=None, previous_stage=None, source="company", now=None):
    now = now or datetime.utcnow()
    if source == "company" and row.first_response_at is None:
        row.first_response_at = now
    reset_response(row, None if row.status in FINAL or row.released_at else add_workdays(now, row.job.response_days))
    record_event(db, "application.transition", "application", row.id, actor_user_id=actor_id, details={
        "status": row.status.value, "previous_status": previous_status.value if previous_status else None,
        "stage": stage_id_for(row), "previous_stage": previous_stage, "job_id": row.job_id,
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
               if item.event_type in {"application.transition", "application.deadline_released", "application.withdrawn", "application.feedback_shared", "application.interview_updated", "application.interview_completed", "application.response_overdue", "application.response_paused", "application.deadline_extended", "application.deadline_protected"}]
    return {**deadline_view(row), "response_owner": f"Equipo de selección de {row.job.company.name}", "job_title": row.job.title, "company_name": row.job.company.name, "job_id": row.job_id, "application_id": row.id, "can_manage": user.role != UserRole.CANDIDATE and (member is None or member.role != "interviewer"), "version": row.version, "status": row.status.value, "stage": stage_id_for(row),
            "stage_title": row.pipeline_stage_title,
            "interview_at": row.interview_at, "interview_details": row.interview_details or {}, "interview_completed_at": row.interview_completed_at, "job_description": row.job.description, "job_requirements": row.job.requirements,
            "job_conditions": {"salary": row.job.salary, "quality_details": row.job.quality_details,
                               "quality_revision": row.job.quality_revision, "response_days": row.job.response_days,
                               "pipeline_stages": stages_for(row.job)},
            "process_estimated_end": row.created_at + timedelta(days=row.job.quality_details["process_days"]) if row.job.quality_details and row.job.quality_details.get("process_days") else None,
            "response_due_at": row.response_due_at, "released_at": row.released_at, "feedback": row.candidate_feedback,
            "events": history, "created_at": row.created_at, "response_days": row.job.response_days,
            "candidate_name": (candidate_alias(row.job_id, row.user_id) if identity_hidden(row.job, row) else row.user.name) if user.role != UserRole.CANDIDATE else None,
            "can_evaluate": user.role == UserRole.COMPANY and not row.released_at and row.status not in FINAL,
            "interview_evaluations": list(reversed(row.interview_evaluations or [])) if user.role != UserRole.CANDIDATE else []}


def export_interview_calendar(db, user, application_id, *, public_app_url):
    row = accessible_application(db, user, application_id)
    now = datetime.now(timezone.utc)
    if row.released_at or row.status in FINAL:
        raise UseCaseError(status_code=409, detail="El proceso finalizó; no hay una cita activa para añadir al calendario")
    if not row.interview_at:
        raise UseCaseError(status_code=409, detail="La empresa aún no ha programado una entrevista")
    if utc(row.interview_at) <= now:
        raise UseCaseError(status_code=409, detail="La fecha de esta entrevista ya pasó; consulta el proceso para confirmar una nueva cita")
    return interview_calendar(application_id=row.id, created_at=row.created_at, interview_at=row.interview_at,
                              job_title=row.job.title, company_name=row.job.company.name,
                              process_url=f"{public_app_url.rstrip('/')}/procesos/{row.id}",
                              version=row.version, now=now)


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
    result = {"released": 0, "reminders": 0, "overdue": 0, "paused": 0, "protected": 0}
    for row in db.applications.approaching_deadlines(now + timedelta(days=1), now=now):
        floor = interview_deadline(row)
        if floor and floor > row.response_due_at:
            if db.applications.claim_response_change(row, {"response_due_at": floor, "response_overdue_at": None, "reminder_sent_at": None}):
                record_event(db, "application.deadline_protected", "application", row.id,
                    details={"source": "system", "job_id": row.job_id, "deadline": floor.isoformat(), "reason_code": "interview_schedule"})
                result["protected"] += 1
            continue
        if row.response_due_at <= now:
            if row.response_overdue_at is None:
                changes = {"response_overdue_at": now}
                if row.deadline_missed_at is None:
                    changes["deadline_missed_at"] = now
                kind, title = "overdue", "Respuesta atrasada de la empresa"
                message = "La empresa superó su fecha de respuesta. Tu candidatura sigue abierta y el equipo de selección debe comunicar el siguiente paso."
            elif add_workdays(row.response_overdue_at, PAUSE_WORKDAYS) <= now:
                changes = {"response_paused_at": now}
                kind, title = "paused", "Proceso en pausa por falta de respuesta de la empresa"
                message = "La empresa sigue sin comunicar un avance. Tu candidatura y su etapa se conservan; puedes consultar el historial o retirar tu postulación."
            else:
                continue
            if not db.applications.claim_response_change(row, changes):
                continue
            record_event(db, f"application.response_{kind}", "application", row.id,
                details={"source": "system", "job_id": row.job_id, "deadline": row.response_due_at.isoformat()})
            for recipient in {row.user_id, row.job.company.owner_user_id}:
                db.add(db.notifications.new(user_id=recipient, type=f"application_response_{kind}", title=title,
                    body=f"{row.job.title}. {message}", action_url=f"/procesos/{row.id}"))
            result[kind] += 1
        elif row.reminder_sent_at is None and db.applications.claim_response_change(row, {"reminder_sent_at": now}):
            local = row.response_due_at.replace(tzinfo=timezone.utc).astimezone(timezone(timedelta(hours=-5)))
            db.add(db.notifications.new(user_id=row.job.company.owner_user_id, type="application_deadline_reminder",
                title="Tu compromiso de respuesta está por vencer", body=f"Comunica el siguiente paso de {row.job.title} antes del {local.strftime('%d/%m/%Y a las %H:%M')} (Colombia). Puedes ampliar el plazo una vez con un motivo y una nueva fecha.",
                action_url=f"/procesos/{row.id}"))
            result["reminders"] += 1
    if any(result.values()):
        db.commit()
    return result


def extend_deadline(db, user, application_id, *, expected_version, due_at, reason, now=None):
    now = now or datetime.utcnow()
    row = accessible_application(db, user, application_id)
    member = db.organizations.member_for_user(user.id)
    if user.role != UserRole.COMPANY or member and member.role == "interviewer":
        raise UseCaseError(status_code=403, detail="Solo el equipo que gestiona la selección puede ampliar el plazo")
    if row.released_at or row.status in FINAL:
        raise UseCaseError(status_code=409, detail="Este proceso finalizó y es de solo lectura")
    if row.version != expected_version:
        raise UseCaseError(status_code=409, detail="El proceso cambió; actualiza antes de ampliar el plazo")
    if row.deadline_extension_count >= EXTENSION_LIMIT:
        raise UseCaseError(status_code=409, detail="Ya utilizaste la ampliación de esta etapa. Comunica un avance o una decisión al candidato")
    if due_at <= now or row.response_due_at and due_at <= row.response_due_at or due_at > add_workdays(max(now, row.response_due_at or now), EXTENSION_WORKDAYS):
        raise UseCaseError(status_code=422, detail="Elige una fecha posterior al plazo actual y hasta 7 días laborables adicionales")
    floor = interview_deadline(row)
    if floor and due_at < floor:
        raise UseCaseError(status_code=422, detail="El nuevo plazo debe respetar la entrevista y su tiempo de respuesta posterior")
    local = due_at.replace(tzinfo=timezone.utc).astimezone(timezone(timedelta(hours=-5)))
    if local.weekday() >= 5:
        raise UseCaseError(status_code=422, detail="Elige un día de lunes a viernes para el compromiso de respuesta")
    previous, was_paused = row.response_due_at, row.response_paused_at is not None
    row.response_due_at, row.response_overdue_at, row.response_paused_at, row.reminder_sent_at = due_at, None, None, None
    row.deadline_extension_count += 1
    record_event(db, "application.deadline_extended", "application", row.id, actor_user_id=user.id,
        details={"source": "company", "job_id": row.job_id, "deadline": due_at.isoformat(), "previous_deadline": previous.isoformat() if previous else None,
                 "extension_reason": reason, "resumed": was_paused})
    db.add(db.notifications.new(user_id=row.user_id, type="application_deadline_extended", title="Nuevo compromiso de respuesta de la empresa",
        body=f"{row.job.company.name} responderá sobre {row.job.title} antes del {local.strftime('%d/%m/%Y a las %H:%M')} (Colombia). Motivo: {reason}", action_url=f"/procesos/{row.id}"))
    db.commit()
    return timeline(db, user, row.id)


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
