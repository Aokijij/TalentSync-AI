from fastapi import APIRouter, Depends, Query, Request, Response
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field

from app.api.deps import (
    get_account_security,
    get_calendar_gateway,
    get_current_user,
    get_unit_of_work,
)
from app.api.v1.routes.account import _session
from app.api.v1.routes.social_access import _temporary_cookie
from app.application.errors import UseCaseError
from app.application.use_cases import calendars as cases
from app.core.config import settings
from app.core.limiter import limiter

router = APIRouter()



@router.get("/account/calendar")
def status(user=Depends(get_current_user), db=Depends(get_unit_of_work), gateway=Depends(get_calendar_gateway)):
    return cases.status(db, user, gateway)


@router.post("/account/calendar/google/connect")
@limiter.limit("10/hour")
def connect(request: Request, response: Response, user=Depends(get_current_user), db=Depends(get_unit_of_work), gateway=Depends(get_calendar_gateway), security=Depends(get_account_security)):
    result = cases.begin(db, user, _session(request), gateway, security)
    _temporary_cookie(response, "talentsync_calendar_browser", result["browser"], 600)
    return {"url": result["url"]}


@router.get("/account/calendar/google/callback")
@limiter.limit("20/hour")
def callback(request: Request, state: str = Query(default="", max_length=200), code: str = Query(default="", max_length=4000), user=Depends(get_current_user), db=Depends(get_unit_of_work), gateway=Depends(get_calendar_gateway), security=Depends(get_account_security)):
    result = "connected"
    try:
        cases.callback(db, user, _session(request), state, request.cookies.get("talentsync_calendar_browser"), code, gateway, security)
    except UseCaseError:
        result = "not_connected"
    response = RedirectResponse(f"{settings.public_app_url.rstrip('/')}/seguridad?calendar={result}#security-calendar", status_code=303)
    response.delete_cookie("talentsync_calendar_browser", path="/")
    response.headers.update({"Cache-Control": "no-store", "Referrer-Policy": "no-referrer"})
    return response


@router.delete("/account/calendar")
def disconnect(user=Depends(get_current_user), db=Depends(get_unit_of_work)):
    return cases.disconnect(db, user)


class SyncRequest(BaseModel):
    minutes: int = Field(default=45, ge=15, le=180)


@router.get("/workflow/applications/{application_id}/calendar")
def event_status(application_id: int, user=Depends(get_current_user), db=Depends(get_unit_of_work)):
    return cases.event_status(db, user, application_id)


@router.post("/workflow/applications/{application_id}/calendar")
@limiter.limit("30/hour")
def synchronize(request: Request, application_id: int, payload: SyncRequest, user=Depends(get_current_user), db=Depends(get_unit_of_work), gateway=Depends(get_calendar_gateway), security=Depends(get_account_security)):
    return cases.synchronize(db, user, application_id, payload.minutes, gateway, security, settings.public_app_url)
