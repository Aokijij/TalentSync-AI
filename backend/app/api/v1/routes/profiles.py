from fastapi import APIRouter, Depends, File, UploadFile

from app.api.deps import (
    get_current_user,
    get_resume_reader,
    get_text_analysis,
    get_unit_of_work,
    require_roles,
)
from app.api.schemas.profile import (
    CandidateProfileResponse,
    ProfileResponse,
    ProfileUpdate,
)
from app.application.ports.services import ResumeReader, TextAnalysis
from app.application.ports.unit_of_work import UnitOfWork
from app.application.use_cases import profiles as use_cases
from app.domain.entities.enums import UserRole
from app.domain.entities.records import Profile, User

router = APIRouter()


@router.get("/me", response_model=ProfileResponse)
def get_my_profile(current_user: User = Depends(get_current_user)) -> Profile:
    return use_cases.get_my_profile(current_user=current_user)


@router.get("/candidates/{user_id}", response_model=CandidateProfileResponse)
def get_candidate_profile(
    user_id: int,
    current_user: User = Depends(require_roles(UserRole.COMPANY, UserRole.ADMIN)),
    db: UnitOfWork = Depends(get_unit_of_work),
) -> dict:
    return use_cases.get_candidate_profile(
        user_id=user_id, current_user=current_user, db=db
    )


@router.put("/me", response_model=ProfileResponse)
def update_my_profile(
    payload: ProfileUpdate,
    current_user: User = Depends(require_roles(UserRole.CANDIDATE, UserRole.ADMIN)),
    db: UnitOfWork = Depends(get_unit_of_work),
    *,
    nlp: TextAnalysis = Depends(get_text_analysis),
) -> Profile:
    return use_cases.update_my_profile(
        payload=payload.model_dump(), current_user=current_user, db=db, nlp=nlp
    )


@router.post("/me/cv", response_model=ProfileResponse)
def upload_cv(
    file: UploadFile = File(...),
    current_user: User = Depends(require_roles(UserRole.CANDIDATE, UserRole.ADMIN)),
    db: UnitOfWork = Depends(get_unit_of_work),
    *,
    nlp: TextAnalysis = Depends(get_text_analysis),
    resumes: ResumeReader = Depends(get_resume_reader),
) -> Profile:
    return use_cases.upload_cv(
        file=file, current_user=current_user, db=db, nlp=nlp, resumes=resumes
    )
