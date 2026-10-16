from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from app.api.schemas.job_quality import QualityDetails
from app.api.schemas.language import LanguageLevel, unique_languages
from app.api.schemas.matching import SkillRequirement, unique_requirements
from app.domain.entities.job_sectors import JOB_SECTORS
from app.domain.services.pipeline import default_stages


class PipelineStage(BaseModel):
    id: str = Field(min_length=2, max_length=80, pattern=r"^[a-z0-9][a-z0-9_-]*$")
    title: str = Field(min_length=2, max_length=60)


class ScreeningQuestionPublic(BaseModel):
    category: Literal["screening", "work_scenario"] = "screening"
    id: str = Field(min_length=2, max_length=80, pattern=r"^[a-z0-9][a-z0-9_-]*$")
    prompt: str = Field(min_length=5, max_length=300)
    type: Literal["open", "choice"] = "open"
    required: bool = True
    options: list[str] = Field(default_factory=list, max_length=12)

    @model_validator(mode="after")
    def validate_options(self):
        if self.type == "choice" and len(self.options) < 2:
            raise ValueError("Las preguntas con opciones necesitan al menos dos respuestas")
        if self.type == "choice" and len(set(self.options)) != len(self.options):
            raise ValueError("Las opciones de una pregunta no pueden repetirse")
        if self.type == "open" and self.options:
            raise ValueError("Las preguntas abiertas no usan opciones")
        return self


class ScreeningQuestionConfig(ScreeningQuestionPublic):
    """Choice scores are configured up front; open answers are reviewed later."""

    option_scores: dict[str, float] = Field(default_factory=dict, max_length=12)

    @model_validator(mode="after")
    def validate_choice_scores(self):
        if self.type == "open" and self.option_scores:
            raise ValueError("Las preguntas abiertas se valoran después de la postulación")
        if any(option not in self.options for option in self.option_scores):
            raise ValueError("La valoración debe pertenecer a una opción existente")
        if any(score < -5 or score > 5 for score in self.option_scores.values()):
            raise ValueError("La valoración de cada opción debe estar entre -5 y +5")
        return self


class PipelineStagesMixin(BaseModel):
    @model_validator(mode="after")
    def validate_pipeline(self):
        stages = getattr(self, "pipeline_stages", None)
        if stages is not None and len({stage.id for stage in stages}) != len(stages):
            raise ValueError("Las etapas del proceso no pueden repetirse")
        return self


def default_pipeline_stages() -> list[PipelineStage]:
    return [PipelineStage(**stage) for stage in default_stages()]


class JobCreate(PipelineStagesMixin):
    quality_details: QualityDetails | None = None
    blind_hiring: bool = True
    response_days: int = Field(default=7, ge=1, le=30)
    skill_requirements: list[SkillRequirement] = Field(default_factory=list, max_length=50)
    _unique_requirements = field_validator("skill_requirements")(unique_requirements)
    status: Literal["active", "draft"] = "active"
    languages: list[LanguageLevel] = Field(default_factory=list, max_length=20)
    _unique_languages = field_validator("languages")(unique_languages)
    company_id: int | None = None
    title: str = Field(min_length=2, max_length=180)
    description: str = Field(min_length=10)
    requirements: str = Field(min_length=10)
    salary: float | None = Field(default=None, ge=0, le=1_000_000_000, allow_inf_nan=False)
    location: str | None = None
    department: str | None = None
    modality: str = "remote"
    employment_type: str = "full_time"
    sector: str
    benefits: list[str] = Field(default_factory=list)
    pipeline_stages: list[PipelineStage] = Field(
        default_factory=default_pipeline_stages, min_length=2, max_length=12
    )
    application_questions: list[ScreeningQuestionConfig] = Field(
        default_factory=list, max_length=10
    )
    required_education_level: Literal["secondary", "technical", "technologist", "university", "postgraduate"] | None = None
    required_study_fields: list[str] = Field(default_factory=list, max_length=20)

    @field_validator("application_questions")
    @classmethod
    def validate_question_ids(cls, value: list[ScreeningQuestionConfig]):
        if len({question.id for question in value}) != len(value):
            raise ValueError("Las preguntas de postulación no pueden repetirse")
        return value

    @field_validator("sector")
    @classmethod
    def validate_sector(cls, value: str) -> str:
        if value not in JOB_SECTORS:
            raise ValueError("Sector laboral no valido")
        return value


