from datetime import datetime
from types import SimpleNamespace
from typing import Any

from app.application.errors import UseCaseError
from app.application.ports.services import TextAnalysis
from app.application.ports.unit_of_work import UnitOfWork
from app.application.use_cases.matching import upsert_recommendation
from app.domain.entities.enums import ApplicationStatus, UserRole
from app.domain.entities.records import Company, Job, User
from app.domain.services.offer_review import review_offer
from app.domain.services.reputation import company_health

REVIEW_FIELDS = {"title", "description", "requirements", "salary", "location", "modality", "employment_type", "sector", "response_days", "quality_details", "skill_requirements", "pipeline_stages"}


def validate_guided_publication(values):
    if values.get("quality_details") and values.get("status") == "active":
        review = review_offer(SimpleNamespace(**values))
        if not review["can_publish"]:
            missing = [row["label"] for row in review["blockers"]]
            missing += [row["message"] for row in review["issues"] if row["severity"] == "critical"]
            raise UseCaseError(status_code=422, detail="Antes de publicar: " + "; ".join(missing) + ". Puedes guardar un borrador.")


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
    min_salary: float | None,
    max_salary: float | None,
    created_after: datetime | None,
    sort: str,
    db: UnitOfWork,
    current_user: User | None = None,
) -> list[Job]:
    jobs = db.jobs.search(
        search,
        modality,
        location,
        department,
        sector,
        employment_type,
        status_filter,
        min_salary,
        max_salary,
        created_after,
        sort,
    )
    company = owned_company(db, current_user) if current_user and current_user.role == UserRole.COMPANY else None
    visible = [job for job in jobs if job.status != "draft" or (current_user and current_user.role == UserRole.ADMIN)
            or (company and company.id == job.company_id)]
    return sorted(visible, key=lambda job: company_health(job.company)["visibility_reduced"]) if sort == "newest" else visible


def public_stats(db: UnitOfWork) -> dict[str, int]:
    return {
        "active_jobs": db.jobs.count_active(),
        "companies": db.companies.count(),
        "candidates": db.users.count_candidates(),
        "applications": db.applications.count(),
    }


