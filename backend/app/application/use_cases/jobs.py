from typing import Any

from app.application.errors import UseCaseError
from app.application.ports.services import TextAnalysis
from app.application.ports.unit_of_work import UnitOfWork
from app.application.use_cases.matching import upsert_recommendation
from app.domain.entities.enums import UserRole
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


def match_current_candidate(
    job_id: int, current_user: User, db: UnitOfWork, *, nlp: TextAnalysis
):
    job = db.jobs.get(job_id)
    if job is None:
        raise UseCaseError(status_code=404, detail="Vacante no encontrada")
    return upsert_recommendation(db, current_user, job, nlp=nlp)
