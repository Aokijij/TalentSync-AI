from fastapi import APIRouter, Depends

from app.api.deps import (
    get_account_security,
    get_repository_inspector,
    get_text_analysis,
    get_unit_of_work,
    require_roles,
)
from app.api.schemas.matching import (
    CandidatePreferences,
    EvidenceSubmission,
    ProjectEvidenceSubmission,
    RepositoryPreviewRequest,
)
from app.application.use_cases import match_settings as cases
from app.application.use_cases import project_evidence
from app.core.config import settings
from app.domain.entities.enums import UserRole

router = APIRouter()
candidate = require_roles(UserRole.CANDIDATE)


@router.get("/integrations/github/capabilities")
def project_capabilities(user=Depends(candidate)):
    return {"github_public": settings.github_project_analysis_enabled}


@router.post("/integrations/github/preview")
def github_preview(payload: RepositoryPreviewRequest, user=Depends(candidate), inspector=Depends(get_repository_inspector), security=Depends(get_account_security)):
    return project_evidence.preview(user, payload.url, inspector, security)


@router.post("/integrations/github/evidence")
def save_project(payload: ProjectEvidenceSubmission, user=Depends(candidate), db=Depends(get_unit_of_work), security=Depends(get_account_security)):
    return project_evidence.save(db, user, payload.model_dump(mode="json"), security)


@router.get("/matching/preferences")
def preferences(user=Depends(candidate), db=Depends(get_unit_of_work)):
    return cases.preferences(db, user)


@router.put("/matching/preferences")
def save_preferences(payload: CandidatePreferences, user=Depends(candidate), db=Depends(get_unit_of_work)):
    return cases.preferences(db, user, payload.model_dump(exclude_unset=True))


@router.get("/matching/evidence")
def evidence(user=Depends(candidate), db=Depends(get_unit_of_work)):
    return cases.evidence(db, user)


@router.post("/matching/evidence")
def add_evidence(payload: EvidenceSubmission, user=Depends(candidate), db=Depends(get_unit_of_work)):
    return cases.evidence(db, user, payload.model_dump(mode="json"))


@router.delete("/matching/evidence/{evidence_id}", status_code=204)
def remove_evidence(evidence_id: str, user=Depends(candidate), db=Depends(get_unit_of_work)):
    cases.remove_evidence(db, user, evidence_id)


@router.get("/matching/jobs/{job_id}")
def explanation(job_id: int, user=Depends(candidate), db=Depends(get_unit_of_work), nlp=Depends(get_text_analysis)):
    return cases.match_details(db, user, job_id, nlp)
