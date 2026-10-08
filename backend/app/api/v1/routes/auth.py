from fastapi import APIRouter, Depends, Request, status

from app.api.deps import (
    get_account_security,
    get_current_user,
    get_text_analysis,
    get_unit_of_work,
)
from app.api.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.application.errors import UseCaseError
from app.application.ports.services import AccountSecurity, TextAnalysis
from app.application.ports.unit_of_work import UnitOfWork
from app.application.use_cases import auth as use_cases
from app.application.use_cases.account_security import request_action
from app.core.config import settings
from app.core.limiter import limiter
from app.domain.entities.records import User

router = APIRouter()


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
@router.post("/candidate/register", response_model=UserResponse, status_code=201)
@router.post("/company/register", response_model=UserResponse, status_code=201)
@limiter.limit("10/hour")
def register(
    request: Request,
    payload: RegisterRequest,
    db: UnitOfWork = Depends(get_unit_of_work),
    *,
    nlp: TextAnalysis = Depends(get_text_analysis),
    security: AccountSecurity = Depends(get_account_security),
) -> User:
    portal = next((role for role in ("candidate", "company") if f"/{role}/register" in request.url.path), None)
    if portal and payload.role.value != portal:
        raise UseCaseError(status_code=422, detail="El rol no corresponde a este formulario de registro")
    if settings.session_auth_enabled and len(payload.password) < 12:
        raise UseCaseError(status_code=422, detail="Usa una contraseña de al menos 12 caracteres")
    user = use_cases.register(
        payload=payload.model_dump(), db=db, nlp=nlp, security=security,
        require_verification=settings.session_auth_enabled,
    )
    if settings.mail_delivery_enabled:
        request_action(db, user.email, "verify", app_url=settings.public_app_url,
                       mail_enabled=True, target_email=user.email, delivery_mode=settings.mail_delivery_mode)
    return user


@router.post("/login", response_model=TokenResponse)
@router.post("/candidate/login", response_model=TokenResponse)
@router.post("/company/login", response_model=TokenResponse)
@limiter.limit("60/hour")
def login(
    request: Request,
    payload: LoginRequest,
    db: UnitOfWork = Depends(get_unit_of_work),
    *,
    security: AccountSecurity = Depends(get_account_security),
) -> TokenResponse:
    if settings.session_auth_enabled:
        raise UseCaseError(status_code=410, detail="Utiliza el acceso con sesión del navegador")
    values = payload.model_dump()
    for portal in ("candidate", "company"):
        if f"/{portal}/login" in request.url.path:
            values["portal"] = portal
    return use_cases.login(payload=values, db=db, security=security)


@router.post("/admin/login", response_model=TokenResponse)
@limiter.limit("30/hour")
def admin_login(
    request: Request,
    payload: LoginRequest,
    db: UnitOfWork = Depends(get_unit_of_work),
    *,
    security: AccountSecurity = Depends(get_account_security),
) -> TokenResponse:
    if settings.session_auth_enabled or settings.admin_sso_required:
        raise UseCaseError(status_code=410, detail="Utiliza el acceso administrativo con sesión o el proveedor corporativo")
    return use_cases.login(
        payload=payload.model_dump(),
        db=db,
        security=security,
        admin_channel=True,
    )


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)) -> User:
    return use_cases.me(current_user=current_user)