class JobUpdate(PipelineStagesMixin):
    quality_details: QualityDetails | None = None
    response_days: int | None = Field(default=None, ge=1, le=30)
    skill_requirements: list[SkillRequirement] | None = Field(default=None, max_length=50)
    _unique_requirements = field_validator("skill_requirements")(unique_requirements)
    languages: list[LanguageLevel] | None = Field(default=None, max_length=20)
    _unique_languages = field_validator("languages")(unique_languages)
    title: str | None = Field(default=None, min_length=2, max_length=180)
    description: str | None = Field(default=None, min_length=10)
    requirements: str | None = Field(default=None, min_length=10)
    salary: float | None = Field(default=None, ge=0, le=1_000_000_000, allow_inf_nan=False)
    location: str | None = None
    department: str | None = None
    modality: str | None = None
    employment_type: str | None = None
    sector: str | None = None
    status: Literal["active", "draft", "paused", "filled", "closed"] | None = None
    benefits: list[str] | None = None
    pipeline_stages: list[PipelineStage] | None = Field(
        default=None, min_length=2, max_length=12
    )
    application_questions: list[ScreeningQuestionConfig] | None = Field(
        default=None, max_length=10
    )
    required_education_level: Literal["secondary", "technical", "technologist", "university", "postgraduate"] | None = None
    required_study_fields: list[str] | None = Field(default=None, max_length=20)

    @field_validator("application_questions")
    @classmethod
    def validate_optional_question_ids(
        cls, value: list[ScreeningQuestionConfig] | None
    ):
        if value is not None and len({question.id for question in value}) != len(value):
            raise ValueError("Las preguntas de postulación no pueden repetirse")
        return value

    @field_validator("sector")
    @classmethod
    def validate_optional_sector(cls, value: str | None) -> str | None:
        if value is not None and value not in JOB_SECTORS:
            raise ValueError("Sector laboral no valido")
        return value


class JobResponse(BaseModel):
    quality_details: QualityDetails | None = None
    quality_revision: int = 0
    quality_summary: dict | None = None
    employer_trust: dict = Field(default_factory=dict)
    blind_hiring: bool = False
    response_days: int = 7
    skill_requirements: list[SkillRequirement] = Field(default_factory=list)
    languages: list[LanguageLevel] = Field(default_factory=list)
    application_questions: list[ScreeningQuestionPublic] = Field(default_factory=list)
    required_education_level: str | None = None
    required_study_fields: list[str] = Field(default_factory=list)
    id: int
    company_id: int
    company_name: str | None = None
    title: str
    description: str
    requirements: str
    salary: float | None
    location: str | None
    department: str | None = None
    modality: str
    employment_type: str
    status: str
    benefits: list[str] | None = None
    pipeline_stages: list[PipelineStage] | None = None
    skills: list[str]
    sector: str | None
    created_at: datetime
    applications_count: int = 0
    application_questions_count: int = 0
    company_logo_url: str | None = None
    company_description: str | None = None
    company_website: str | None = None
    company_size: str | None = None
    company_location: str | None = None
    source_kind: str = "internal"
    source_name: str | None = None
    source_portal: str | None = None
    external_url: str | None = None
    expires_at: datetime | None = None

    model_config = {"from_attributes": True}


class JobReopen(BaseModel):
    mode: Literal["continue", "new"]


class PublicStatsResponse(BaseModel):
    active_jobs: int
    companies: int
    candidates: int
    applications: int


class QualityPreview(JobCreate):
    job_id: int | None = None
    title: str = Field(default="", max_length=180)
    description: str = Field(default="", max_length=20000)
    requirements: str = Field(default="", max_length=20000)
