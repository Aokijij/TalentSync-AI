from typing import Any

from app.application.errors import UseCaseError
from app.application.ports.services import TextAnalysis
from app.application.ports.unit_of_work import UnitOfWork
from app.application.use_cases.matching import upsert_recommendation
from app.domain.entities.enums import ApplicationStatus, UserRole
from app.domain.entities.records import Company, Job, User


def owned_company(db: UnitOfWork, user: User) -> Company | None:
    return db.companies.find_by_owner(user.id)


def ensure_job_access(db: UnitOfWork, job: Job, user: User) -> None:
    if user.role == UserRole.ADMIN:
        return
    company = owned_company(db, user)
    if company is None or job.company_id != company.id:
        raise UseCaseError(status_code=403, detail="No puedes gestionar esta vacante")


def list_jobs(
    search: str | None,
    modality: str | None,
    location: str | None,
    department: str | None,
    sector: str | None,
    employment_type: str | None,
    status_filter: str | None,
    db: UnitOfWork,
) -> list[Job]:
    return db.jobs.search(
        search, modality, location, department, sector, employment_type, status_filter
    )


def create_job(
    payload: dict[str, Any], current_user: User, db: UnitOfWork, *, nlp: TextAnalysis
) -> Job:
    company = (
        db.companies.get(payload["company_id"])
        if payload["company_id"] is not None
        else owned_company(db, current_user)
    )
    if company is None:
        raise UseCaseError(
            status_code=404, detail="No hay empresa asociada para publicar la vacante"
        )
    if current_user.role != UserRole.ADMIN and company.owner_user_id != current_user.id:
        raise UseCaseError(status_code=403, detail="No puedes publicar en esta empresa")
    analysis = nlp.analyze_job(
        f"{payload['title']} {payload['description']} {payload['requirements']}"
    )
    job = db.jobs.new(
        **{key: value for key, value in payload.items() if key != "company_id"},
        company_id=company.id,
        skills=analysis.skills,
        embedding=analysis.embedding,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    for follow in db.companies.followers_for_company(company.id):
        candidate = follow.candidate
        if candidate.profile is None:
            continue
        recommendation = upsert_recommendation(db, candidate, job, nlp=nlp)
        if recommendation.match_percentage < follow.min_match:
            continue
        db.add(
            db.notifications.new(
                user_id=candidate.id,
                type="company_job_match",
                title=f"Nueva vacante de {company.name}",
                body=(
                    f"{company.name} publicó {job.title}, con "
                    f"{recommendation.match_percentage:.0f}% de compatibilidad contigo."
                ),
                action_url=f"/vacantes/{job.id}",
            )
        )
    db.commit()
    return job


def get_job(job_id: int, db: UnitOfWork) -> Job:
    job = db.jobs.get_with_company(job_id)
    if job is None:
        raise UseCaseError(status_code=404, detail="Vacante no encontrada")
    return job


def update_job(
    job_id: int,
    payload: dict[str, Any],
    current_user: User,
    db: UnitOfWork,
    *,
    nlp: TextAnalysis,
) -> Job:
    job = db.jobs.get(job_id)
    if job is None:
        raise UseCaseError(status_code=404, detail="Vacante no encontrada")
    ensure_job_access(db, job, current_user)
    changes = dict(payload)
    previous_status = job.status
    if previous_status == "filled" and changes.get("status") in {"active", "paused", "closed"}:
        raise UseCaseError(status_code=422, detail="Para reabrir la vacante, elige si deseas continuar el proceso o crear uno nuevo")
    if changes.get("status") == "filled" and not any(
        application.status.value == "hired" for application in job.applications
    ):
        raise UseCaseError(
            status_code=422,
            detail="Selecciona primero a la persona contratada en el proceso de la vacante",
        )
    if "pipeline_stages" in changes:
        remaining_ids = {stage["id"] for stage in changes["pipeline_stages"]}
        occupied_ids = {
            application.pipeline_stage
            for application in job.applications
            if application.pipeline_stage
        }
        removed_occupied = occupied_ids - remaining_ids
        if removed_occupied:
            raise UseCaseError(
                status_code=422,
                detail="No puedes eliminar una etapa que todavía tiene candidatos",
            )
    for key, value in changes.items():
        setattr(job, key, value)
    if previous_status != "filled" and job.status == "filled":
        rejected_stage = next(
            (
                stage["id"]
                for stage in job.pipeline_stages or []
                if stage["id"] == "rejected"
            ),
            None,
        )
        for application in db.applications.for_job(job.id):
            if application.status in {
                ApplicationStatus.HIRED,
                ApplicationStatus.REJECTED,
            }:
                continue
            application.status = ApplicationStatus.REJECTED
            application.resolution_reason = "another_candidate_selected"
            if rejected_stage:
                application.pipeline_stage = rejected_stage
            db.add(
                db.notifications.new(
                    user_id=application.user_id,
                    type="application_not_selected",
                    title="La vacante fue cubierta",
                    body=(
                        f"{job.company.name} finalizó el proceso de {job.title} "
                        "porque completó las contrataciones necesarias. Se seleccionó a otra persona."
                    ),
                    action_url=f"/postulaciones?focus={application.id}",
                )
            )
    if {"title", "description", "requirements"}.intersection(changes):
        analysis = nlp.analyze_job(f"{job.title} {job.description} {job.requirements}")
        job.skills = analysis.skills
        job.embedding = analysis.embedding
    db.commit()
    db.refresh(job)
    return job


def delete_job(job_id: int, current_user: User, db: UnitOfWork) -> None:
    job = db.jobs.get(job_id)
    if job is None:
        raise UseCaseError(status_code=404, detail="Vacante no encontrada")
    ensure_job_access(db, job, current_user)
    db.delete(job)
    db.commit()


def reopen_job(job_id: int, mode: str, current_user: User, db: UnitOfWork, *, nlp: TextAnalysis) -> Job:
    job = get_job(job_id, db)
    ensure_job_access(db, job, current_user)
    if job.status != "filled":
        raise UseCaseError(status_code=409, detail="Solo puedes reabrir una vacante cubierta")
    if mode == "continue":
        job.status = "active"
        db.commit()
        db.refresh(job)
        return job
    # A new vacancy keeps the previous selection process and notifications intact.
    payload = {key: getattr(job, key) for key in ["company_id", "title", "description", "requirements", "salary", "location", "department", "modality", "employment_type", "sector", "benefits", "languages"]}
    payload["pipeline_stages"] = job.pipeline_stages
    return create_job(payload, current_user, db, nlp=nlp)


def match_current_candidate(
    job_id: int, current_user: User, db: UnitOfWork, *, nlp: TextAnalysis
):
    job = db.jobs.get(job_id)
    if job is None:
        raise UseCaseError(status_code=404, detail="Vacante no encontrada")
    return upsert_recommendation(db, current_user, job, nlp=nlp)
