from datetime import datetime
from types import SimpleNamespace

from app.application.errors import UseCaseError
from app.application.use_cases.jobs import ensure_job_access, owned_company
from app.domain.services.offer_review import feedback_summary, review_offer


def quality(db, user, job_id):
    job = db.jobs.get(job_id)
    if job is None:
        raise UseCaseError(status_code=404, detail="Vacante no encontrada")
    ensure_job_access(db, job, user)
    report = review_offer(job, db.jobs.active())
    report["feedback"] = feedback_summary(db.jobs.offer_feedback_for(job.id), job.quality_revision)
    report["revision"] = job.quality_revision
    report["guided"] = bool(job.quality_details)
    return report


def preview(db, user, payload):
    values = dict(payload)
    job_id = values.pop("job_id", None)
    if job_id is not None:
        job = db.jobs.get(job_id)
        if job is None:
            raise UseCaseError(status_code=404, detail="Vacante no encontrada")
        ensure_job_access(db, job, user)
        values.update(id=job.id, company_id=job.company_id)
    else:
        company = owned_company(db, user)
        values.update(id=None, company_id=company.id if company else None)
    return review_offer(SimpleNamespace(**values), db.jobs.active())


def candidate_feedback(db, user, job_id, reason=None, *, remove=False):
    job = db.jobs.get(job_id)
    if job is None or job.status == "draft":
        raise UseCaseError(status_code=404, detail="Vacante no encontrada")
    row = db.jobs.candidate_offer_feedback(user.id, job_id)
    if remove:
        if row:
            db.delete(row)
        db.commit()
        return {"reason": None}
    if reason is not None:
        if job.status != "active":
            raise UseCaseError(status_code=409, detail="La vacante ya no recibe opiniones")
        if row is None:
            row = db.jobs.new_offer_feedback(user_id=user.id, job_id=job_id)
            db.add(row)
        row.reason = reason
        row.revision = job.quality_revision
        row.created_at = datetime.utcnow()
        db.commit()
    return {"reason": row.reason if row and row.revision == job.quality_revision else None}
