from datetime import datetime, timedelta, timezone
from typing import Any

from app.application.errors import UseCaseError
from app.application.ports.unit_of_work import UnitOfWork
from app.application.use_cases.events import record_event
from app.application.use_cases.workflow import transition
from app.domain.entities.enums import ApplicationStatus, UserRole
from app.domain.entities.records import Application, User
from app.domain.services.blind_hiring import identity_hidden
from app.domain.services.interview_calendar import utc
from app.domain.services.pipeline import stages_for


def _screening_result(job, submitted: list[dict]) -> tuple[list[dict], float]:
    questions = job.application_questions or []
    submitted_by_id = {
        item["question_id"]: str(item["answer"]).strip() for item in submitted
    }
    known_ids = {question["id"] for question in questions}
    if set(submitted_by_id) - known_ids:
        raise UseCaseError(status_code=422, detail="Hay respuestas para preguntas que no pertenecen a la vacante")
    saved: list[dict] = []
    automatic_adjustment = 0.0
    for question in questions:
        answer = submitted_by_id.get(question["id"], "")
        if question.get("required", True) and not answer:
            raise UseCaseError(status_code=422, detail=f"Responde la pregunta: {question['prompt']}")
        if not answer:
            continue
        configured_adjustment = 0.0
        if question.get("type") == "choice":
            matches = [option for option in question.get("options", []) if option.strip() == answer]
            if len(matches) != 1:
                raise UseCaseError(status_code=422, detail=f"Selecciona una opción válida para: {question['prompt']}")
            configured_adjustment = float((question.get("option_scores") or {}).get(matches[0], 0) or 0)
            automatic_adjustment += configured_adjustment
        saved.append(
            {
                "question_id": question["id"],
                "question": question["prompt"],
                "type": question.get("type", "open"),
                "answer": answer,
                "reviewer_adjustment": 0,
                "configured_adjustment": configured_adjustment,
            }
        )
    return saved, max(-20.0, min(20.0, automatic_adjustment))

STATUS_LABELS = {
    "submitted": "Postulación recibida",
    "seen": "Postulación recibida",
    "reviewing": "En revisión",
    "shortlisted": "En revisión",
    "technical_interview": "Entrevista",
    "psychometric_test": "Entrevista",
    "accepted": "Seleccionado",
    "hired": "Seleccionado",
    "rejected": "No seleccionado",
}
LEGACY_STAGE_STATUS = {
    "submitted": ApplicationStatus.SUBMITTED,
    "reviewing": ApplicationStatus.REVIEWING,
    "shortlisted": ApplicationStatus.SHORTLISTED,
    "interview": ApplicationStatus.TECHNICAL_INTERVIEW,
    "technical_interview": ApplicationStatus.TECHNICAL_INTERVIEW,
    "psychometric_test": ApplicationStatus.PSYCHOMETRIC_TEST,
    "hired": ApplicationStatus.HIRED,
    "rejected": ApplicationStatus.REJECTED,
}


