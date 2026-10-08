from app.application.errors import UseCaseError
from app.application.use_cases.jobs import ensure_job_access
from app.domain.services.job_quality import assess_quality


def quality(db, user, job_id):
    job = db.jobs.get(job_id)
    if job is None:
        raise UseCaseError(status_code=404, detail="Vacante no encontrada")
    ensure_job_access(db, job, user)
    return assess_quality(job, db.jobs.active())
