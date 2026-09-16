from datetime import datetime

from pydantic import BaseModel, Field, field_validator
from app.api.schemas.language import LanguageLevel, unique_languages


class ProfileBase(BaseModel):
    profession: str | None = None
    skills: list[str] = Field(default_factory=list)
    languages: list[LanguageLevel] = Field(default_factory=list, max_length=20)

    _unique_languages = field_validator("languages")(unique_languages)
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
    resume_style: str = "classic"
    resume_color: str = "default"

    @field_validator("resume_color")
    @classmethod
    def validate_resume_color(cls, value: str) -> str:
        if value not in {"default", "forest", "wine", "slate", "navy", "blue", "teal", "rose"}:
            raise ValueError("El color de hoja de vida no es válido")
        return value

    @field_validator("resume_style")
    @classmethod
    def validate_resume_style(cls, value: str) -> str:
        if value not in {"classic", "modern", "minimal"}:
            raise ValueError("El estilo de hoja de vida no es válido")
        return value


class ProfileUpdate(ProfileBase):
    pass


class ProfileResponse(ProfileBase):
    id: int
    user_id: int
    cv_text: str | None = None
    cv_filename: str | None = None
    cv_uploaded_at: datetime | None = None
    photo_url: str | None = None

    model_config = {"from_attributes": True}


class CandidateProfileResponse(ProfileResponse):
    name: str
    email: str
