from typing import Literal

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import Response
from pydantic import BaseModel, Field

from app.api.deps import (
    get_current_user,
    get_resume_exporter,
    get_unit_of_work,
    require_roles,
)
from app.api.schemas.application import (
    ApplicationCreate,
    ApplicationResponse,
    ApplicationStatusUpdate,
    CompanyApplicationResponse,
)
from app.application.ports.unit_of_work import UnitOfWork
from app.application.use_cases import application_preparation, recruitment
from app.application.use_cases import applications as use_cases
from app.domain.entities.enums import UserRole
from app.domain.entities.records import Application, User
from app.domain.services.resume_filename import resume_disposition

router = APIRouter()


@router.get("/jobs/{job_id}/workspace")
def recruitment_workspace(job_id: int, bucket: Literal["inbox", "active", "closed", "interviews"] = "inbox",
    search: str = Query(default="", max_length=150), score_filter: Literal["all", "strong", "missing", "unreviewed"] = "all",
    order: Literal["score", "recent", "oldest"] = "score", stage: str | None = Query(default=None, max_length=80),
    page: int = Query(default=1, ge=1), page_size: int = Query(default=25, ge=1, le=50),
    user=Depends(require_roles(UserRole.COMPANY, UserRole.ADMIN)), db=Depends(get_unit_of_work)):
    return recruitment.workspace(db, user, job_id, bucket=bucket, search=search, score_filter=score_filter, order=order, stage=stage, page=page, page_size=page_size)


@router.get("/{application_id}/review")
def applicant_review(application_id: int, user=Depends(require_roles(UserRole.COMPANY, UserRole.ADMIN)), db=Depends(get_unit_of_work)):
    return recruitment.detail(db, user, application_id)


class ReviewRequest(BaseModel):
    expected_version: int = Field(ge=1)


@router.post("/{application_id}/reviewed")
def mark_reviewed(application_id: int, payload: ReviewRequest, user=Depends(require_roles(UserRole.COMPANY, UserRole.ADMIN)), db=Depends(get_unit_of_work)):
    return recruitment.mark_reviewed(db, user, application_id, payload.expected_version)


@router.get("/{application_id}/resume", response_class=Response)
def application_resume(application_id: int, user=Depends(get_current_user), db=Depends(get_unit_of_work), exporter=Depends(get_resume_exporter)):
    row = application_preparation.submitted_resume(db, user, application_id, exporter)
    return Response(row.pdf, media_type="application/pdf", headers={"Content-Disposition": resume_disposition(row.snapshot["name"]), "Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff"})


@router.post(
    "", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED
)
def apply_to_job(
    payload: ApplicationCreate,
    current_user: User = Depends(require_roles(UserRole.CANDIDATE)),
    db: UnitOfWork = Depends(get_unit_of_work),
    exporter=Depends(get_resume_exporter),
) -> Application:
    return use_cases.apply_to_job(
        payload=payload.model_dump(), current_user=current_user, db=db, exporter=exporter
    )


@router.get("/me", response_model=list[ApplicationResponse])
def my_applications(
    current_user: User = Depends(get_current_user),
    db: UnitOfWork = Depends(get_unit_of_work),
) -> list[Application]:
    return use_cases.my_applications(current_user=current_user, db=db)


@router.get("/jobs/{job_id}", response_model=list[CompanyApplicationResponse])
def job_applications(
    job_id: int,
    current_user: User = Depends(require_roles(UserRole.COMPANY, UserRole.ADMIN)),
    db: UnitOfWork = Depends(get_unit_of_work),
) -> list[Application]:
    return [use_cases.company_application_view(row, current_user) for row in use_cases.job_applications(job_id=job_id, current_user=current_user, db=db)]


@router.put("/jobs/{job_id}/mark-seen")
def mark_job_applications_seen(
    job_id: int,
    current_user: User = Depends(require_roles(UserRole.COMPANY, UserRole.ADMIN)),
    db: UnitOfWork = Depends(get_unit_of_work),
) -> dict[str, int]:
    return use_cases.mark_job_applications_seen(
        job_id=job_id, current_user=current_user, db=db
    )


@router.put("/{application_id}/status", response_model=CompanyApplicationResponse)
def update_status(
    application_id: int,
    payload: ApplicationStatusUpdate,
    current_user: User = Depends(require_roles(UserRole.COMPANY, UserRole.ADMIN)),
    db: UnitOfWork = Depends(get_unit_of_work),
) -> Application:
    row = use_cases.update_status(
        application_id=application_id,
        payload=payload.model_dump(exclude_unset=True),
        current_user=current_user,
        db=db,
    )
    return use_cases.company_application_view(row, current_user)


@router.delete("/{application_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_application(
    application_id: int,
    current_user: User = Depends(get_current_user),
    db: UnitOfWork = Depends(get_unit_of_work),
) -> None:
    return use_cases.delete_application(
        application_id=application_id, current_user=current_user, db=db
    )
