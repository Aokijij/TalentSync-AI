from typing import Any

from app.application.errors import UseCaseError
from app.application.ports.services import AccountSecurity, TextAnalysis
from app.application.ports.unit_of_work import UnitOfWork
from app.domain.entities.enums import UserRole
from app.domain.entities.records import User
from app.domain.services.skills import normalize_skills


def register(
    payload: dict[str, Any],
    db: UnitOfWork,
    *,
    nlp: TextAnalysis,
    security: AccountSecurity,
) -> User:
    if payload["role"] == UserRole.ADMIN:
        raise UseCaseError(
            status_code=403,
            detail="No se puede registrar un administrador por este canal",
        )
    if db.users.find_by_email(payload["email"]):
        raise UseCaseError(status_code=409, detail="El email ya esta registrado")
    if payload["role"] == UserRole.COMPANY:
        if not payload["company_name"] or not payload["nit"]:
            raise UseCaseError(
                status_code=422,
                detail="Las cuentas empresa requieren nombre de empresa y NIT",
            )
        if db.companies.find_by_nit(payload["nit"]):
            raise UseCaseError(
                status_code=409, detail="Ya existe una empresa registrada con ese NIT"
            )
    user = db.users.new(
        name=payload["name"],
        email=payload["email"],
        password_hash=security.hash_password(payload["password"]),
        role=payload["role"],
    )
    db.add(user)
    db.flush()
    profile_text = " ".join(
        filter(
            None,
            [
                payload["profession"],
                " ".join(payload["skills"]),
                payload["experience"],
                payload["education"],
            ],
        )
    )
    nlp_result = nlp.analyze_cv(profile_text) if profile_text else None
    db.add(
        db.profiles.new(
            user_id=user.id,
            profession=payload["profession"]
            if payload["profession"]
            else nlp_result.profession
            if nlp_result
            else None,
            skills=normalize_skills(
                payload["skills"]
                if payload["skills"]
                else nlp_result.skills
                if nlp_result
                else []
            ),
            experience=payload["experience"]
            if payload["experience"]
            else nlp_result.experience
            if nlp_result
            else None,
            education=payload["education"]
            if payload["education"]
            else nlp_result.education
            if nlp_result
            else None,
            location=nlp_result.location if nlp_result else None,
            phone=nlp_result.phone if nlp_result else None,
            experiences=nlp_result.experiences if nlp_result else [],
            educations=nlp_result.educations if nlp_result else [],
            certifications=nlp_result.certifications if nlp_result else [],
            embedding=nlp.embed(profile_text) if profile_text else None,
        )
    )
    if payload["role"] == UserRole.COMPANY:
        db.add(
            db.companies.new(
                owner_user_id=user.id,
                name=payload["company_name"],
                nit=payload["nit"],
                description=payload["company_description"],
            )
        )
    db.commit()
    db.refresh(user)
    return user


def login(
    payload: dict[str, Any], db: UnitOfWork, *, security: AccountSecurity
) -> dict:
    user = db.users.find_by_email(payload["email"])
    if user is None or not security.verify_password(
        payload["password"], user.password_hash
    ):
        raise UseCaseError(status_code=401, detail="Credenciales invalidas")
    return dict(
        access_token=security.create_access_token(str(user.id), user.role.value)
    )


def me(current_user: User) -> User:
    return current_user
