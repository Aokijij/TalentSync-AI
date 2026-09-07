from fastapi import APIRouter, Depends

from app.api.deps import get_current_user, get_unit_of_work, require_roles
from app.api.schemas.company import CompanyCreate, CompanyResponse, CompanyUpdate
from app.application.ports.unit_of_work import UnitOfWork
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


@router.get("", response_model=list[CompanyResponse])
def list_companies(
    current_user: User = Depends(get_current_user),
    db: UnitOfWork = Depends(get_unit_of_work),
) -> list[Company]:
    return use_cases.list_companies(current_user=current_user, db=db)