def validate_retired_scenarios(questions: list[dict], previous: list[dict]) -> None:
    if any(question.get("category") == "work_scenario" and question not in previous for question in questions):
        raise UseCaseError(status_code=422, detail="Los escenarios de trabajo se retiraron. Usa preguntas de selección relacionadas con los requisitos del cargo.")


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
    accessible = owned_company(db, current_user) if current_user.role == UserRole.COMPANY else None
    if current_user.role != UserRole.ADMIN and (accessible is None or accessible.id != company.id):
        raise UseCaseError(status_code=403, detail="No puedes publicar en esta empresa")
    payload = dict(payload)
    validate_retired_scenarios(payload.get("application_questions") or [], [])
    if company.verification_required and company.verification_status != "verified":
        payload["status"] = "draft"
    validate_guided_publication({**payload, "id": None})
    analysis = nlp.analyze_job(
        f"{payload['title']} {payload['description']} {payload['requirements']}"
    )
    job = db.jobs.new(
        **{key: value for key, value in payload.items() if key != "company_id"},
        company_id=company.id,
        quality_revision=1 if payload.get("quality_details") else 0,
        skills=analysis.skills,
        embedding=analysis.embedding,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    if job.status == "draft":
        return job
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


def get_job(job_id: int, db: UnitOfWork, current_user: User | None = None) -> Job:
    job = db.jobs.get_with_company(job_id)
    if job is None:
        raise UseCaseError(status_code=404, detail="Vacante no encontrada")
    if job.status == "draft":
        if current_user is None:
            raise UseCaseError(status_code=404, detail="Vacante no encontrada")
        ensure_job_access(db, job, current_user)
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
    if job.quality_details and "quality_details" in changes and changes["quality_details"] is None:
        raise UseCaseError(status_code=422, detail="Conserva las condiciones de la revisión guiada")
    review_values = {key: changes.get(key, getattr(job, key, None)) for key in REVIEW_FIELDS | {"status", "id", "company_id", "blind_hiring"}}
    validate_guided_publication(review_values)
    review_changed = bool(review_values.get("quality_details")) and any(getattr(job, key, None) != changes[key] for key in REVIEW_FIELDS.intersection(changes))
    if "application_questions" in changes:
        validate_retired_scenarios(changes["application_questions"] or [], job.application_questions or [])
    if "response_days" in changes and changes["response_days"] is None:
        raise UseCaseError(status_code=422, detail="Indica un plazo de 1 a 30 días")
    if changes.get("status") == "active" and job.company.verification_required and job.company.verification_status != "verified":
        raise UseCaseError(status_code=403, detail="Verifica la empresa antes de publicar")
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
    if review_changed:
        job.quality_revision += 1
        from app.application.use_cases.events import record_event
        record_event(db, "job.quality_updated", "job", job.id, actor_user_id=current_user.id,
                     details={"version": job.quality_revision, "status": job.status})
        for application in job.applications:
            if application.status in {ApplicationStatus.HIRED, ApplicationStatus.REJECTED}:
                continue
            db.add(db.notifications.new(user_id=application.user_id, type="job_conditions_updated",
                   title="La empresa actualizó la oferta", body=f"Revisa las condiciones y el proceso de {job.title}. Versión {job.quality_revision}.",
                   action_url=f"/vacantes/{job.id}"))
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
            from app.application.use_cases.workflow import transition
            transition(db, application, current_user.id)
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
    if previous_status != "closed" and job.status == "closed":
        from app.application.use_cases.workflow import FINAL, transition
        for application in job.applications:
            if application.status not in FINAL and application.released_at is None:
                application.status = ApplicationStatus.REJECTED
                application.resolution_reason = "position_closed"
                application.candidate_feedback = {"source": "system", "reason_code": "position_closed", "message": "La empresa cerró la vacante. El proceso ha finalizado.", "created_at": datetime.utcnow().isoformat()}
                transition(db, application, current_user.id)
                db.add(db.notifications.new(user_id=application.user_id, type="application_closed", title="La vacante fue cerrada", body=f"La empresa cerró {job.title}.", action_url=f"/procesos/{application.id}"))
    db.commit()
    db.refresh(job)
    return job


def delete_job(job_id: int, current_user: User, db: UnitOfWork) -> None:
    job = db.jobs.get(job_id)
    if job is None:
        raise UseCaseError(status_code=404, detail="Vacante no encontrada")
    ensure_job_access(db, job, current_user)
    if current_user.role == UserRole.COMPANY and job.applications:
        raise UseCaseError(status_code=409, detail="Esta vacante tiene procesos con historial. Ciérrala para conservar su trazabilidad")
    db.delete(job)
    db.commit()


def reopen_job(job_id: int, mode: str, current_user: User, db: UnitOfWork, *, nlp: TextAnalysis) -> Job:
    job = get_job(job_id, db, current_user)
    ensure_job_access(db, job, current_user)
    if job.status != "filled":
        raise UseCaseError(status_code=409, detail="Solo puedes reabrir una vacante cubierta")
    if job.company.verification_required and job.company.verification_status != "verified":
        raise UseCaseError(status_code=403, detail="Verifica la empresa antes de publicar")
    if mode == "continue":
        validate_guided_publication({key: "active" if key == "status" else getattr(job, key, None) for key in REVIEW_FIELDS | {"status", "id", "company_id", "blind_hiring"}})
        job.status = "active"
        db.commit()
        db.refresh(job)
        return job
    # A new vacancy keeps the previous selection process and notifications intact.
    payload = {key: getattr(job, key) for key in ["company_id", "title", "description", "requirements", "salary", "location", "department", "modality", "employment_type", "sector", "benefits", "languages", "application_questions", "required_education_level", "required_study_fields"]}
    payload.update({key: getattr(job, key) for key in ["blind_hiring", "skill_requirements", "response_days", "quality_details"]})
    payload["application_questions"] = [question for question in payload["application_questions"] or [] if question.get("category") != "work_scenario"]
    payload["pipeline_stages"] = job.pipeline_stages
    return create_job(payload, current_user, db, nlp=nlp)


def get_application_questions(
    job_id: int, current_user: User, db: UnitOfWork
) -> list[dict]:
    job = get_job(job_id, db, current_user)
    ensure_job_access(db, job, current_user)
    return job.application_questions or []


def match_current_candidate(
    job_id: int, current_user: User, db: UnitOfWork, *, nlp: TextAnalysis
):
    job = db.jobs.get(job_id)
    if job is None or job.status == "draft":
        raise UseCaseError(status_code=404, detail="Vacante no encontrada")
    return upsert_recommendation(db, current_user, job, nlp=nlp)
