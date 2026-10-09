from typing import Literal

from pydantic import BaseModel, Field, HttpUrl, field_validator

from app.domain.services.skills import skill_key


class SkillRequirement(BaseModel):
    skill: str = Field(min_length=1, max_length=100)
    essential: bool = False
    weight: int = Field(default=1, ge=1, le=5)

    @field_validator("skill")
    @classmethod
    def normalized_skill(cls, value):
        value = skill_key(value)
        if not value:
            raise ValueError("La habilidad no puede estar vacía")
        return value


def unique_requirements(value):
    if value is None:
        raise ValueError("Usa una lista vacía para retirar los requisitos")
    if value is not None and len({item.skill for item in value}) != len(value):
        raise ValueError("Los requisitos no pueden repetirse")
    return value


class CandidatePreferences(BaseModel):
    minimum_salary: float | None = Field(default=None, ge=0, le=1_000_000_000)
    salary_required: bool = False
    modalities: list[Literal["remote", "hybrid", "onsite"]] = Field(default_factory=list, max_length=3)
    modality_required: bool = False
    locations: list[str] = Field(default_factory=list, max_length=30)
    location_required: bool = False

    @field_validator("locations")
    @classmethod
    def bounded_locations(cls, value):
        if any(not item.strip() or len(item) > 120 for item in value):
            raise ValueError("Indica ubicaciones de hasta 120 caracteres")
        return list(dict.fromkeys(item.strip() for item in value))


class EvidenceSubmission(BaseModel):
    add_to_profile: bool = False
    title: str = Field(min_length=3, max_length=160)
    kind: Literal["project", "repository", "portfolio", "experience", "certificate"]
    url: HttpUrl | None = None
    description: str = Field(min_length=10, max_length=2000)
    skills: list[str] = Field(min_length=1, max_length=20)

    @field_validator("skills")
    @classmethod
    def normalized_skills(cls, value):
        result = list(dict.fromkeys(skill_key(item) for item in value))
        if any(not item or len(item) > 100 for item in result):
            raise ValueError("Indica habilidades de hasta 100 caracteres")
        return result


class ProjectEvidenceSubmission(EvidenceSubmission):
    kind: Literal["repository"] = "repository"
    preview_token: str = Field(min_length=50, max_length=30000)
    add_to_profile: bool = False
    confirm_ownership: Literal[True]


class RepositoryPreviewRequest(BaseModel):
    url: str = Field(min_length=10, max_length=250)
    confirm_public_access: Literal[True]
