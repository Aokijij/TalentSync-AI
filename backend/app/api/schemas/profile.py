from datetime import date, datetime
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    field_validator,
    model_serializer,
    model_validator,
)

from app.api.schemas.credentials import DrivingLicense, ProfessionalCard
from app.api.schemas.language import LanguageLevel, unique_languages
from app.api.schemas.personal_details import Identification, PersonalVisibility
from app.domain.services.colombian_locations import canonical_commuting_city
from app.domain.services.credential_links import certificate_url
from app.domain.services.experience_dates import validate_experiences
from app.domain.services.profile_links import LINK_PLATFORMS, professional_link_url
from app.domain.services.profile_status import (
    single_current_employment,
    validate_educations,
)
from app.domain.services.skills import skill_key
from app.domain.services.training_types import validate_training


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
        return list(dict.fromkeys(canonical_commuting_city(value) for value in values))


class ProfileLink(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    platform: Literal["linkedin", "github", "portfolio", "gitlab", "behance", "dribbble", "kaggle", "stackoverflow", "medium", "youtube", "other"]
    url: HttpUrl
    label: str = Field(default="", max_length=60)

    @model_validator(mode="after")
    def professional_url(self):
        professional_link_url(self.url)
        label, domain = LINK_PLATFORMS[self.platform]
        host = (self.url.host or "").lower()
        if domain and host != domain and not host.endswith("." + domain):
            raise ValueError(f"El enlace de {label} debe pertenecer a {domain}")
        return self


class ProfileBase(BaseModel):
    profession: str | None = None
    skills: list[str] = Field(default_factory=list)
    skill_levels: dict[str, Literal["learning", "basic", "intermediate", "advanced", "expert"]] | None = Field(default=None, max_length=100)

    @field_validator("skill_levels")
    @classmethod
    def normalized_levels(cls, value):
        if value is None:
            return None
        if any(not skill_key(key) or len(key) > 100 for key in value):
            raise ValueError("Indica nombres válidos de habilidades de hasta 100 caracteres")
        return {skill_key(key): level for key, level in value.items()}
    driving_licenses: list[DrivingLicense] = Field(default_factory=list, max_length=8)
    professional_cards: list[ProfessionalCard] = Field(default_factory=list, max_length=20)
    languages: list[LanguageLevel] = Field(default_factory=list, max_length=20)

    _unique_languages = field_validator("languages")(unique_languages)
    experience: str | None = None
    summary_mode: Literal["automatic", "custom"] | None = None
    education: str | None = None
    location: str | None = None
    department: str | None = None
    availability: str | None = None
    preferred_modality: str | None = None
    preferred_sector: str | None = None
    desired_salary: float | None = None
    phone: str | None = None
    links: list[ProfileLink] = Field(default_factory=list, max_length=10)

    @field_validator("driving_licenses")
    @classmethod
    def unique_driving_categories(cls, values):
        if values is not None and len({row.category for row in values}) != len(values):
            raise ValueError("No repitas una categoría de licencia de conducción")
        return values

    @field_validator("links")
    @classmethod
    def unique_links(cls, values):
        if values is not None and len({str(item.url) for item in values}) != len(values):
            raise ValueError("No repitas el mismo enlace profesional")
        return values
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
    birth_date: date | None = None
    identification: Identification | None = None
    personal_visibility: PersonalVisibility = Field(default_factory=PersonalVisibility)

    @field_validator("birth_date")
    @classmethod
    def valid_birth_date(cls, value):
        if value is not None and (value > date.today() or value.year < 1900):
            raise ValueError("Indica una fecha de nacimiento válida, entre 1900 y hoy")
        return value

    driving_licenses: list[DrivingLicense] | None = Field(default=None, max_length=8)
    professional_cards: list[ProfessionalCard] | None = Field(default=None, max_length=20)
    # Omission preserves links for older clients; an empty list removes them.
    links: list[ProfileLink] | None = Field(default=None, max_length=10)
    experience: str | None = Field(default=None, max_length=3000)
    name: str | None = Field(default=None, min_length=2, max_length=120)
    _single_employment = field_validator("experiences")(single_current_employment)
    _study_status = field_validator("educations")(validate_educations)

    @field_validator("certifications")
    @classmethod
    def certificate_links(cls, values):
        return [{**item, "url": certificate_url(item.get("url"))} for item in validate_training(values) or []]


class ProfileResponse(ProfileBase):
    birth_date: date | None = None
    identification: Identification | None = None
    personal_visibility: PersonalVisibility = Field(default_factory=PersonalVisibility)
    skill_level_sources: dict = Field(default_factory=dict)
    id: int
    user_id: int
    cv_text: str | None = None
    cv_filename: str | None = None
    cv_uploaded_at: datetime | None = None
    photo_url: str | None = None
    resume_export_options: dict = Field(default_factory=dict)
    cv_skill_context: list[dict] = Field(default_factory=list)
    cv_mention_decisions: dict = Field(default_factory=dict)
    cv_entity_review: dict = Field(default_factory=dict)
    cv_guidance: dict = Field(default_factory=dict)

    model_config = {"from_attributes": True}


class CandidateProfileResponse(ProfileResponse):
    personal_visibility: PersonalVisibility = Field(default_factory=PersonalVisibility, exclude=True)

    @model_serializer(mode="wrap")
    def only_shared_personal_details(self, handler):
        result = handler(self)
        for key in ("birth_date", "identification"):
            if getattr(self, key) is None:
                result.pop(key, None)
        return result
    submitted_version: str | None = None
    name: str
    email: str | None = None
    identity_hidden: bool = False
