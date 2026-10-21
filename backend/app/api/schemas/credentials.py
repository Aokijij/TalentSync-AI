from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

DrivingCategory = Literal["A1", "A2", "B1", "B2", "B3", "C1", "C2", "C3"]
CredentialStatus = Literal["valid", "expired", "suspended", "in_progress", "unknown"]


class DrivingLicense(BaseModel):
    model_config = ConfigDict(extra="forbid")
    category: DrivingCategory
    status: CredentialStatus = "unknown"
    expires_on: date | None = None


class ProfessionalCard(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    profession: str = Field(min_length=2, max_length=160)
    issuer: str = Field(default="", max_length=160)
    number: str = Field(default="", max_length=60)
    status: CredentialStatus = "unknown"
    expires_on: date | None = None


class CredentialRequirements(BaseModel):
    model_config = ConfigDict(extra="forbid")
    driving_categories: list[DrivingCategory] = Field(
        default_factory=list, max_length=8
    )
    professional_cards: list[str] = Field(default_factory=list, max_length=20)

    @field_validator("driving_categories")
    @classmethod
    def unique_categories(cls, values):
        return list(dict.fromkeys(values))

    @field_validator("professional_cards")
    @classmethod
    def valid_professions(cls, values):
        from app.domain.services.academic_fields import academic_name

        cleaned = [value.strip() for value in values]
        if any(len(value) < 2 or len(value) > 160 for value in cleaned):
            raise ValueError("Indica profesiones de entre 2 y 160 caracteres")
        return list({academic_name(value): value for value in cleaned}.values())
