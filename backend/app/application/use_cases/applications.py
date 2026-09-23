from typing import Any

from app.application.errors import UseCaseError
from app.application.ports.unit_of_work import UnitOfWork
from app.domain.entities.enums import ApplicationStatus, UserRole
from app.domain.entities.records import Application, User


def _normalize(value: str) -> str:
    return " ".join(value.lower().strip().split())


def _screening_result(job, submitted: list[dict]) -> tuple[list[dict], float]:
    questions = job.application_questions or []
    submitted_by_id = {
        item["question_id"]: str(item["answer"]).strip() for item in submitted
    }
    known_ids = {question["id"] for question in questions}
    if set(submitted_by_id) - known_ids:
        raise UseCaseError(status_code=422, detail="Hay respuestas para preguntas que no pertenecen a la vacante")
    saved: list[dict] = []
    adjustment = 0.0
    for question in questions:
        answer = submitted_by_id.get(question["id"], "")
        if question.get("required", True) and not answer:
            raise UseCaseError(status_code=422, detail=f"Responde la pregunta: {question['prompt']}")
        if not answer:
            continue
        if question.get("type") == "choice" and answer not in question.get("options", []):
            raise UseCaseError(status_code=422, detail=f"Selecciona una opción válida para: {question['prompt']}")
        normalized_answer = _normalize(answer)
        if question.get("type") == "choice":
            preferred = question.get("preferred_options", [])
            if preferred:
                adjustment += (
                    question.get("positive_adjustment", 0)
                    if answer in preferred
                    else question.get("negative_adjustment", 0)
                )
        else:
            keywords = [_normalize(item) for item in question.get("keywords", []) if item.strip()]
            if keywords:
                adjustment += (
                    question.get("positive_adjustment", 0)
                    if any(keyword in normalized_answer for keyword in keywords)
                    else question.get("negative_adjustment", 0)
                )
        saved.append(
            {"question_id": question["id"], "question": question["prompt"], "answer": answer}
        )
    return saved, max(-20.0, min(20.0, adjustment))

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
    payload: dict[str, Any], current_user: User, db: UnitOfWork
) -> Application:
    job = db.jobs.get(payload["job_id"])
    if job is None or job.status != "active":
        raise UseCaseError(status_code=404, detail="La vacante no esta disponible")
    existing = db.applications.find_for_user_job(current_user.id, payload["job_id"])
    if existing:
        return existing
    answers, screening_adjustment = _screening_result(
        job, payload.get("screening_answers", [])
    )
    first_stage = (job.pipeline_stages or [{"id": "submitted"}])[0]["id"]
    application = db.applications.new(
        user_id=current_user.id,
        job_id=payload["job_id"],
        pipeline_stage=first_stage,
        screening_answers=answers,
        screening_adjustment=screening_adjustment,
    )
    db.add(application)
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
    previous_status = application.status
    previous_stage = application.pipeline_stage
    previous_interview = application.interview_at
    requested_stage = changes.pop("pipeline_stage", None)
    if requested_stage is not None:
        configured = {
            stage["id"]: stage for stage in application.job.pipeline_stages or []
        }
        if requested_stage not in configured:
            raise UseCaseError(
                status_code=422,
                detail="La etapa no pertenece al proceso de esta vacante",
            )
        application.pipeline_stage = requested_stage
        application.status = LEGACY_STAGE_STATUS.get(
            requested_stage, ApplicationStatus.REVIEWING
        )
    for key, value in changes.items():
        setattr(application, key, value)
    status_changed = application.status != previous_status
    stage_changed = application.pipeline_stage != previous_stage
    interview_changed = application.interview_at != previous_interview
    if (status_changed or stage_changed) and application.status != ApplicationStatus.REJECTED:
        application.resolution_reason = None
    if application.status == ApplicationStatus.HIRED and (
        status_changed or stage_changed
    ):
        application.resolution_reason = None
        if any(
            stage.get("id") == "hired"
            for stage in application.job.pipeline_stages or []
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
    elif status_changed or stage_changed or interview_changed:
        current_status = (
            application.status.value
            if hasattr(application.status, "value")
            else str(application.status)
        )
        if interview_changed and application.interview_at:
            notification_type = "application_interview"
            title = "Entrevista programada"
            body = f"Tu entrevista para {application.job.title} será el {application.interview_at.strftime('%d/%m/%Y a las %H:%M')}."
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
                action_url=f"/postulaciones?focus={application.id}",
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
    if current_user.role not in {UserRole.CANDIDATE, UserRole.COMPANY, UserRole.ADMIN}:
        raise UseCaseError(status_code=403, detail="Rol no autorizado")
    db.delete(application)
    db.commit()
