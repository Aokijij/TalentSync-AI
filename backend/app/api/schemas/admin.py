from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator

from app.api.schemas.job_quality import QualityDetails
from app.api.schemas.language import LanguageLevel, unique_languages
from app.api.schemas.matching import SkillRequirement, unique_requirements
from app.domain.entities.job_sectors import JOB_SECTORS


class ExternalContentFields(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    external_published_at: datetime | None = None
    title: str | None = Field(default=None, min_length=2, max_length=180)
    location: str | None = Field(default=None, max_length=300)
    department: str | None = Field(default=None, max_length=100)
    modality: Literal["remote", "hybrid", "onsite"] | None = None
    employment_type: Literal["full_time", "part_time", "contract", "internship", "temporary"] | None = None
    sector: str | None = None
    benefits: list[str] | None = Field(default=None, max_length=30)
    languages: list[LanguageLevel] | None = Field(default=None, max_length=20)
    skill_requirements: list[SkillRequirement] | None = Field(default=None, max_length=50)
    quality_details: QualityDetails | None = None
    description: str | None = Field(default=None, max_length=40000)
    requirements: str | None = Field(default=None, max_length=20000)
    salary: float | None = Field(default=None, ge=0, le=1_000_000_000, allow_inf_nan=False)
    skills: list[str] | None = Field(default=None, max_length=50)
    required_education_level: Literal["secondary", "technical", "technologist", "university", "postgraduate"] | None = None
    required_study_fields: list[str] | None = Field(default=None, max_length=20)

    @field_validator("title", "description", "requirements", "skills", "required_study_fields", "languages", "skill_requirements", "quality_details", "modality", "employment_type", "benefits")
    @classmethod
    def reject_null(cls, value):
        if value is None:
            raise ValueError("Usa un valor explícito para actualizar este campo")
        return value

    @field_validator("external_published_at")
    @classmethod
    def source_date(cls, value, info):
        if value is None:
            return value
        if value.tzinfo:
            value = value.astimezone(timezone.utc).replace(tzinfo=None)
        if info.field_name == "external_published_at" and value > datetime.now(timezone.utc).replace(tzinfo=None):
            raise ValueError("La publicación original no puede tener una fecha futura")
        return value

    @field_validator("languages")
    @classmethod
    def distinct_languages(cls, value):
        return unique_languages(value)

    @field_validator("skill_requirements")
    @classmethod
    def distinct_requirements(cls, value):
        return unique_requirements(value)

    @field_validator("sector")
    @classmethod
    def known_sector(cls, value):
        if value is not None and value not in JOB_SECTORS:
            raise ValueError("Selecciona un sector del catálogo")
        return value


class ExternalContentReview(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    revision: int = Field(ge=0)
    source_url: HttpUrl
    note: str = Field(min_length=10, max_length=2000)
    fields: ExternalContentFields


class CatalogCleanupRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    ids: list[int] = Field(min_length=1, max_length=200)


class ManualSourceReview(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    source_url: HttpUrl
    confirmed_open: Literal[True]
    note: str = Field(min_length=20, max_length=2000)


class ExternalCatalogStatus(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    status: Literal["active", "draft", "paused", "closed"]
    revision: int = Field(ge=0)
    note: str = Field(min_length=5, max_length=2000)
    manual_verification: ManualSourceReview | None = None


class PublicationReview(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Literal["automatic", "approved", "held"]
    note: str = Field(min_length=5, max_length=2000)
    revision: int = Field(ge=0)

    @field_validator("note")
    @classmethod
    def clean_note(cls, value):
        value = value.strip()
        if len(value) < 5:
            raise ValueError("Indica un motivo para registrar la decisión")
        return value


class JobCatalogSyncRequest(BaseModel):
    keywords: str = Field(min_length=2, max_length=240)
    location: str = Field(default="Colombia", min_length=2, max_length=120)
    pages: int = Field(default=2, ge=1, le=5)
    result_count: int = Field(default=20, ge=5, le=50)

    @field_validator("keywords", "location")
    @classmethod
    def normalize_text(cls, value: str) -> str:
        return " ".join(value.split())


class EmployerBoardRequest(BaseModel):
    board_url: str = Field(min_length=15, max_length=500)
    keywords: str = Field(default="", max_length=120)
    location: str = Field(default="Colombia", max_length=120)
    selected_ids: list[str] = Field(default_factory=list, max_length=50)
    authorized: bool = False

    @field_validator("board_url")
    @classmethod
    def valid_board(cls, value):
        from app.infrastructure.job_catalogs.ats import board_reference
        board_reference(value)
        return value
