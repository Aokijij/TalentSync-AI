from datetime import datetime

from pydantic import BaseModel


class RecommendationResponse(BaseModel):
    id: int
    user_id: int
    job_id: int
    match_percentage: float
    skill_match_percentage: float = 0
    semantic_match_percentage: float = 0
    reasons: list[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class RankedCandidate(BaseModel):
    user_id: int
    name: str
    profession: str | None
    match_percentage: float
    skills: list[str]
    experience_years: float | None = None
    experience_summary: str | None = None
    has_applied: bool = False
