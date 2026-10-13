from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.api.schemas.language import LanguageLevel, unique_languages
from app.domain.services.experience_dates import validate_experiences


class Mobility(BaseModel):
    model_config = ConfigDict(extra="forbid")
    willing_to_relocate: bool | None = None
    willing_to_travel: bool | None = None
    commuting_cities: list[str] = Field(default_factory=list, max_length=20)

    @field_validator("commuting_cities")
    @classmethod
    def cities(cls, values):
        if any(not value.strip() or len(value.strip()) > 120 for value in values):
            raise ValueError("Indica ciudades válidas de hasta 120 caracteres")
        return list(dict.fromkeys(value.strip() for value in values))


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
    _experience_dates = field_validator("experiences")(validate_experiences)
    mobility: Mobility = Field(default_factory=Mobility)
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
    name: str | None = Field(default=None, min_length=2, max_length=120)


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
    email: str | None = None
    identity_hidden: bool = False
