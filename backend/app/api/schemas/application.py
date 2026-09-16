from datetime import datetime

from pydantic import BaseModel

from app.domain.entities.enums import ApplicationStatus


class ApplicationCreate(BaseModel):
    job_id: int


class ApplicationStatusUpdate(BaseModel):
    status: ApplicationStatus | None = None
    pipeline_stage: str | None = None
    recruiter_notes: str | None = None
    interview_at: datetime | None = None


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
