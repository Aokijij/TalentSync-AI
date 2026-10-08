from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from app.api.deps import get_sql_sandbox, get_unit_of_work, require_roles
from app.application.use_cases import sql_practice as cases
from app.core.limiter import limiter
from app.domain.entities.enums import UserRole
from app.domain.services.sql_challenges import catalog

router = APIRouter()
candidate = require_roles(UserRole.CANDIDATE)


class SQLQuery(BaseModel):
    query: str = Field(min_length=1, max_length=4000)


@router.get("/learning/practical")
def challenges(user=Depends(candidate)):
    return catalog()


@router.post("/learning/practical/{challenge_id}/start")
@limiter.limit("10/hour")
def start(request: Request, challenge_id: str, user=Depends(candidate), db=Depends(get_unit_of_work)):
    return cases.start(db, user, challenge_id)


@router.post("/learning/practical/attempts/{attempt_id}/preview")
@limiter.limit("20/minute")
def preview(request: Request, attempt_id: str, payload: SQLQuery, user=Depends(candidate), db=Depends(get_unit_of_work), sandbox=Depends(get_sql_sandbox)):
    return cases.preview(db, user, attempt_id, payload.query, sandbox)


@router.post("/learning/practical/attempts/{attempt_id}/submit")
@limiter.limit("10/hour")
def submit(request: Request, attempt_id: str, payload: SQLQuery, user=Depends(candidate), db=Depends(get_unit_of_work), sandbox=Depends(get_sql_sandbox)):
    return cases.submit(db, user, attempt_id, payload.query, sandbox)
