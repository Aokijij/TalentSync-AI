from fastapi import APIRouter, Depends, Request, Response

from app.api.deps import (
    get_account_security,
    get_current_user,
    get_social_identity_provider,
    get_unit_of_work,
    require_roles,
)
from app.api.schemas.account import (
    ActionRequest,
    ChangeEmail,
    EmailRequest,
    MfaCode,
    MfaDisable,
    PasswordRequest,
    PrivacyRequest,
)
from app.api.schemas.auth import LoginRequest, UserResponse
from app.application.errors import UseCaseError
from app.application.use_cases import account_security as cases
from app.core.config import settings
from app.core.limiter import limiter
from app.domain.entities.enums import UserRole

router = APIRouter()
candidate = require_roles(UserRole.CANDIDATE)


def _origin(request):
    origin = request.headers.get("origin")
    if origin and origin not in settings.cors_origins:
        raise UseCaseError(status_code=403, detail="Origen no permitido")


def _cookie_response(request, response, payload, db, security, admin):
    _origin(request)
    if admin and settings.admin_sso_required:
        raise UseCaseError(status_code=403, detail="Utiliza el acceso corporativo obligatorio")
    values = payload.model_dump()
    for portal in ("candidate", "company"):
        if f"/{portal}/login" in request.url.path:
            values["portal"] = portal
    result = cases.create_session(db, values, security, admin=admin,
                                  user_agent=request.headers.get("user-agent", ""))
    if result.get("mfa_required"):
        return result
    set_session_cookies(response, result)
    return {"user": UserResponse.model_validate(result["user"]).model_dump(),
            "mfa_setup_required": result["mfa_setup_required"]}


def set_session_cookies(response, result):
    options = {"secure": settings.session_cookie_secure or settings.environment.casefold() in {"production", "staging"},
               "samesite": "lax", "path": "/"}
    if result["remember"]:
        options["max_age"] = 30 * 86400
    response.set_cookie("talentsync_session", result["token"], httponly=True, **options)
    response.set_cookie("talentsync_csrf", result["csrf"], httponly=False, **options)


@router.get("/auth/options")
def options(gateway=Depends(get_social_identity_provider)):
    return {"mode": "session" if settings.session_auth_enabled else "legacy",
            "local_mail": settings.local_mail_enabled and settings.environment == "development",
            "providers": [{"id": name, "enabled": gateway.configured(name),
                           "reason": "Solo para candidatos" if gateway.configured(name) else "Requiere credenciales y origen HTTPS" if name == "linkedin" else "Requiere configurar credenciales"}
                          for name in ("google", "github", "linkedin")]}


@router.post("/auth/session/login")
@router.post("/auth/session/candidate/login")
@router.post("/auth/session/company/login")
@limiter.limit("30/hour")
def login(request: Request, response: Response, payload: LoginRequest,
          db=Depends(get_unit_of_work), security=Depends(get_account_security)):
    return _cookie_response(request, response, payload, db, security, False)


@router.post("/auth/session/admin/login")
@limiter.limit("15/hour")
def admin_login(request: Request, response: Response, payload: LoginRequest,
                db=Depends(get_unit_of_work), security=Depends(get_account_security)):
    return _cookie_response(request, response, payload, db, security, True)


@router.post("/auth/session/logout")
def logout(request: Request, response: Response, user=Depends(get_current_user), db=Depends(get_unit_of_work)):
    session = getattr(request.state, "account_session", None)
    if session:
        cases.revoke_session(db, user, session.id)
    response.delete_cookie("talentsync_session", path="/")
    response.delete_cookie("talentsync_csrf", path="/")
    return {"message": "Sesión cerrada"}


@router.post("/auth/password/request")
@limiter.limit("5/hour")
def recover(request: Request, payload: EmailRequest, db=Depends(get_unit_of_work)):
    _origin(request)
    return cases.request_action(db, str(payload.email).casefold(), "reset", app_url=settings.public_app_url,
                                mail_enabled=settings.mail_delivery_enabled, delivery_mode=settings.mail_delivery_mode)


