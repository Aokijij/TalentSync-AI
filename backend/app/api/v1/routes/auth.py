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
from app.application.ports.services import AccountSecurity, TextAnalysis
from app.application.ports.unit_of_work import UnitOfWork
from app.application.use_cases import auth as use_cases
from app.core.limiter import limiter
from app.domain.entities.records import User

router = APIRouter()


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
@limiter.limit("10/hour")
def register(
    request: Request,
    payload: RegisterRequest,
    db: UnitOfWork = Depends(get_unit_of_work),
    *,
    nlp: TextAnalysis = Depends(get_text_analysis),
    security: AccountSecurity = Depends(get_account_security),
) -> User:
    return use_cases.register(
        payload=payload.model_dump(), db=db, nlp=nlp, security=security
    )


@router.post("/login", response_model=TokenResponse)
@limiter.limit("60/hour")
def login(
    request: Request,
    payload: LoginRequest,
    db: UnitOfWork = Depends(get_unit_of_work),
    *,
    security: AccountSecurity = Depends(get_account_security),
) -> TokenResponse:
    return use_cases.login(payload=payload.model_dump(), db=db, security=security)


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)) -> User:
    return use_cases.me(current_user=current_user)
