from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class JobMission(BaseModel):
    model_config = ConfigDict(extra="forbid")
    outcome: str = Field(default="", max_length=500)
    measure: str = Field(default="", max_length=300)
    days: int = Field(default=90, ge=1, le=365)
    skill: str = Field(default="", max_length=100)


class QualityDetails(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: Literal[1] = 1
    salary_max: float | None = Field(default=None, ge=0, le=1_000_000_000, allow_inf_nan=False)
    variable_pay: str = Field(default="", max_length=500)
    contract_type: Literal["", "indefinite", "fixed_term", "services", "apprenticeship", "project"] = ""
    schedule: str = Field(default="", max_length=300)
    seniority: Literal["", "entry", "junior", "mid", "senior", "lead"] = ""
    experience_years: int | None = Field(default=None, ge=0, le=50)
    learnable_skills: list[str] = Field(default_factory=list, max_length=20)
    missions: list[JobMission] = Field(default_factory=list, max_length=5)
    interview_count: int | None = Field(default=None, ge=0, le=10)
    process_days: int | None = Field(default=None, ge=1, le=180)


FeedbackReason = Literal["salary", "requirements", "unclear", "modality", "process", "other"]


class OfferFeedbackInput(BaseModel):
    reason: FeedbackReason
