from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.domain.entities.enums import ApplicationStatus


class ScreeningAnswer(BaseModel):
    question_id: str = Field(min_length=2, max_length=80)
    question: str | None = None
    answer: str = Field(min_length=1, max_length=2000)
    type: Literal["open", "choice"] | None = None
    reviewer_adjustment: float = Field(default=0, ge=-3, le=3)
    configured_adjustment: float = Field(default=0, ge=-5, le=5)


class ApplicationCreate(BaseModel):
    job_id: int
    screening_answers: list[ScreeningAnswer] = Field(default_factory=list, max_length=10)


class ApplicationStatusUpdate(BaseModel):
    expected_version: int | None = Field(default=None, ge=1)
    candidate_feedback: "CandidateFeedback | None" = None
    status: ApplicationStatus | None = None
    pipeline_stage: str | None = None
    recruiter_notes: str | None = None
    interview_at: datetime | None = None
    screening_answer_adjustments: dict[str, float] | None = None


class CandidateFeedback(BaseModel):
    reason_code: Literal["skills_gap", "experience_gap", "position_closed", "other"]
    message: str = Field(min_length=10, max_length=1500)


ApplicationStatusUpdate.model_rebuild()


class ApplicationResponse(BaseModel):
    version: int = 1
    response_due_at: datetime | None = None
    released_at: datetime | None = None
    candidate_feedback: dict = Field(default_factory=dict)
    id: int
    user_id: int
    job_id: int
    status: ApplicationStatus
    created_at: datetime
    job_title: str | None = None
    company_name: str | None = None
    candidate_name: str | None = None
    interview_at: datetime | None = None
    pipeline_stage: str | None = None
    pipeline_stage_title: str | None = None
    resolution_reason: str | None = None

    model_config = {"from_attributes": True}


class CompanyApplicationResponse(ApplicationResponse):
    recruiter_notes: str | None = None
    screening_answers: list[ScreeningAnswer] = Field(default_factory=list)
    screening_adjustment: float = 0
    base_match_percentage: float | None = None
    adjusted_match_percentage: float | None = None
