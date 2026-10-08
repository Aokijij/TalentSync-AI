from typing import Literal

from pydantic import BaseModel, EmailStr, Field, HttpUrl


class VerificationSubmission(BaseModel):
    legal_name: str = Field(min_length=3, max_length=180)
    website: HttpUrl | None = None
    registry_reference: str = Field(min_length=5, max_length=300)
    representative_role: str = Field(min_length=3, max_length=120)
    notes: str = Field(default="", max_length=1500)


class VerificationReview(BaseModel):
    status: Literal["verified", "information_required", "rejected", "suspended"]
    feedback: str = Field(min_length=10, max_length=1500)


class TeamInvitation(BaseModel):
    email: EmailStr
    role: Literal["recruiter", "interviewer"]
    assigned_job_ids: list[int] = Field(default_factory=list, max_length=100)


class TeamUpdate(BaseModel):
    role: Literal["recruiter", "interviewer"]
    active: bool
    assigned_job_ids: list[int] = Field(default_factory=list, max_length=100)


class AcceptInvitation(BaseModel):
    token: str = Field(min_length=20, max_length=200)
