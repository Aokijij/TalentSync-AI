from fastapi import APIRouter, Depends, Query, Request, Response
from fastapi.responses import RedirectResponse

from app.api.deps import (
    get_account_security,
    get_social_identity_provider,
    get_unit_of_work,
    require_roles,
)
from app.api.schemas.account import MfaCode, SocialAccountRequest
from app.api.v1.routes.account import _origin, _session, set_session_cookies
from app.application.errors import UseCaseError
from app.application.use_cases import social_access as cases
from app.core.config import settings
from app.core.limiter import limiter
from app.domain.entities.enums import UserRole

router = APIRouter()
candidate = require_roles(UserRole.CANDIDATE)


def _temporary_cookie(response, name, value, seconds):
    response.set_cookie(name, value, max_age=seconds, httponly=True, samesite="lax", path="/",
        secure=settings.session_cookie_secure or settings.environment.casefold() in {"production", "staging"})
    response.headers["Cache-Control"] = "no-store"


@router.post("/auth/social/{provider}/start")
@limiter.limit("20/hour")
def start(request: Request, response: Response, provider: str,
          db=Depends(get_unit_of_work), gateway=Depends(get_social_identity_provider), security=Depends(get_account_security)):
    _origin(request)
    result = cases.begin(db, provider, gateway, security)
    _temporary_cookie(response, "talentsync_oauth_browser", result["browser"], 600)
    return {"url": result["url"]}


@router.get("/auth/social/{provider}/callback")
@limiter.limit("30/hour")
def callback(request: Request, provider: str, state: str = Query(default="", max_length=256),
             code: str = Query(default="", max_length=4096),
             db=Depends(get_unit_of_work), gateway=Depends(get_social_identity_provider), security=Depends(get_account_security)):
    result = None
    try:
        result = cases.callback(db, provider, state, request.cookies.get("talentsync_oauth_browser"), code,
                                gateway, security, user_agent=request.headers.get("user-agent", ""),
                                session_token=request.cookies.get("talentsync_session"))
        status = "linked" if result.get("linked") else "mfa" if result.get("mfa_required") else "new" if result["created"] else "ok"
    except UseCaseError as error:
        status = "existing" if error.status_code == 409 else "unavailable" if error.status_code == 503 else "failed"
    destination = "/seguridad?social=linked" if status == "linked" else "/bienvenida" if status == "new" else "/candidato" if status == "ok" else f"/acceso-social?status={status}"
    response = RedirectResponse(f"{settings.public_app_url.rstrip('/')}{destination}", status_code=303)
    response.delete_cookie("talentsync_oauth_browser", path="/")
    response.headers["Cache-Control"] = "no-store"
    response.headers["Referrer-Policy"] = "no-referrer"
    if result and not result.get("linked"):
        if result.get("mfa_required"):
            _temporary_cookie(response, "talentsync_social_mfa", result["pending"], 300)
            # An earlier session must never masquerade as the pending user's session.
            response.delete_cookie("talentsync_session", path="/")
            response.delete_cookie("talentsync_csrf", path="/")
        else:
            response.delete_cookie("talentsync_social_mfa", path="/")
            set_session_cookies(response, result)
    return response


@router.get("/account/social-identities")
def identities(user=Depends(candidate), db=Depends(get_unit_of_work)):
    return cases.identities(db, user)


@router.post("/account/social-identities/{provider}/link")
@limiter.limit("10/hour")
def link(request: Request, response: Response, provider: str, payload: SocialAccountRequest,
         user=Depends(candidate), db=Depends(get_unit_of_work), gateway=Depends(get_social_identity_provider),
         security=Depends(get_account_security)):
    _origin(request)
    result = cases.begin(db, provider, gateway, security, user=user, session=_session(request), credentials=payload.model_dump())
    _temporary_cookie(response, "talentsync_oauth_browser", result["browser"], 600)
    return {"url": result["url"]}


@router.delete("/account/social-identities/{provider}")
@limiter.limit("10/hour")
def unlink(request: Request, provider: str, payload: SocialAccountRequest,
           user=Depends(candidate), db=Depends(get_unit_of_work), security=Depends(get_account_security)):
    _origin(request)
    return cases.unlink(db, user, _session(request), provider, payload.model_dump(), security)


@router.post("/auth/social/complete")
@limiter.limit("10/hour")
def complete(request: Request, response: Response, payload: MfaCode,
             db=Depends(get_unit_of_work), security=Depends(get_account_security)):
    _origin(request)
    result = cases.complete_mfa(db, request.cookies.get("talentsync_social_mfa"), payload.code, security,
                                user_agent=request.headers.get("user-agent", ""))
    set_session_cookies(response, result)
    response.delete_cookie("talentsync_social_mfa", path="/")
    response.headers["Cache-Control"] = "no-store"
    return {"message": "Acceso completado"}
