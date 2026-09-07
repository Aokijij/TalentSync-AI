from typing import Any

from app.application.errors import UseCaseError
from app.application.ports.unit_of_work import UnitOfWork
from app.domain.entities.enums import UserRole
from app.domain.entities.records import Company, User


def create_company(
    payload: dict[str, Any], current_user: User, db: UnitOfWork
) -> Company:
    if current_user.role == UserRole.COMPANY and db.companies.find_by_owner(
        current_user.id
    ):
        raise UseCaseError(
            status_code=409, detail="Esta cuenta ya tiene una empresa asociada"
        )
    if db.companies.find_by_nit(payload["nit"]):
        raise UseCaseError(status_code=409, detail="Ya existe una empresa con ese NIT")
    company = db.companies.new(owner_user_id=current_user.id, **dict(payload))
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


def get_my_company(current_user: User, db: UnitOfWork) -> Company:
    company = db.companies.find_by_owner(current_user.id)
    if company is None:
        raise UseCaseError(
            status_code=404, detail="Esta cuenta no tiene una empresa asociada"
        )
    return company


def update_my_company(
    payload: dict[str, Any], current_user: User, db: UnitOfWork
) -> Company:
    company = db.companies.find_by_owner(current_user.id)
    if company is None:
        raise UseCaseError(
            status_code=404, detail="Esta cuenta no tiene una empresa asociada"
        )
    changes = dict(payload)
    if "nit" in changes and changes["nit"] != company.nit:
        existing = db.companies.find_by_nit(changes["nit"])
        if existing is not None:
            raise UseCaseError(
                status_code=409, detail="Ya existe una empresa con ese NIT"
            )
    for key, value in changes.items():
        setattr(company, key, value)
    db.commit()
    db.refresh(company)
    return company


def list_companies(current_user: User, db: UnitOfWork) -> list[Company]:
    return db.companies.list_owned(
        current_user.id if current_user.role == UserRole.COMPANY else None
    )
