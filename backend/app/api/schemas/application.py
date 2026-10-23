from datetime import datetime
from typing import Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, Field, field_validator, model_validator

from app.domain.entities.enums import ApplicationStatus
from app.domain.services.interview_calendar import utc


class ScreeningAnswer(BaseModel):
    question_id: str = Field(min_length=2, max_length=80)
    question: str | None = None
    answer: str = Field(min_length=1, max_length=2000)
    type: Literal["open", "choice"] | None = None
    reviewer_adjustment: float = Field(default=0, ge=-3, le=3)
    configured_adjustment: float = Field(default=0, ge=-5, le=5)


class ApplicationCreate(BaseModel):
    job_id: int
    attach_resume: bool = True
    resume_version_id: str | None = Field(default=None, pattern=r"^[a-f0-9]{32}$")

    @model_validator(mode="before")
    @classmethod
    def reject_retired_preparation(cls, values):
        if isinstance(values, dict) and values.get("coach_draft_id"):
            raise ValueError("Las presentaciones por vacante se retiraron; postúlate con tu perfil habitual")
        return values

    screening_answers: list[ScreeningAnswer] = Field(default_factory=list, max_length=10)


class InterviewDetails(BaseModel):
    mode: Literal["virtual", "in_person"]
    location: str = Field(min_length=3, max_length=1000)
    minutes: int = Field(default=45, ge=15, le=180)
    instructions: str = Field(default="", max_length=2000)

    @field_validator("location", "instructions")
    @classmethod
    def trim_text(cls, value):
        return value.strip()

    @model_validator(mode="after")
    def valid_location(self):
        if len(self.location) < 3:
            raise ValueError("Indica la dirección o el enlace de la entrevista")
        if self.mode == "virtual":
            try:
                url = urlsplit(self.location)
                valid = url.scheme == "https" and url.hostname and not url.username and not url.password and not any(c.isspace() for c in self.location)
            except ValueError:
                valid = False
            if not valid:
                raise ValueError("Indica un enlace HTTPS válido para la entrevista virtual")
        return self


class ApplicationStatusUpdate(BaseModel):
    expected_version: int | None = Field(default=None, ge=1)
    candidate_feedback: "CandidateFeedback | None" = None
    status: ApplicationStatus | None = None
    pipeline_stage: str | None = None
    recruiter_notes: str | None = None
    interview_at: datetime | None = None
    interview_details: InterviewDetails | None = None
    screening_answer_adjustments: dict[str, float] | None = None

    @field_validator("interview_at")
    @classmethod
    def interview_in_utc(cls, value):
        # The database stores naive UTC; normalize offsets before persistence.
        return utc(value).replace(tzinfo=None) if value is not None else None


class CandidateFeedback(BaseModel):
    reason_code: Literal["skills_gap", "experience_gap", "position_closed", "other"]
    message: str = Field(min_length=10, max_length=1500)


ApplicationStatusUpdate.model_rebuild()


class ApplicationResponse(BaseModel):
    resume_version_id: str | None = None
    coach_draft_id: str | None = None
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
    interview_details: dict = Field(default_factory=dict)
    pipeline_stage: str | None = None
    pipeline_stage_title: str | None = None
    resolution_reason: str | None = None

    model_config = {"from_attributes": True}


class CompanyApplicationResponse(ApplicationResponse):
    identity_hidden: bool = False
    recruiter_notes: str | None = None
    screening_answers: list[ScreeningAnswer] = Field(default_factory=list)
    screening_adjustment: float = 0
    base_match_percentage: float | None = None
    adjusted_match_percentage: float | None = None
