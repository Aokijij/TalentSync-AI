from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.api.deps import (
    get_interest_trainer,
    get_text_analysis,
    get_unit_of_work,
    require_roles,
)
from app.application.use_cases import personalization as cases
from app.domain.entities.enums import UserRole

router = APIRouter()
candidate = require_roles(UserRole.CANDIDATE)
admin = require_roles(UserRole.ADMIN)


class Feedback(BaseModel):
    job_id: int = Field(gt=0)
    interested: bool


@router.get("/personalization/feedback")
def own(user=Depends(candidate), db=Depends(get_unit_of_work)):
    return cases.own(db, user)


@router.put("/personalization/feedback")
def feedback(payload: Feedback, user=Depends(candidate), db=Depends(get_unit_of_work), nlp=Depends(get_text_analysis)):
    return cases.feedback(db, user, payload.job_id, payload.interested, nlp)


@router.delete("/personalization/feedback/{job_id}")
def remove(job_id: int, user=Depends(candidate), db=Depends(get_unit_of_work)):
    return cases.remove(db, user, job_id)


@router.get("/admin/models")
def status(user=Depends(admin), db=Depends(get_unit_of_work), nlp=Depends(get_text_analysis)):
    return cases.model_status(db, nlp)


@router.post("/admin/models/train")
def train(user=Depends(admin), db=Depends(get_unit_of_work), nlp=Depends(get_text_analysis), trainer=Depends(get_interest_trainer)):
    return cases.train(db, nlp, trainer, user=user)
