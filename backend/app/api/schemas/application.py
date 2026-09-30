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


class ApplicationCreate(BaseModel):
    job_id: int
    screening_answers: list[ScreeningAnswer] = Field(default_factory=list, max_length=10)


class ApplicationStatusUpdate(BaseModel):
    status: ApplicationStatus | None = None
    pipeline_stage: str | None = None
    recruiter_notes: str | None = None
    interview_at: datetime | None = None
    screening_answer_adjustments: dict[str, float] | None = None


class ApplicationResponse(BaseModel):
    id: int
    user_id: int
    job_id: int
    status: ApplicationStatus
    created_at: datetime
    job_title: str | None = None
    company_name: str | None = None
    candidate_name: str | None = None
    recruiter_notes: str | None = None
    interview_at: datetime | None = None
    pipeline_stage: str | None = None
    pipeline_stage_title: str | None = None
    resolution_reason: str | None = None

    model_config = {"from_attributes": True}


class CompanyApplicationResponse(ApplicationResponse):
    screening_answers: list[ScreeningAnswer] = Field(default_factory=list)
    screening_adjustment: float = 0
    base_match_percentage: float | None = None
    adjusted_match_percentage: float | None = None
