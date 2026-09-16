from fastapi import APIRouter, Depends, Query

from app.api.deps import get_text_analysis, get_unit_of_work, require_roles
from app.api.schemas.notification import NotificationResponse
from app.api.schemas.recommendation import RankedCandidate, RecommendationResponse
from app.application.ports.services import TextAnalysis
from app.application.ports.unit_of_work import UnitOfWork
from app.application.use_cases import recommendations as use_cases
from app.domain.entities.enums import UserRole
from app.domain.entities.records import Recommendation, User

router = APIRouter()


@router.get("/me/jobs", response_model=list[RecommendationResponse])
def my_recommended_jobs(
    include_all: bool = Query(default=False),
    current_user: User = Depends(require_roles(UserRole.CANDIDATE, UserRole.ADMIN)),
    db: UnitOfWork = Depends(get_unit_of_work),
    *,
    nlp: TextAnalysis = Depends(get_text_analysis),
) -> list[Recommendation]:
    return use_cases.my_recommended_jobs(
        include_all=include_all, current_user=current_user, db=db, nlp=nlp
    )


@router.get("/jobs/{job_id}/candidates", response_model=list[RankedCandidate])
def ranked_candidates(
    job_id: int,
    current_user: User = Depends(require_roles(UserRole.COMPANY, UserRole.ADMIN)),
    db: UnitOfWork = Depends(get_unit_of_work),
    *,
    nlp: TextAnalysis = Depends(get_text_analysis),
) -> list[RankedCandidate]:
    return use_cases.ranked_candidates(
        job_id=job_id, current_user=current_user, db=db, nlp=nlp
    )


@router.post(
    "/jobs/{job_id}/candidates/{user_id}/invite",
    response_model=NotificationResponse,
)
def invite_candidate(
    job_id: int,
    user_id: int,
    current_user: User = Depends(require_roles(UserRole.COMPANY, UserRole.ADMIN)),
    db: UnitOfWork = Depends(get_unit_of_work),
    *,
    nlp: TextAnalysis = Depends(get_text_analysis),
):
    return use_cases.invite_candidate(
        job_id=job_id,
        user_id=user_id,
        current_user=current_user,
        db=db,
        nlp=nlp,
    )
