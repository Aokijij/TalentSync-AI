from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.api.deps import (
    get_interest_trainer,
    get_social_identity_provider,
    get_text_analysis,
    get_unit_of_work,
    require_roles,
)
from app.application.use_cases import personalization as cases
from app.core.config import settings
from app.domain.entities.enums import UserRole
from app.domain.services.integration_readiness import integration_readiness

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
def status(user=Depends(admin), db=Depends(get_unit_of_work), nlp=Depends(get_text_analysis), gateway=Depends(get_social_identity_provider)):
    result = cases.model_status(db, nlp)
    result["integrations"] = integration_readiness(
        neural_active=getattr(nlp, "match_method", "").startswith("local-sentence-transformer:"),
        local_mail=settings.local_mail_enabled, smtp=settings.smtp_enabled,
        providers={key: gateway.configured(key) for key in ("google", "github", "linkedin", "workspace", "entra")},
        catalog=bool(settings.jsearch_api_key or settings.jooble_api_key or settings.adzuna_app_id and settings.adzuna_app_key))
    result["mfa_review_active"] = settings.mfa_review_active
    return result


@router.post("/admin/models/train")
def train(user=Depends(admin), db=Depends(get_unit_of_work), nlp=Depends(get_text_analysis), trainer=Depends(get_interest_trainer)):
    return cases.train(db, nlp, trainer, user=user)