@router.post("/auth/action/confirm")
@limiter.limit("20/hour")
def action(request: Request, payload: ActionRequest, db=Depends(get_unit_of_work), security=Depends(get_account_security)):
    _origin(request)
    return cases.complete_action(db, payload.token, payload.purpose, password=payload.password, security=security)


@router.post("/account/verify-email")
@limiter.limit("5/hour")
def verify_email(request: Request, user=Depends(get_current_user), db=Depends(get_unit_of_work)):
    return cases.request_action(db, user.email, "verify", app_url=settings.public_app_url, mail_enabled=settings.mail_delivery_enabled,
                                target_email=user.email, delivery_mode=settings.mail_delivery_mode)


@router.post("/account/change-email")
@limiter.limit("5/hour")
def change_email(request: Request, payload: ChangeEmail, user=Depends(get_current_user),
                 db=Depends(get_unit_of_work), security=Depends(get_account_security)):
    cases._password(user, payload.password, security)
    return cases.request_action(db, user.email, "email", target_email=str(payload.email).casefold(), app_url=settings.public_app_url,
                                mail_enabled=settings.mail_delivery_enabled, delivery_mode=settings.mail_delivery_mode)


@router.get("/account/sessions")
def sessions(request: Request, user=Depends(get_current_user), db=Depends(get_unit_of_work)):
    current = getattr(request.state, "account_session", None)
    return [{"id": row.id, "device": row.user_agent, "created_at": row.created_at, "last_seen_at": row.last_seen_at,
             "expires_at": row.expires_at, "revoked": row.revoked_at is not None, "current": current is not None and current.id == row.id}
            for row in db.accounts.sessions_for_user(user.id)]


@router.delete("/account/sessions/{session_id}")
def revoke(session_id: int, user=Depends(get_current_user), db=Depends(get_unit_of_work)):
    cases.revoke_session(db, user, session_id)
    return {"message": "Sesión revocada"}


@router.get("/account/privacy")
def privacy(user=Depends(candidate), db=Depends(get_unit_of_work)):
    return cases.privacy(db, user)


@router.put("/account/privacy")
def update_privacy(payload: PrivacyRequest, user=Depends(candidate), db=Depends(get_unit_of_work)):
    return cases.privacy(db, user, payload.model_dump())


def _session(request):
    session = getattr(request.state, "account_session", None)
    if session is None:
        raise UseCaseError(status_code=401, detail="Esta operación requiere una sesión del navegador")
    return session


@router.post("/account/mfa/setup")
@limiter.limit("5/hour")
def setup(request: Request, payload: PasswordRequest, user=Depends(get_current_user),
          db=Depends(get_unit_of_work), security=Depends(get_account_security)):
    _session(request)
    return cases.start_mfa(db, user, payload.password, security)


@router.post("/account/mfa/confirm")
@limiter.limit("10/hour")
def confirm(request: Request, payload: MfaCode, user=Depends(get_current_user),
            db=Depends(get_unit_of_work), security=Depends(get_account_security)):
    return cases.confirm_mfa(db, user, _session(request), payload.code, security)


@router.post("/account/mfa/disable")
@limiter.limit("5/hour")
def disable(request: Request, payload: MfaDisable, user=Depends(get_current_user),
            db=Depends(get_unit_of_work), security=Depends(get_account_security)):
    cases.disable_mfa(db, user, _session(request), payload.model_dump(), security)
    return {"message": "Autenticación desactivada"}


@router.get("/dev/mailbox")
def mailbox(request: Request, db=Depends(get_unit_of_work)):
    if (not settings.local_mail_enabled or settings.environment != "development"
            or not settings.database_url.startswith("sqlite")
            or not request.client or request.client.host not in {"127.0.0.1", "::1", "testclient"}):
        raise UseCaseError(status_code=404, detail="No encontrado")
    return [{"id": row.id, "recipient": row.recipient, "subject": row.subject, "body": row.body, "created_at": row.created_at}
            for row in db.accounts.messages()]
