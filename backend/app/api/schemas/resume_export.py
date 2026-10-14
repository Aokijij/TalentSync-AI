from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.api.schemas.profile import ProfileUpdate

ResumeSection = Literal["contact", "summary", "experiences", "educations", "certifications", "skills", "languages", "evidence", "preferences"]
ALL_SECTIONS = ["contact", "summary", "experiences", "educations", "certifications", "skills", "languages", "evidence", "preferences"]


class ResumeExport(BaseModel):
    model_config = ConfigDict(extra="forbid")
    sections: list[ResumeSection] = Field(default_factory=lambda: list(ALL_SECTIONS), max_length=9)
    include_photo: bool = True
    # A validated draft is used only for this PDF, without changing saved data.
    profile: ProfileUpdate | None = None


class CvMentionDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")
    skill: str = Field(min_length=1, max_length=120)
    action: Literal["confirm", "dismiss", "restore"]
