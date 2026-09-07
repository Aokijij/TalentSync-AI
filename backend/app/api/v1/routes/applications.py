from fastapi import APIRouter, Depends, status

from app.api.deps import get_current_user, get_unit_of_work, require_roles
from app.api.schemas.application import (
    ApplicationCreate,
    ApplicationResponse,
    ApplicationStatusUpdate,
)
from app.application.ports.unit_of_work import UnitOfWork
from app.application.use_cases import applications as use_cases
from app.domain.entities.enums import UserRole
from app.domain.entities.records import Application, User

router = APIRouter()


@router.post(
    "", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED
)
def apply_to_job(
    payload: ApplicationCreate,
    current_user: User = Depends(require_roles(UserRole.CANDIDATE)),
    db: UnitOfWork = Depends(get_unit_of_work),
) -> Application:
    return use_cases.apply_to_job(
        payload=payload.model_dump(), current_user=current_user, db=db
    )


@router.get("/me", response_model=list[ApplicationResponse])
def my_applications(
    current_user: User = Depends(get_current_user),
    db: UnitOfWork = Depends(get_unit_of_work),
) -> list[Application]:
    return use_cases.my_applications(current_user=current_user, db=db)


@router.get("/jobs/{job_id}", response_model=list[ApplicationResponse])
def job_applications(
    job_id: int,
    current_user: User = Depends(require_roles(UserRole.COMPANY, UserRole.ADMIN)),
    db: UnitOfWork = Depends(get_unit_of_work),
) -> list[Application]:
    return use_cases.job_applications(job_id=job_id, current_user=current_user, db=db)


@router.put("/jobs/{job_id}/mark-seen")
def mark_job_applications_seen(
    job_id: int,
    current_user: User = Depends(require_roles(UserRole.COMPANY, UserRole.ADMIN)),
    db: UnitOfWork = Depends(get_unit_of_work),
) -> dict[str, int]:
    return use_cases.mark_job_applications_seen(
        job_id=job_id, current_user=current_user, db=db
    )


@router.put("/{application_id}/status", response_model=ApplicationResponse)
def update_status(
    application_id: int,
    payload: ApplicationStatusUpdate,
    current_user: User = Depends(require_roles(UserRole.COMPANY, UserRole.ADMIN)),
    db: UnitOfWork = Depends(get_unit_of_work),
) -> Application:
    return use_cases.update_status(
        application_id=application_id,
        payload=payload.model_dump(exclude_unset=True),
        current_user=current_user,
        db=db,
    )


@router.delete("/{application_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_application(
    application_id: int,
    current_user: User = Depends(get_current_user),
    db: UnitOfWork = Depends(get_unit_of_work),
) -> None:
    return use_cases.delete_application(
        application_id=application_id, current_user=current_user, db=db
    )
