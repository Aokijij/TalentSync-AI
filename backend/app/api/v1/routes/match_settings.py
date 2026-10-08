from fastapi import APIRouter, Depends

from app.api.deps import get_text_analysis, get_unit_of_work, require_roles
from app.api.schemas.matching import CandidatePreferences, EvidenceSubmission
from app.application.use_cases import match_settings as cases
from app.domain.entities.enums import UserRole

router = APIRouter()
candidate = require_roles(UserRole.CANDIDATE)


@router.get("/matching/preferences")
def preferences(user=Depends(candidate), db=Depends(get_unit_of_work)):
    return cases.preferences(db, user)


@router.put("/matching/preferences")
def save_preferences(payload: CandidatePreferences, user=Depends(candidate), db=Depends(get_unit_of_work)):
    return cases.preferences(db, user, payload.model_dump())


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
