from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.application.ports.services import AccountSecurity as AccountSecurityPort
from app.application.ports.services import ResumeReader as ResumeReaderPort
from app.application.ports.services import TextAnalysis
from app.application.ports.unit_of_work import UnitOfWork
from app.application.use_cases.account_security import resolve_session
from app.application.use_cases.organizations import authorize_request
from app.core.config import settings
from app.domain.entities.enums import UserRole
from app.infrastructure.database.models import User
from app.infrastructure.database.session import get_db
from app.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork
from app.infrastructure.images import get_image_storage as get_image_storage
from app.infrastructure.job_catalogs import (
    AdzunaJobCatalog,
    JoobleJobCatalog,
    JSearchJobCatalog,
)
from app.infrastructure.nlp.resumes import ResumeReader
from app.infrastructure.nlp.text_processor import text_processor
from app.infrastructure.security.accounts import AccountSecurity
from app.infrastructure.security.jwt import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def get_current_user(
    request: Request, token: str | None = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    browser_token = request.cookies.get("talentsync_session")
    if browser_token:
        user, session = resolve_session(SqlAlchemyUnitOfWork(db), browser_token,
            csrf=request.headers.get("X-CSRF-Token"), mutation=request.method not in {"GET", "HEAD", "OPTIONS"})
        request.state.account_session = session
        if user.role != UserRole.CANDIDATE and (not user.mfa_enabled or not session.mfa_verified):
            if not request.url.path.startswith(("/api/v1/auth/", "/api/v1/account/")):
                raise HTTPException(status_code=403, detail="Configura la autenticación de dos factores en Seguridad para continuar")
        authorize_request(SqlAlchemyUnitOfWork(db), user, request.url.path, request.method)
        return user
    if not token or settings.session_auth_enabled:
        raise HTTPException(status_code=401, detail="Inicia sesión para continuar")
    payload = decode_access_token(token)
    if payload is None or payload.get("sub") is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido"
        )
    try:
        user = db.get(User, int(payload["sub"]))
    except (ValueError, TypeError):
        raise HTTPException(status_code=401, detail="Token inválido") from None
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no existe"
        )
    authorize_request(SqlAlchemyUnitOfWork(db), user, request.url.path, request.method)
    return user


def get_optional_user(request: Request, token: str | None = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    if token or request.cookies.get("talentsync_session"):
        return get_current_user(request, token, db)
    return None


def require_roles(*roles: UserRole):
    def checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Rol no autorizado"
            )
        return current_user

    return checker


def get_unit_of_work(db: Session = Depends(get_db)) -> UnitOfWork:
    return SqlAlchemyUnitOfWork(db)


def get_text_analysis() -> TextAnalysis:
    return text_processor


def get_interest_trainer():
    from app.infrastructure.nlp.interest_trainer import InterestTrainer
    return InterestTrainer()


def get_account_security() -> AccountSecurityPort:
    return AccountSecurity()


def get_resume_reader() -> ResumeReaderPort:
    return ResumeReader()


def get_jooble_job_catalog():
    from app.core.config import settings

    return JoobleJobCatalog(
        api_key=settings.jooble_api_key,
        base_url=settings.jooble_api_base_url,
        timeout_seconds=settings.jooble_timeout_seconds,
    )


def get_adzuna_job_catalog():
    from app.core.config import settings

    return AdzunaJobCatalog(
        app_id=settings.adzuna_app_id,
        app_key=settings.adzuna_app_key,
        country=settings.adzuna_country,
        base_url=settings.adzuna_api_base_url,
        timeout_seconds=settings.adzuna_timeout_seconds,
    )


def get_jsearch_job_catalog():
    from app.core.config import settings

    return JSearchJobCatalog(
        api_key=settings.jsearch_api_key,
        base_url=settings.jsearch_api_base_url,
        timeout_seconds=settings.jsearch_timeout_seconds,
    )


# Backwards-compatible dependency name used by the existing Jooble routes/tests.
get_job_catalog = get_jooble_job_catalog
