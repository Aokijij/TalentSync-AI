from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.api.deps import (
    get_calendar_gateway,
    get_interest_trainer,
    get_social_identity_provider,
    get_text_analysis,
    get_unit_of_work,
    get_writing_service,
    require_roles,
)
from app.application.use_cases import personalization as cases
from app.application.use_cases.integration_observations import (
    health_observations,
    observations,
)
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
def status(user=Depends(admin), db=Depends(get_unit_of_work), nlp=Depends(get_text_analysis), gateway=Depends(get_social_identity_provider), calendar=Depends(get_calendar_gateway), writing_service=Depends(get_writing_service)):
    result = cases.model_status(db, nlp)
    result["integrations"] = integration_readiness(
        neural_active=getattr(nlp, "match_method", "").startswith("local-sentence-transformer:"),
        writing_service=writing_service,
        local_mail=settings.local_mail_enabled, smtp=settings.smtp_enabled, gmail=settings.gmail_mail_enabled,
        calendar=calendar.configured, mail_events=bool(settings.resend_enabled and settings.resend_webhook_secret),
        resend=settings.resend_enabled, learn=bool(settings.learn_enabled and settings.learn_tenant_id and settings.learn_client_id and settings.learn_client_secret), github_projects=settings.github_project_analysis_enabled,
        youtube=bool(settings.youtube_learning_enabled and settings.youtube_api_key), public_learning=settings.public_learning_refresh_enabled, observations=observations(db), health_reports=health_observations(db),
        codewars=settings.codewars_enabled,
        catalog_providers={"jsearch": bool(settings.jsearch_api_key), "adzuna": bool(settings.adzuna_app_id and settings.adzuna_app_key), "jooble": bool(settings.jooble_api_key), "greenhouse": True, "lever": True, "ashby": True, "getonboard": True},
        providers={key: gateway.configured(key) for key in ("google", "github", "linkedin", "workspace", "entra")},
        catalog=bool(settings.jsearch_api_key or settings.jooble_api_key or settings.adzuna_app_id and settings.adzuna_app_key))
    result["mfa_review_active"] = settings.mfa_review_active
    return result


@router.post("/admin/models/train")
def train(user=Depends(admin), db=Depends(get_unit_of_work), nlp=Depends(get_text_analysis), trainer=Depends(get_interest_trainer)):
    return cases.train(db, nlp, trainer, user=user)