def apply_to_job(
    payload: dict[str, Any], current_user: User, db: UnitOfWork, *, exporter
) -> Application:
    job = db.jobs.get(payload["job_id"])
    if job is None:
        raise UseCaseError(status_code=404, detail="La vacante no esta disponible")
    db.profiles.lock_owner(current_user.id)
    existing = db.applications.find_for_user_job(current_user.id, payload["job_id"])
    if existing:
        return existing
    if job.status != "active":
        raise UseCaseError(status_code=404, detail="La vacante no esta disponible")
    if job.expires_at and job.expires_at < datetime.utcnow():
        raise UseCaseError(status_code=404, detail="La vacante ya venció")
    if job.external_url:
        raise UseCaseError(
            status_code=422,
            detail="Esta vacante recibe postulaciones en el sitio de la fuente original",
        )
    from copy import deepcopy

    from app.application.use_cases.application_preparation import (
        owned_version,
        profile_resume,
    )
    from app.domain.services.application_preparation import job_snapshot, resume_profile
    answers, screening_adjustment = _screening_result(job, payload.get("screening_answers", []))
    attach_resume = payload.get("attach_resume", True)
    saved = {"attach_resume": attach_resume}
    version_id = payload.get("resume_version_id")
    if version_id:
        if not attach_resume:
            raise UseCaseError(status_code=422, detail="Elige un CV o continúa sin adjunto")
        version = owned_version(db, current_user, version_id)
        if version.job_id != job.id:
            raise UseCaseError(status_code=422, detail="El CV guardado pertenece a otra vacante")
        saved = {**deepcopy(version.snapshot), "resume_version_id": version.id, "pdf_sha256": version.pdf_sha256, "attach_resume": True}
    elif current_user.profile:
        db.refresh(current_user.profile)
        saved = {"schema": 2, "name": current_user.name, "email": current_user.email,
                 "profile": resume_profile(current_user.profile), "job": job_snapshot(job), "attach_resume": attach_resume}
        if attach_resume:
            pdf = profile_resume(db, current_user, job, saved["profile"], exporter)
            saved.update(profile_resume_id=pdf.id, pdf_sha256=pdf.pdf_sha256)
    elif attach_resume:
        raise UseCaseError(status_code=422, detail="Completa tu perfil antes de adjuntar tu hoja de vida")
    first_stage = (job.pipeline_stages or [{"id": "submitted"}])[0]["id"]
    application = db.applications.new(
        user_id=current_user.id,
        job_id=payload["job_id"],
        pipeline_stage=first_stage,
        screening_answers=answers,
        screening_adjustment=screening_adjustment,
        coach_snapshot=saved,
    )
    db.add(application)
    db.flush()
    transition(db, application, current_user.id, source="candidate")
    invitation = db.notifications.find_unread(
        current_user.id, "candidate_invitation", f"/vacantes/{job.id}"
    )
    if invitation:
        invitation.is_read = True
    db.add(
        db.notifications.new(
            user_id=job.company.owner_user_id,
            type="application_received",
            title="Nueva postulación",
            body=f"{current_user.name} se postuló a {job.title}.",
            action_url=f"/empresa/postulaciones?job={job.id}",
        )
    )
    db.commit()
    db.refresh(application)
    return application


def my_applications(current_user: User, db: UnitOfWork) -> list[Application]:
    return db.applications.for_user(current_user.id)


def job_applications(
    job_id: int, current_user: User, db: UnitOfWork
) -> list[Application]:
    job = db.jobs.get(job_id)
    if job is None:
        raise UseCaseError(status_code=404, detail="Vacante no encontrada")
    if current_user.role != UserRole.ADMIN:
        company = db.companies.find_by_owner(current_user.id)
        if company is None or company.id != job.company_id:
            raise UseCaseError(
                status_code=403, detail="No puedes consultar estas postulaciones"
            )
    return db.applications.for_job(job_id)


def mark_job_applications_seen(
    job_id: int, current_user: User, db: UnitOfWork
) -> dict[str, int]:
    job = db.jobs.get(job_id)
    if job is None:
        raise UseCaseError(status_code=404, detail="Vacante no encontrada")
    if current_user.role == UserRole.COMPANY:
        company = db.companies.find_by_owner(current_user.id)
        if company is None or company.id != job.company_id:
            raise UseCaseError(
                status_code=403, detail="No puedes gestionar estas postulaciones"
            )
    updated = db.applications.mark_submitted_seen(job_id)
    db.commit()
    return {"updated": updated}


