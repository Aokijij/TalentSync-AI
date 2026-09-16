from pathlib import Path
from typing import Any
from uuid import uuid4

from app.application.errors import UseCaseError
from app.application.ports.services import ImageStorage
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


def get_company(company_id: int, db: UnitOfWork) -> Company:
    company = db.companies.get(company_id)
    if company is None:
        raise UseCaseError(status_code=404, detail="Empresa no encontrada")
    return company


def upload_company_image(
    file,
    kind: str,
    current_user: User,
    db: UnitOfWork,
    *,
    storage: ImageStorage,
) -> Company:
    if kind not in {"logo", "cover"}:
        raise UseCaseError(status_code=400, detail="Tipo de imagen no válido")
    company = db.companies.find_by_owner(current_user.id)
    if company is None:
        raise UseCaseError(
            status_code=404, detail="Esta cuenta no tiene una empresa asociada"
        )
    allowed_types = {
        "image/jpeg": ("jpg", b"\xff\xd8\xff"),
        "image/png": ("png", b"\x89PNG\r\n\x1a\n"),
        "image/webp": ("webp", b"RIFF"),
    }
    image_type = allowed_types.get(file.content_type or "")
    if image_type is None:
        raise UseCaseError(
            status_code=400, detail="La imagen debe ser JPG, PNG o WebP"
        )
    extension, signature = image_type
    size_limit = 5 * 1024 * 1024 if kind == "cover" else 3 * 1024 * 1024
    content = file.file.read(size_limit + 1)
    if not content:
        raise UseCaseError(status_code=400, detail="La imagen está vacía")
    if len(content) > size_limit:
        limit = 5 if kind == "cover" else 3
        raise UseCaseError(
            status_code=400, detail=f"La imagen no puede superar {limit} MB"
        )
    if not content.startswith(signature) or (
        extension == "webp" and content[8:12] != b"WEBP"
    ):
        raise UseCaseError(status_code=400, detail="El archivo no es una imagen válida")

    filename = f"company_{company.id}_{kind}_{uuid4().hex}.{extension}"
    storage.save("company_images", filename, content, file.content_type)
    setattr(company, f"{kind}_filename", filename)
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


def company_image_content(
    company_id: int, kind: str, db: UnitOfWork, *, storage: ImageStorage
) -> tuple[bytes, str]:
    if kind not in {"logo", "cover"}:
        raise UseCaseError(status_code=404, detail="Imagen no encontrada")
    company = db.companies.get(company_id)
    filename = getattr(company, f"{kind}_filename", None) if company else None
    if not filename:
        raise UseCaseError(status_code=404, detail="Imagen no encontrada")
    media_type = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
    }.get(Path(filename).suffix.lower(), "application/octet-stream")
    return storage.read("company_images", filename), media_type


def follow_company(
    company_id: int, min_match: float, current_user: User, db: UnitOfWork
) -> dict:
    if db.companies.get(company_id) is None:
        raise UseCaseError(status_code=404, detail="Empresa no encontrada")
    follow = db.companies.find_follow(current_user.id, company_id)
    if follow is None:
        follow = db.companies.new_follow(
            candidate_user_id=current_user.id,
            company_id=company_id,
            min_match=min_match,
        )
        db.add(follow)
    else:
        follow.min_match = min_match
    db.commit()
    return {
        "company_id": company_id,
        "is_following": True,
        "min_match": follow.min_match,
    }


def unfollow_company(company_id: int, current_user: User, db: UnitOfWork) -> None:
    follow = db.companies.find_follow(current_user.id, company_id)
    if follow is not None:
        db.delete(follow)
        db.commit()


def follow_status(company_id: int, current_user: User, db: UnitOfWork) -> dict:
    if db.companies.get(company_id) is None:
        raise UseCaseError(status_code=404, detail="Empresa no encontrada")
    follow = db.companies.find_follow(current_user.id, company_id)
    return {
        "company_id": company_id,
        "is_following": follow is not None,
        "min_match": follow.min_match if follow else 60,
    }
