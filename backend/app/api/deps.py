from functools import lru_cache

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.application.ports.services import AccountSecurity as AccountSecurityPort
from app.application.ports.services import ProjectInspector as ProjectInspectorPort
from app.application.ports.services import ResumeReader as ResumeReaderPort
from app.application.ports.services import TextAnalysis
from app.application.ports.unit_of_work import UnitOfWork
from app.application.use_cases.account_security import resolve_session, revoke_session
from app.application.use_cases.organizations import authorize_request
from app.core.config import settings
from app.domain.entities.enums import UserRole
from app.domain.services.access_policy import requires_mfa_setup
from app.domain.services.corporate_identity import PROVIDERS, authority_fingerprint
from app.infrastructure.database.models import User
from app.infrastructure.database.session import get_db
from app.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork
from app.infrastructure.images import get_image_storage as get_image_storage
from app.infrastructure.job_catalogs import (
    AdzunaJobCatalog,
    JoobleJobCatalog,
    JSearchJobCatalog,
)
from app.infrastructure.matching_gate import matching_slot
from app.infrastructure.nlp.resumes import ResumeReader
from app.infrastructure.nlp.text_processor import text_processor
from app.infrastructure.security.accounts import AccountSecurity
from app.infrastructure.security.jwt import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


@lru_cache
def get_career_writer():
    from app.infrastructure.nlp.career_writer import LocalCareerWriter
    if not settings.career_writer_model or not settings.career_writer_executable:
        return None
    return LocalCareerWriter(settings.career_writer_model, settings.career_writer_executable, settings.career_writer_timeout_seconds)


@lru_cache
def get_youtube_learning():
    from app.infrastructure.youtube_learning import YouTubeLearning
    return YouTubeLearning(settings)


@lru_cache
def get_learn_catalog():
    from app.infrastructure.learn_catalog import LearnCatalog
    return LearnCatalog(settings)


def get_curated_catalog():
    from app.infrastructure import curated_learning
    return curated_learning


@lru_cache
def get_public_learning_catalog():
    from app.infrastructure.public_learning import PublicLearningCatalog
    return PublicLearningCatalog()


def get_current_user(
    request: Request, token: str | None = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    browser_token = request.cookies.get("talentsync_session")
    if browser_token:
        user, session = resolve_session(SqlAlchemyUnitOfWork(db), browser_token,
            csrf=request.headers.get("X-CSRF-Token"), mutation=request.method not in {"GET", "HEAD", "OPTIONS"})
        request.state.account_session = session
        if user.role == UserRole.ADMIN:
            corporate = get_corporate_configuration()
            if session.authentication_method in PROVIDERS:
                if session.authentication_method != corporate["provider"] or session.authentication_authority != corporate["authority"]:
                    revoke_session(SqlAlchemyUnitOfWork(db), user, session.id)
                    raise HTTPException(status_code=401, detail="El proveedor corporativo cambió; inicia sesión de nuevo")
            elif settings.admin_sso_required:
                raise HTTPException(status_code=401, detail="Inicia una sesión mediante el proveedor corporativo")
        admin_review = settings.mfa_review_active or user.role == UserRole.ADMIN and not settings.admin_mfa_required
        access_notice = user.role == UserRole.COMPANY and (
            (request.method == "GET" and request.url.path == "/api/v1/organization/access")
            or (request.method == "POST" and request.url.path == "/api/v1/organization/access-review")
        )
        if not admin_review and ((requires_mfa_setup(user.role, settings.company_mfa_required) and not user.mfa_enabled) or (user.mfa_enabled and not session.mfa_verified)):
            if not access_notice and not request.url.path.startswith(("/api/v1/auth/", "/api/v1/account/")):
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
    if user.role == UserRole.ADMIN and settings.admin_sso_required:
        raise HTTPException(status_code=401, detail="Se requiere una sesión corporativa")
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


def get_corporate_configuration():
    provider = settings.admin_sso_provider
    boundary = settings.entra_tenant_id if provider == "entra" else settings.workspace_domain
    client_id = settings.oauth_entra_client_id if provider == "entra" else settings.oauth_workspace_client_id
    return {"provider": provider, "domain": boundary, "authority": authority_fingerprint(provider, boundary, client_id)}


def get_text_analysis() -> TextAnalysis:
    return text_processor


def get_matching_gate():
    return matching_slot


def get_interest_trainer():
    from app.infrastructure.nlp.interest_trainer import InterestTrainer
    return InterestTrainer()


def get_account_security() -> AccountSecurityPort:
    return AccountSecurity()


def get_social_identity_provider():
    from app.infrastructure.security.social import SocialIdentityProvider
    return SocialIdentityProvider(settings)


def get_resume_reader() -> ResumeReaderPort:
    return ResumeReader()


def get_project_inspector() -> ProjectInspectorPort:
    from app.infrastructure.project_inspector import ProjectInspector
    return ProjectInspector()


@lru_cache
def get_repository_inspector():
    from app.infrastructure.github_projects import GitHubProjectInspector
    return GitHubProjectInspector(settings)


@lru_cache
def get_codewars_reader():
    from app.infrastructure.codewars import CodewarsReader
    return CodewarsReader(settings)


def get_sql_sandbox():
    from app.infrastructure.sql_sandbox import SQLSandbox
    return SQLSandbox()


def get_interview_ice():
    from app.infrastructure.interview_ice import InterviewIce
    return InterviewIce(settings)


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


def get_resume_exporter():
    from app.infrastructure.resume_pdf import resume_pdf
    def export(user, **options):
        filename = getattr(user.profile, "photo_filename", None)
        photo = get_image_storage().read("profile_photos", filename) if filename and options.get("include_photo", True) else None
        return resume_pdf(user, photo=photo, **options)
    return export


def get_resume_previews():
    from app.infrastructure.resume_previews import resume_previews
    return resume_previews