def update_status(
    application_id: int, payload: dict[str, Any], current_user: User, db: UnitOfWork
) -> Application:
    application = db.applications.get(application_id)
    if application is None:
        raise UseCaseError(status_code=404, detail="Postulacion no encontrada")
    if current_user.role == UserRole.COMPANY:
        company = db.companies.find_by_owner(current_user.id)
        if company is None or application.job.company_id != company.id:
            raise UseCaseError(
                status_code=403, detail="No puedes gestionar esta postulacion"
            )
    changes = dict(payload)
    if application.released_at:
        raise UseCaseError(status_code=409, detail="El proceso fue cerrado o retirado; no puedes reactivarlo sin una nueva postulación")
    expected = changes.pop("expected_version", None)
    if expected is not None and application.version != expected:
        raise UseCaseError(status_code=409, detail="El proceso cambió; actualiza antes de guardar")
    if application.status in {ApplicationStatus.REJECTED, ApplicationStatus.ACCEPTED, ApplicationStatus.HIRED}:
        raise UseCaseError(status_code=409, detail="Este proceso finalizó y es de solo lectura")
    interview_action = changes.pop("interview_action", None)
    if interview_action == "complete":
        if not application.interview_at or application.interview_at > datetime.utcnow():
            raise UseCaseError(status_code=422, detail="Solo puedes registrar una entrevista cuya hora de inicio ya pasó")
        if any(key in changes for key in ("interview_at", "interview_details", "status", "pipeline_stage")):
            raise UseCaseError(status_code=422, detail="Registra la entrevista realizada antes de cambiar su programación o etapa")
        if application.interview_completed_at is None:
            application.interview_completed_at = datetime.utcnow()
            application.response_due_at = datetime.utcnow() + timedelta(days=application.job.response_days)
            application.reminder_sent_at = None
            record_event(db, "application.interview_completed", "application", application.id, actor_user_id=current_user.id,
                         details={"source": "company", "job_id": application.job_id})
            db.add(db.notifications.new(user_id=application.user_id, type="application_interview",
                title="Entrevista realizada · Pendiente de respuesta", body=f"La empresa registró tu entrevista para {application.job.title}. Consulta el plazo de respuesta en tu proceso.", action_url=f"/procesos/{application.id}"))
        if application.status not in {ApplicationStatus.TECHNICAL_INTERVIEW, ApplicationStatus.PSYCHOMETRIC_TEST}:
            changes["status"] = ApplicationStatus.TECHNICAL_INTERVIEW
            if "interview" in {stage["id"] for stage in stages_for(application.job)}:
                changes["pipeline_stage"] = "interview"
    feedback = changes.pop("candidate_feedback", None)
    if feedback:
        application.candidate_feedback = {**feedback, "source": "company", "created_at": datetime.utcnow().isoformat()}
        record_event(db, "application.feedback_shared", "application", application.id, actor_user_id=current_user.id, details={"reason_code": feedback["reason_code"]})
        db.add(db.notifications.new(user_id=application.user_id, type="application_feedback", title="Recibiste feedback de la empresa", body=f"Consulta el mensaje sobre {application.job.title}.", action_url=f"/procesos/{application.id}"))
    previous_status = application.status
    previous_stage = application.pipeline_stage
    previous_interview = application.interview_at
    previous_details = dict(application.interview_details or {})
    if "interview_details" in changes:
        changes["interview_details"] = changes["interview_details"] or {}
    requested_interview = changes.get("interview_at", previous_interview)
    if requested_interview and requested_interview != previous_interview:
        if requested_interview <= datetime.utcnow():
            raise UseCaseError(status_code=422, detail="Elige una fecha y hora futuras para la entrevista")
        if application.status in {ApplicationStatus.REJECTED, ApplicationStatus.ACCEPTED, ApplicationStatus.HIRED}:
            raise UseCaseError(status_code=409, detail="Este proceso ya finalizó; no puedes programar una entrevista")
    if "interview_at" in changes and changes["interview_at"] is None:
        changes["interview_details"] = {}
    elif changes.get("interview_details") and not requested_interview:
        raise UseCaseError(status_code=422, detail="Indica la fecha y hora de la entrevista")
    answer_adjustments = changes.pop("screening_answer_adjustments", None)
    if answer_adjustments is not None:
        if identity_hidden(application.job, application):
            raise UseCaseError(status_code=403, detail="La valoración de texto libre se habilita después de la fase ciega")
        saved_answers = [dict(item) for item in application.screening_answers or []]
        saved_ids = {item.get("question_id") for item in saved_answers}
        unknown = set(answer_adjustments) - saved_ids
        if unknown:
            raise UseCaseError(
                status_code=422,
                detail="La valoración contiene respuestas que no pertenecen a la postulación",
            )
        new_manual = 0.0
        automatic = sum(float(item.get("configured_adjustment", 0) or 0) for item in saved_answers)
        for answer in saved_answers:
            question_id = answer.get("question_id")
            value = float(answer_adjustments.get(question_id, answer.get("reviewer_adjustment", 0)) or 0)
            if value < -3 or value > 3:
                raise UseCaseError(
                    status_code=422,
                    detail="La valoración de cada respuesta debe estar entre -3 y +3",
                )
            if answer.get("type") == "choice":
                if question_id in answer_adjustments and value:
                    raise UseCaseError(status_code=422, detail="Las respuestas de selección usan la valoración configurada en la vacante")
                answer["reviewer_adjustment"] = 0
            else:
                answer["reviewer_adjustment"] = value
                new_manual += value
        application.screening_answers = saved_answers
        application.screening_adjustment = max(-20.0, min(20.0, automatic + new_manual))

    requested_stage = changes.pop("pipeline_stage", None)
    # Status-only actions must keep the displayed stage consistent. Custom
    # active stages remain valid when their existing status is unchanged.
    if requested_stage is None and changes.get("status") and changes["status"] != previous_status:
        target = {ApplicationStatus.SUBMITTED: "submitted", ApplicationStatus.SEEN: "submitted",
                  ApplicationStatus.REVIEWING: "reviewing", ApplicationStatus.SHORTLISTED: "reviewing",
                  ApplicationStatus.TECHNICAL_INTERVIEW: "interview", ApplicationStatus.PSYCHOMETRIC_TEST: "interview",
                  ApplicationStatus.HIRED: "hired", ApplicationStatus.ACCEPTED: "hired", ApplicationStatus.REJECTED: "rejected"}.get(changes["status"])
        if target in {item["id"] for item in stages_for(application.job)}:
            requested_stage = target
    if requested_stage is None and requested_interview and requested_interview != previous_interview:
        configured_ids = {item["id"] for item in stages_for(application.job)}
        if "interview" in configured_ids:
            requested_stage = "interview"
        changes.setdefault("status", ApplicationStatus.TECHNICAL_INTERVIEW)
    if requested_stage is not None:
        configured = {
            stage["id"]: stage for stage in stages_for(application.job)
        }
        if requested_stage not in configured:
            raise UseCaseError(
                status_code=422,
                detail="La etapa no pertenece al proceso de esta vacante",
            )
        application.pipeline_stage = requested_stage
        application.status = ApplicationStatus.SUBMITTED if requested_stage == stages_for(application.job)[0]["id"] else LEGACY_STAGE_STATUS.get(
            requested_stage, ApplicationStatus.REVIEWING
        )
    for key, value in changes.items():
        setattr(application, key, value)
    status_changed = application.status != previous_status
    stage_changed = application.pipeline_stage != previous_stage
    interview_changed = application.interview_at != previous_interview or (application.interview_details or {}) != previous_details
    if application.interview_at != previous_interview:
        application.interview_completed_at = None
    final_statuses = {ApplicationStatus.REJECTED, ApplicationStatus.ACCEPTED, ApplicationStatus.HIRED}
    if interview_changed and application.interview_at and application.status in final_statuses:
        raise UseCaseError(status_code=409, detail="Un proceso finalizado no admite entrevistas nuevas o modificadas")
    if interview_changed:
        action = "cancelled" if not application.interview_at else "scheduled" if not previous_interview else "rescheduled" if application.interview_at != previous_interview else "updated"
        record_event(db, "application.interview_updated", "application", application.id, actor_user_id=current_user.id, details={
            "action": action, "source": "company", "job_id": application.job_id,
            "interview_at": application.interview_at.isoformat() if application.interview_at else None,
            "previous_interview_at": previous_interview.isoformat() if previous_interview else None,
            "interview_mode": (application.interview_details or {}).get("mode"),
            "interview_minutes": (application.interview_details or {}).get("minutes")})
    if application.status in {ApplicationStatus.TECHNICAL_INTERVIEW, ApplicationStatus.PSYCHOMETRIC_TEST, ApplicationStatus.ACCEPTED, ApplicationStatus.HIRED} and application.identity_revealed_at is None:
        application.identity_revealed_at = datetime.utcnow()
        record_event(db, "application.identity_revealed", "application", application.id, actor_user_id=current_user.id, details={"stage": application.pipeline_stage, "job_id": application.job_id})
    if status_changed or stage_changed:
        transition(db, application, current_user.id, previous_status=previous_status, previous_stage=previous_stage)
    if application.status not in final_statuses and (interview_changed or status_changed or stage_changed):
        now = datetime.utcnow()
        if application.interview_at and application.interview_at > now:
            interview_deadline = application.interview_at + timedelta(minutes=(application.interview_details or {}).get("minutes", 45), days=application.job.response_days)
            # Do not close a process for silence before its scheduled interview.
            if application.response_due_at is None or application.response_due_at < interview_deadline:
                application.response_due_at = interview_deadline
                application.reminder_sent_at = None
            if application.first_response_at is None:
                application.first_response_at = now
        elif previous_interview and not application.interview_at:
            application.response_due_at = now + timedelta(days=application.job.response_days)
            application.reminder_sent_at = None
    if (status_changed or stage_changed) and application.status != ApplicationStatus.REJECTED:
        application.resolution_reason = None
    if application.status == ApplicationStatus.HIRED and (
        status_changed or stage_changed
    ):
        application.resolution_reason = None
        if any(
            stage.get("id") == "hired"
            for stage in stages_for(application.job)
        ):
            application.pipeline_stage = "hired"
        selected_company = application.job.company.name
        db.add(
            db.notifications.new(
                user_id=application.user_id,
                type="application_selected",
                title="¡Fuiste seleccionado!",
                body=(
                    f"{selected_company} te seleccionó para {application.job.title}. "
                    "La empresa se pondrá en contacto contigo para los siguientes pasos."
                ),
                action_url=f"/postulaciones?focus={application.id}",
            )
        )
    elif interview_action != "complete" and (status_changed or stage_changed or interview_changed):
        current_status = (
            application.status.value
            if hasattr(application.status, "value")
            else str(application.status)
        )
        if interview_changed and application.interview_at:
            notification_type = "application_interview"
            title = "Entrevista programada" if not previous_interview else "Entrevista reprogramada" if application.interview_at != previous_interview else "Detalles de entrevista actualizados"
            local_time = utc(application.interview_at).astimezone(timezone(timedelta(hours=-5)))
            details = application.interview_details or {}
            modality = "virtual" if details.get("mode") == "virtual" else "presencial" if details.get("mode") == "in_person" else "con modalidad por confirmar"
            body = f"Tu entrevista {modality} para {application.job.title} será el {local_time.strftime('%d/%m/%Y a las %H:%M')} (hora de Colombia). Revisa el lugar o enlace en el proceso. Si la añadiste a Google Calendar, se actualizará automáticamente."
        elif interview_changed:
            notification_type = "application_interview"
            title = "Entrevista cancelada"
            body = f"La empresa canceló la entrevista para {application.job.title}. Quedó registrado en el historial; si la añadiste a Google Calendar, se retirará automáticamente."
        else:
            notification_type = "application_status"
            stage_title = application.pipeline_stage_title or STATUS_LABELS.get(
                current_status, current_status
            )
            title = f"Proceso: {stage_title}"
            company_name = application.job.company.name
            previous_label = STATUS_LABELS.get(
                previous_status.value
                if hasattr(previous_status, "value")
                else str(previous_status),
                "la etapa anterior",
            )
            body = (
                f"{company_name} actualizó tu postulación a {application.job.title}: "
                f"pasó de {previous_label.lower()} a {stage_title.lower()}."
            )
        db.add(
            db.notifications.new(
                user_id=application.user_id,
                type=notification_type,
                title=title,
                body=body,
                action_url=f"/procesos/{application.id}",
            )
        )
    db.commit()
    db.refresh(application)
    return application


