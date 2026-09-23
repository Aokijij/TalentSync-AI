from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from app.domain.entities.job_sectors import JOB_SECTORS
from app.api.schemas.language import LanguageLevel, unique_languages


class PipelineStage(BaseModel):
    id: str = Field(min_length=2, max_length=80, pattern=r"^[a-z0-9][a-z0-9_-]*$")
    title: str = Field(min_length=2, max_length=60)


class ScreeningQuestionPublic(BaseModel):
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
    keywords: list[str] = Field(default_factory=list, max_length=20)
    preferred_options: list[str] = Field(default_factory=list, max_length=12)
    option_scores: dict[str, float] = Field(default_factory=dict, max_length=12)
    positive_adjustment: float = Field(default=3, ge=0, le=10)
    negative_adjustment: float = Field(default=-1, ge=-10, le=0)

    @model_validator(mode="after")
    def validate_scoring(self):
        if self.type == "choice" and any(
            option not in self.options for option in self.preferred_options
        ):
            raise ValueError("La respuesta preferida debe pertenecer a las opciones")
        if self.type == "choice" and any(
            option not in self.options for option in self.option_scores
        ):
            raise ValueError("La valoración debe pertenecer a una opción existente")
        if any(score < -10 or score > 10 for score in self.option_scores.values()):
            raise ValueError("La valoración de cada opción debe estar entre -10 y 10")
        if self.type == "open" and self.preferred_options:
            raise ValueError("Las preguntas abiertas usan palabras clave")
        if self.type == "open" and self.option_scores:
            raise ValueError("Las preguntas abiertas no usan valoración automática")
        return self


class PipelineStagesMixin(BaseModel):
    @model_validator(mode="after")
    def validate_pipeline(self):
        stages = getattr(self, "pipeline_stages", None)
        if stages is not None and len({stage.id for stage in stages}) != len(stages):
            raise ValueError("Las etapas del proceso no pueden repetirse")
        return self


def default_pipeline_stages() -> list[PipelineStage]:
    return [
        PipelineStage(id="submitted", title="Recibidas"),
        PipelineStage(id="reviewing", title="En revisión"),
        PipelineStage(id="interview", title="Entrevista"),
        PipelineStage(id="hired", title="Contratados"),
        PipelineStage(id="rejected", title="No seleccionados"),
    ]


class JobCreate(PipelineStagesMixin):
    languages: list[LanguageLevel] = Field(default_factory=list, max_length=20)
    _unique_languages = field_validator("languages")(unique_languages)
    company_id: int | None = None
    title: str = Field(min_length=2, max_length=180)
    description: str = Field(min_length=10)
    requirements: str = Field(min_length=10)
    salary: float | None = None
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
    languages: list[LanguageLevel] | None = Field(default=None, max_length=20)
    _unique_languages = field_validator("languages")(unique_languages)
    title: str | None = Field(default=None, min_length=2, max_length=180)
    description: str | None = Field(default=None, min_length=10)
    requirements: str | None = Field(default=None, min_length=10)
    salary: float | None = None
    location: str | None = None
    department: str | None = None
    modality: str | None = None
    employment_type: str | None = None
    sector: str | None = None
    status: Literal["active", "paused", "filled", "closed"] | None = None
    benefits: list[str] | None = None
    pipeline_stages: list[PipelineStage] | None = Field(
        default=None, min_length=2, max_length=12
    )
    application_questions: list[ScreeningQuestionConfig] | None = Field(
        default=None, max_length=10
    )

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
    languages: list[LanguageLevel] = Field(default_factory=list)
    application_questions: list[ScreeningQuestionPublic] = Field(default_factory=list)
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
