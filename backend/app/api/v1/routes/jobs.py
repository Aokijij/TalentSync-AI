from datetime import datetime

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_text_analysis, get_unit_of_work, require_roles
from app.api.schemas.job import (
    JobCreate,
    JobResponse,
    JobUpdate,
    JobReopen,
    PublicStatsResponse,
    ScreeningQuestionConfig,
)
from app.api.schemas.recommendation import RecommendationResponse
from app.application.ports.services import TextAnalysis
from app.application.ports.unit_of_work import UnitOfWork
from app.application.use_cases import jobs as use_cases
from app.domain.entities.enums import UserRole
from app.domain.entities.records import Job, User

router = APIRouter()


@router.get("", response_model=list[JobResponse])
def list_jobs(
    search: str | None = None,
    modality: str | None = None,
    location: str | None = None,
    department: str | None = None,
    sector: str | None = None,
    employment_type: str | None = None,
    status_filter: str | None = Query(default="active", alias="status"),
    min_salary: float | None = Query(default=None, ge=0),
    max_salary: float | None = Query(default=None, ge=0),
    created_after: datetime | None = None,
    sort: str = Query(default="newest", pattern="^(newest|oldest|salary_asc|salary_desc)$"),
    db: UnitOfWork = Depends(get_unit_of_work),
) -> list[Job]:
    return use_cases.list_jobs(
        search=search,
        modality=modality,
        location=location,
        department=department,
        sector=sector,
        employment_type=employment_type,
        status_filter=status_filter,
        min_salary=min_salary,
        max_salary=max_salary,
        created_after=created_after,
        sort=sort,
        db=db,
    )


@router.get("/public-stats", response_model=PublicStatsResponse)
def get_public_stats(
    db: UnitOfWork = Depends(get_unit_of_work),
) -> dict[str, int]:
    return use_cases.public_stats(db)


@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
def create_job(
    payload: JobCreate,
    current_user: User = Depends(require_roles(UserRole.COMPANY, UserRole.ADMIN)),
    db: UnitOfWork = Depends(get_unit_of_work),
    *,
    nlp: TextAnalysis = Depends(get_text_analysis),
) -> Job:
    return use_cases.create_job(
        payload=payload.model_dump(), current_user=current_user, db=db, nlp=nlp
    )


@router.get("/{job_id}", response_model=JobResponse)
def get_job(job_id: int, db: UnitOfWork = Depends(get_unit_of_work)) -> Job:
    return use_cases.get_job(job_id=job_id, db=db)


@router.get(
    "/{job_id}/application-questions",
    response_model=list[ScreeningQuestionConfig],
)
def get_application_questions(
    job_id: int,
    current_user: User = Depends(require_roles(UserRole.COMPANY, UserRole.ADMIN)),
    db: UnitOfWork = Depends(get_unit_of_work),
):
    return use_cases.get_application_questions(job_id, current_user, db)


@router.patch("/{job_id}", response_model=JobResponse)
def update_job(
    job_id: int,
    payload: JobUpdate,
    current_user: User = Depends(require_roles(UserRole.COMPANY, UserRole.ADMIN)),
    db: UnitOfWork = Depends(get_unit_of_work),
    *,
    nlp: TextAnalysis = Depends(get_text_analysis),
) -> Job:
    return use_cases.update_job(
        job_id=job_id,
        payload=payload.model_dump(exclude_unset=True),
        current_user=current_user,
        db=db,
        nlp=nlp,
    )


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job(
    job_id: int,
    current_user: User = Depends(require_roles(UserRole.COMPANY, UserRole.ADMIN)),
    db: UnitOfWork = Depends(get_unit_of_work),
) -> None:
    return use_cases.delete_job(job_id=job_id, current_user=current_user, db=db)


@router.post("/{job_id}/reopen", response_model=JobResponse)
def reopen_job(
    job_id: int,
    payload: JobReopen,
    current_user: User = Depends(require_roles(UserRole.COMPANY, UserRole.ADMIN)),
    db: UnitOfWork = Depends(get_unit_of_work),
    nlp: TextAnalysis = Depends(get_text_analysis),
):
    return use_cases.reopen_job(job_id, payload.mode, current_user, db, nlp=nlp)


@router.post("/{job_id}/match", response_model=RecommendationResponse)
def match_current_candidate(
    job_id: int,
    current_user: User = Depends(require_roles(UserRole.CANDIDATE, UserRole.ADMIN)),
    db: UnitOfWork = Depends(get_unit_of_work),
    *,
    nlp: TextAnalysis = Depends(get_text_analysis),
):
    return use_cases.match_current_candidate(
        job_id=job_id, current_user=current_user, db=db, nlp=nlp
    )
