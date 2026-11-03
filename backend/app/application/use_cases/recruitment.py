from datetime import datetime

from app.application.errors import UseCaseError
from app.application.use_cases.applications import company_application_view
from app.application.use_cases.events import record_event
from app.application.use_cases.profiles import get_candidate_profile
from app.domain.entities.enums import UserRole


def authorized_job(db, user, job_id):
    job = db.jobs.get(job_id)
    if job is None:
        raise UseCaseError(status_code=404, detail="Vacante no encontrada")
    if user.role != UserRole.ADMIN:
        company = db.companies.find_for_access(user.id)
        if company is None or company.id != job.company_id:
            raise UseCaseError(status_code=403, detail="No puedes consultar estas postulaciones")
        member = db.organizations.member_for_user(user.id)
        if member and member.role == "interviewer":
            raise UseCaseError(status_code=403, detail="Tu acceso se limita a entrevistas asignadas")
    return job


def workspace(db, user, job_id, **filters):
    job = authorized_job(db, user, job_id)
    return db.applications.workspace_page(job, **filters)


def detail(db, user, application_id):
    row = db.applications.get(application_id)
    if row is None:
        raise UseCaseError(status_code=404, detail="Postulación no encontrada")
    authorized_job(db, user, row.job_id)
    try:
        profile = get_candidate_profile(row.user_id, user, db, job_id=row.job_id)
    except UseCaseError as error:
        if error.status_code != 404:
            raise
        profile = None
    allowed = ("profession", "experience", "education", "skills", "skill_levels", "experiences", "educations", "certifications", "languages", "availability", "location", "department", "identity_hidden", "submitted_resume_url")
    recommendation = db.recommendations.find_for_user_job(row.user_id, row.job_id)
    base = recommendation.match_percentage if recommendation else None
    scores = (base, max(0, min(100, base + (row.screening_adjustment or 0))) if base is not None else None)
    return {"application": {**company_application_view(row, user, scores=scores), "reviewed_at": row.reviewed_at},
            "profile": {key: profile.get(key) for key in allowed} if profile else None}


def mark_reviewed(db, user, application_id, expected_version):
    row = db.applications.get(application_id)
    if row is None:
        raise UseCaseError(status_code=404, detail="Postulación no encontrada")
    authorized_job(db, user, row.job_id)
    if row.reviewed_at is not None:
        return {"reviewed_at": row.reviewed_at, "version": row.version, "first_review": False}
    if row.version != expected_version:
        raise UseCaseError(status_code=409, detail="El proceso cambió; vuelve a abrir el perfil antes de marcarlo revisado")
    row.reviewed_at = datetime.utcnow()
    record_event(db, "application.reviewed", "application", row.id, actor_user_id=user.id, details={"job_id": row.job_id})
    db.commit()
    db.refresh(row)
    return {"reviewed_at": row.reviewed_at, "version": row.version, "first_review": True}
