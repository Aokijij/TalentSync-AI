from typing import Literal

from pydantic import BaseModel, EmailStr, Field, HttpUrl


class VerificationSubmission(BaseModel):
    legal_name: str = Field(min_length=3, max_length=180)
    website: HttpUrl | None = None
    registry_reference: str = Field(min_length=5, max_length=300)
    representative_role: str = Field(min_length=3, max_length=120)
    notes: str = Field(default="", max_length=1500)
    tax_id: str = Field(min_length=5, max_length=80)
    business_activity: str = Field(min_length=10, max_length=500)
    address: str = Field(min_length=8, max_length=250)
    city: str = Field(min_length=2, max_length=100)
    contact_email: EmailStr
    contact_phone: str = Field(min_length=7, max_length=30)
    representative_name: str = Field(min_length=5, max_length=160)
    registry_authority: str = Field(min_length=5, max_length=160)
    registry_document_url: HttpUrl
    accuracy_confirmed: Literal[True]


class AccessReviewRequest(BaseModel):
    message: str = Field(min_length=20, max_length=1000)


class InterviewEvaluation(BaseModel):
    rating: int = Field(ge=1, le=5)
    recommendation: Literal["continue", "hold", "not_recommended"]
    summary: str = Field(min_length=20, max_length=1500)


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


class InterviewAssignments(BaseModel):
    assigned_job_ids: list[int] = Field(default_factory=list, max_length=100)
    model_config = {"extra": "forbid"}


class AcceptInvitation(BaseModel):
    token: str = Field(min_length=20, max_length=200)
