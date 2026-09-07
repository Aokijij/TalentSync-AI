from datetime import datetime

from pydantic import BaseModel, Field, field_validator, model_validator

from app.domain.entities.job_sectors import JOB_SECTORS


class PipelineStage(BaseModel):
    id: str = Field(min_length=2, max_length=80, pattern=r"^[a-z0-9][a-z0-9_-]*$")
    title: str = Field(min_length=2, max_length=60)


class PipelineStagesMixin(BaseModel):
    @model_validator(mode="after")
    def validate_pipeline(self):
        stages = getattr(self, "pipeline_stages", None)
        if stages is not None and len({stage.id for stage in stages}) != len(stages):
            raise ValueError("Las etapas del proceso no pueden repetirse")
        return self


def default_pipeline_stages() -> list[PipelineStage]:
    return [
        PipelineStage(id="submitted", title="Nuevos"),
        PipelineStage(id="shortlisted", title="Preseleccionados"),
        PipelineStage(id="technical_interview", title="Entrevista técnica"),
        PipelineStage(id="psychometric_test", title="Prueba psicotécnica"),
        PipelineStage(id="hired", title="Contratados"),
        PipelineStage(id="rejected", title="Descartados"),
    ]


class JobCreate(PipelineStagesMixin):
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

    @field_validator("sector")
    @classmethod
    def validate_sector(cls, value: str) -> str:
        if value not in JOB_SECTORS:
            raise ValueError("Sector laboral no valido")
        return value


class JobUpdate(PipelineStagesMixin):
    title: str | None = Field(default=None, min_length=2, max_length=180)
    description: str | None = Field(default=None, min_length=10)
    requirements: str | None = Field(default=None, min_length=10)
    salary: float | None = None
    location: str | None = None
    department: str | None = None
    modality: str | None = None
    employment_type: str | None = None
    sector: str | None = None
    status: str | None = None
    benefits: list[str] | None = None
    pipeline_stages: list[PipelineStage] | None = Field(
        default=None, min_length=2, max_length=12
    )

    @field_validator("sector")
    @classmethod
    def validate_optional_sector(cls, value: str | None) -> str | None:
        if value is not None and value not in JOB_SECTORS:
            raise ValueError("Sector laboral no valido")
        return value


class JobResponse(BaseModel):
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

    model_config = {"from_attributes": True}
