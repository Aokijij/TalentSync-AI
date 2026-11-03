from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel, Field

from app.api.deps import (
    get_account_files,
    get_account_security,
    get_current_user,
    get_unit_of_work,
)
from app.application.use_cases import account_data as cases
from app.core.limiter import limiter

router = APIRouter()


class Credentials(BaseModel):
    password: str = Field(min_length=1, max_length=200)
    code: str | None = Field(default=None, max_length=100)


class EraseRequest(Credentials):
    confirmation: str = Field(max_length=20)


@router.get("/account/data")
def status(user=Depends(get_current_user), db=Depends(get_unit_of_work)):
    return cases.status(db, user)


@router.post("/account/data/export")
@limiter.limit("3/hour")
def export(request: Request, payload: Credentials, user=Depends(get_current_user), db=Depends(get_unit_of_work), security=Depends(get_account_security), files=Depends(get_account_files)):
    content = cases.export(db, user, payload.model_dump(), security, files)
    return Response(content, media_type="application/zip", headers={"Content-Disposition": 'attachment; filename="TalentSync-mis-datos.zip"', "Cache-Control": "no-store"})


@router.post("/account/data/erase")
@limiter.limit("3/hour")
def erase(request: Request, payload: EraseRequest, response: Response, user=Depends(get_current_user), db=Depends(get_unit_of_work), security=Depends(get_account_security), files=Depends(get_account_files)):
    result = cases.erase(db, user, payload.model_dump(), security, files)
    response.delete_cookie("talentsync_session", path="/")
    response.delete_cookie("talentsync_csrf", path="/")
    return result