def delete_application(application_id: int, current_user: User, db: UnitOfWork) -> None:
    application = db.applications.get(application_id)
    if application is None:
        raise UseCaseError(status_code=404, detail="Postulacion no encontrada")
    if (
        current_user.role == UserRole.CANDIDATE
        and application.user_id != current_user.id
    ):
        raise UseCaseError(
            status_code=403, detail="No puedes eliminar esta postulacion"
        )
    if current_user.role == UserRole.COMPANY:
        company = db.companies.find_by_owner(current_user.id)
        if company is None or application.job.company_id != company.id:
            raise UseCaseError(
                status_code=403, detail="No puedes eliminar esta postulacion"
            )
        raise UseCaseError(status_code=403, detail="El historial del proceso se conserva. Comunica su finalización en lugar de eliminarlo")
    if current_user.role not in {UserRole.CANDIDATE, UserRole.COMPANY, UserRole.ADMIN}:
        raise UseCaseError(status_code=403, detail="Rol no autorizado")
    db.delete(application)
    db.commit()


def company_application_view(row, user, *, scores=None):
    hidden = user.role != UserRole.ADMIN and identity_hidden(row.job, row)
    fields = ["id", "user_id", "job_id", "status", "created_at", "job_title", "company_name", "candidate_name", "interview_at", "pipeline_stage", "pipeline_stage_title", "resolution_reason", "recruiter_notes", "screening_adjustment", "version", "response_due_at", "released_at", "candidate_feedback"]
    result = {key: getattr(row, key) for key in fields}
    result["base_match_percentage"], result["adjusted_match_percentage"] = scores if scores is not None else (row.base_match_percentage, row.adjusted_match_percentage)
    result["reviewed_at"] = row.reviewed_at
    result["interview_details"] = row.interview_details or {}
    result["interview_completed_at"] = row.interview_completed_at
    result["identity_hidden"] = hidden
    result["screening_answers"] = [] if hidden else row.screening_answers or []
    return result
