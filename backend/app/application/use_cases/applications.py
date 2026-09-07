from typing import Any

from app.application.errors import UseCaseError
from app.application.ports.unit_of_work import UnitOfWork
from app.domain.entities.enums import ApplicationStatus, UserRole
from app.domain.entities.records import Application, User

STATUS_LABELS = {
    "submitted": "Recibida",
    "seen": "Vista por la empresa",
    "reviewing": "En revisión",
    "shortlisted": "Preseleccionada",
    "technical_interview": "Entrevista técnica",
    "psychometric_test": "Prueba psicotécnica",
    "accepted": "Aceptada",
    "hired": "Contratado",
    "rejected": "Descartada",
}
LEGACY_STAGE_STATUS = {
    "submitted": ApplicationStatus.SUBMITTED,
    "shortlisted": ApplicationStatus.SHORTLISTED,
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
    first_stage = (job.pipeline_stages or [{"id": "submitted"}])[0]["id"]
    application = db.applications.new(
        user_id=current_user.id, job_id=payload["job_id"], pipeline_stage=first_stage
    )
    db.add(application)
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
    if status_changed or stage_changed or interview_changed:
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
            body = f"Tu postulación a {application.job.title} avanzó a {stage_title.lower()}."
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
