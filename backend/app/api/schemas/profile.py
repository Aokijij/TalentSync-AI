from datetime import datetime

from pydantic import BaseModel, Field


class ProfileBase(BaseModel):
    profession: str | None = None
    skills: list[str] = Field(default_factory=list)
    experience: str | None = None
    education: str | None = None
    location: str | None = None
    department: str | None = None
    availability: str | None = None
    preferred_modality: str | None = None
    preferred_sector: str | None = None
    desired_salary: float | None = None
    phone: str | None = None
    # Older profiles can have NULL in these columns until they are edited.
    experiences: list[dict] | None = Field(default_factory=list)
    educations: list[dict] | None = Field(default_factory=list)
    certifications: list[dict] | None = Field(default_factory=list)


class ProfileUpdate(ProfileBase):
    pass


class ProfileResponse(ProfileBase):
    id: int
    user_id: int
    cv_text: str | None = None
    cv_filename: str | None = None
    cv_uploaded_at: datetime | None = None

    model_config = {"from_attributes": True}


class CandidateProfileResponse(ProfileResponse):
    name: str
    email: str
