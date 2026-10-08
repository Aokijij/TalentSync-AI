from fastapi import APIRouter, Depends, Query, Request, Response
from fastapi.responses import RedirectResponse

from app.api.deps import (
    get_account_security,
    get_corporate_configuration,
    get_social_identity_provider,
    get_unit_of_work,
)
from app.api.schemas.account import MfaCode
from app.api.v1.routes.account import _origin, set_session_cookies
from app.api.v1.routes.social_access import _temporary_cookie
from app.application.errors import UseCaseError
from app.application.use_cases import admin_sso as cases
from app.core.config import settings
from app.core.limiter import limiter

router = APIRouter()


@router.get("/auth/admin-sso/options")
def options(gateway=Depends(get_social_identity_provider)):
    provider = settings.admin_sso_provider
    return {"enabled": gateway.configured(provider), "required": settings.admin_sso_required,
            "provider": "Microsoft Entra ID" if provider == "entra" else "Google Workspace"}


@router.post("/auth/admin-sso/start")
@limiter.limit("10/hour")
def start(request: Request, response: Response, db=Depends(get_unit_of_work),
          gateway=Depends(get_social_identity_provider), security=Depends(get_account_security)):
    _origin(request)
    corporate = get_corporate_configuration()
    result = cases.begin(db, gateway, security, provider=corporate["provider"], authority=corporate["authority"])
    _temporary_cookie(response, "talentsync_admin_sso_browser", result["browser"], 600)
    return {"url": result["url"]}


@router.get("/auth/admin-sso/callback")
@limiter.limit("20/hour")
def callback(request: Request, state: str = Query(default="", max_length=256), code: str = Query(default="", max_length=4096),
             db=Depends(get_unit_of_work), gateway=Depends(get_social_identity_provider), security=Depends(get_account_security)):
    result = None
    try:
        result = cases.callback(db, state, request.cookies.get("talentsync_admin_sso_browser"), code, gateway, security,
                                user_agent=request.headers.get("user-agent", ""), **get_corporate_configuration())
        destination = "/acceso-corporativo?status=mfa" if result.get("mfa_required") else "/seguridad" if result["mfa_setup_required"] else "/admin"
    except UseCaseError as error:
        destination = "/acceso-corporativo?status=unavailable" if error.status_code == 503 else "/acceso-corporativo?status=failed"
    response = RedirectResponse(f"{settings.public_app_url.rstrip('/')}{destination}", status_code=303)
    response.delete_cookie("talentsync_admin_sso_browser", path="/")
    response.headers["Cache-Control"] = "no-store"
    response.headers["Referrer-Policy"] = "no-referrer"
    if result:
        if result.get("mfa_required"):
            _temporary_cookie(response, "talentsync_admin_sso_mfa", result["pending"], 300)
            response.delete_cookie("talentsync_session", path="/")
            response.delete_cookie("talentsync_csrf", path="/")
        else:
            response.delete_cookie("talentsync_admin_sso_mfa", path="/")
            set_session_cookies(response, result)
    return response


@router.post("/auth/admin-sso/complete")
@limiter.limit("10/hour")
def complete(request: Request, response: Response, payload: MfaCode, db=Depends(get_unit_of_work),
             gateway=Depends(get_social_identity_provider), security=Depends(get_account_security)):
    _origin(request)
    if not gateway.configured(settings.admin_sso_provider):
        raise UseCaseError(status_code=503, detail="El acceso corporativo no está configurado")
    result = cases.complete(db, request.cookies.get("talentsync_admin_sso_mfa"), payload.code, security,
                            user_agent=request.headers.get("user-agent", ""), **get_corporate_configuration())
    set_session_cookies(response, result)
    response.delete_cookie("talentsync_admin_sso_mfa", path="/")
    response.headers["Cache-Control"] = "no-store"
    return {"message": "Acceso administrativo completado"}
