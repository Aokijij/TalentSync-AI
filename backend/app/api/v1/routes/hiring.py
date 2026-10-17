from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from app.api.deps import get_text_analysis, get_unit_of_work, require_roles
from app.api.schemas.job import QualityPreview
from app.api.schemas.job_quality import OfferFeedbackInput
from app.application.use_cases import hiring as cases
from app.domain.entities.enums import UserRole
from app.domain.services.offer_skills import infer_offer_skills
from app.domain.services.skills import normalize_skills

router = APIRouter()


@router.get("/hiring/education/catalog")
def education_catalog(query: str = Query(default="", max_length=120), user=Depends(require_roles(UserRole.COMPANY, UserRole.ADMIN))):
    from app.domain.services.academic_fields import academic_name, catalog
    data = catalog()
    terms = academic_name(query).split()
    rows = [row for row in data["programs"] if all(term in academic_name(" ".join([row["label"], *row["aliases"]])) for term in terms)]
    return {"version": data["version"], "scope": data["scope"], "classification": data["classification"], "items": [{"label": row["label"], "aliases": row["aliases"]} for row in rows[:100]]}


class SkillSearchInput(BaseModel):
    text: str = Field(min_length=3, max_length=20000)


@router.post("/hiring/skills/search")
def search_skills(payload: SkillSearchInput, user=Depends(require_roles(UserRole.COMPANY, UserRole.ADMIN)), nlp=Depends(get_text_analysis)):
    skills = normalize_skills(nlp.extract_skills(payload.text))[:100]
    return {"skills": skills, "requirements": infer_offer_skills(payload.text, skills)}


@router.get("/hiring/quality/{job_id}")
def quality(job_id: int, user=Depends(require_roles(UserRole.COMPANY, UserRole.ADMIN)), db=Depends(get_unit_of_work)):
    return cases.quality(db, user, job_id)


@router.post("/hiring/quality/preview")
def preview(payload: QualityPreview, user=Depends(require_roles(UserRole.COMPANY, UserRole.ADMIN)), db=Depends(get_unit_of_work)):
    return cases.preview(db, user, payload.model_dump())


@router.post("/hiring/quality/writing")
def writing(payload: QualityPreview, user=Depends(require_roles(UserRole.COMPANY, UserRole.ADMIN)), db=Depends(get_unit_of_work)):
    return cases.writing(db, user, payload.model_dump())


@router.get("/hiring/feedback/{job_id}")
def own_feedback(job_id: int, user=Depends(require_roles(UserRole.CANDIDATE)), db=Depends(get_unit_of_work)):
    return cases.candidate_feedback(db, user, job_id)


@router.put("/hiring/feedback/{job_id}")
def feedback(job_id: int, payload: OfferFeedbackInput, user=Depends(require_roles(UserRole.CANDIDATE)), db=Depends(get_unit_of_work)):
    return cases.candidate_feedback(db, user, job_id, payload.reason)


@router.delete("/hiring/feedback/{job_id}")
def delete_feedback(job_id: int, user=Depends(require_roles(UserRole.CANDIDATE)), db=Depends(get_unit_of_work)):
    return cases.candidate_feedback(db, user, job_id, remove=True)
