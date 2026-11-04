from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


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
