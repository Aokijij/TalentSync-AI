from fastapi import APIRouter, Depends, File, UploadFile, status
from fastapi.responses import Response

from app.api.deps import get_current_user, get_image_storage, get_unit_of_work, require_roles
from app.api.schemas.company import (
    CompanyCreate,
    CompanyFollowResponse,
    CompanyFollowSettings,
    CompanyResponse,
    CompanyUpdate,
)
from app.application.ports.unit_of_work import UnitOfWork
from app.application.ports.services import ImageStorage
from app.application.use_cases import companies as use_cases
from app.domain.entities.enums import UserRole
from app.domain.entities.records import Company, User

router = APIRouter()


@router.post("", response_model=CompanyResponse)
def create_company(
    payload: CompanyCreate,
    current_user: User = Depends(require_roles(UserRole.COMPANY, UserRole.ADMIN)),
    db: UnitOfWork = Depends(get_unit_of_work),
) -> Company:
    return use_cases.create_company(
        payload=payload.model_dump(), current_user=current_user, db=db
    )


@router.get("/me", response_model=CompanyResponse)
def get_my_company(
    current_user: User = Depends(require_roles(UserRole.COMPANY, UserRole.ADMIN)),
    db: UnitOfWork = Depends(get_unit_of_work),
) -> Company:
    return use_cases.get_my_company(current_user=current_user, db=db)


@router.put("/me", response_model=CompanyResponse)
def update_my_company(
    payload: CompanyUpdate,
    current_user: User = Depends(require_roles(UserRole.COMPANY)),
    db: UnitOfWork = Depends(get_unit_of_work),
) -> Company:
    return use_cases.update_my_company(
        payload=payload.model_dump(exclude_unset=True), current_user=current_user, db=db
    )


@router.post("/me/logo", response_model=CompanyResponse)
def upload_company_logo(
    file: UploadFile = File(...),
    current_user: User = Depends(require_roles(UserRole.COMPANY)),
    db: UnitOfWork = Depends(get_unit_of_work),
    storage: ImageStorage = Depends(get_image_storage),
) -> Company:
    return use_cases.upload_company_image(
        file=file,
        kind="logo",
        current_user=current_user,
        db=db,
        storage=storage,
    )


@router.post("/me/cover", response_model=CompanyResponse)
def upload_company_cover(
    file: UploadFile = File(...),
    current_user: User = Depends(require_roles(UserRole.COMPANY)),
    db: UnitOfWork = Depends(get_unit_of_work),
    storage: ImageStorage = Depends(get_image_storage),
) -> Company:
    return use_cases.upload_company_image(
        file=file,
        kind="cover",
        current_user=current_user,
        db=db,
        storage=storage,
    )


@router.get("", response_model=list[CompanyResponse])
def list_companies(
    current_user: User = Depends(get_current_user),
    db: UnitOfWork = Depends(get_unit_of_work),
) -> list[Company]:
    return use_cases.list_companies(current_user=current_user, db=db)


@router.get("/{company_id}", response_model=CompanyResponse)
def get_company(
    company_id: int,
    current_user: User = Depends(get_current_user),
    db: UnitOfWork = Depends(get_unit_of_work),
) -> Company:
    return use_cases.get_company(company_id=company_id, db=db)


@router.get("/{company_id}/logo", response_class=Response)
def get_company_logo(
    company_id: int,
    db: UnitOfWork = Depends(get_unit_of_work),
    storage: ImageStorage = Depends(get_image_storage),
) -> Response:
    content, media_type = use_cases.company_image_content(
        company_id=company_id, kind="logo", db=db, storage=storage
    )
    return Response(content, media_type=media_type, headers={"Cache-Control": "no-cache", "X-Content-Type-Options": "nosniff"})


@router.get("/{company_id}/cover", response_class=Response)
def get_company_cover(
    company_id: int,
    db: UnitOfWork = Depends(get_unit_of_work),
    storage: ImageStorage = Depends(get_image_storage),
) -> Response:
    content, media_type = use_cases.company_image_content(
        company_id=company_id, kind="cover", db=db, storage=storage
    )
    return Response(content, media_type=media_type, headers={"Cache-Control": "no-cache", "X-Content-Type-Options": "nosniff"})


@router.get("/{company_id}/follow", response_model=CompanyFollowResponse)
def follow_status(
    company_id: int,
    current_user: User = Depends(require_roles(UserRole.CANDIDATE)),
    db: UnitOfWork = Depends(get_unit_of_work),
) -> dict:
    return use_cases.follow_status(
        company_id=company_id, current_user=current_user, db=db
    )


@router.put("/{company_id}/follow", response_model=CompanyFollowResponse)
def follow_company(
    company_id: int,
    payload: CompanyFollowSettings,
    current_user: User = Depends(require_roles(UserRole.CANDIDATE)),
    db: UnitOfWork = Depends(get_unit_of_work),
) -> dict:
    return use_cases.follow_company(
        company_id=company_id,
        min_match=payload.min_match,
        current_user=current_user,
        db=db,
    )


@router.delete("/{company_id}/follow", status_code=status.HTTP_204_NO_CONTENT)
def unfollow_company(
    company_id: int,
    current_user: User = Depends(require_roles(UserRole.CANDIDATE)),
    db: UnitOfWork = Depends(get_unit_of_work),
) -> None:
    use_cases.unfollow_company(
        company_id=company_id, current_user=current_user, db=db
    )
