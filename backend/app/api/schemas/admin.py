from pydantic import BaseModel, Field, field_validator


class JobCatalogSyncRequest(BaseModel):
    keywords: str = Field(min_length=2, max_length=240)
    location: str = Field(default="Colombia", min_length=2, max_length=120)
    pages: int = Field(default=2, ge=1, le=5)
    result_count: int = Field(default=20, ge=5, le=50)

    @field_validator("keywords", "location")
    @classmethod
    def normalize_text(cls, value: str) -> str:
        return " ".join(value.split())
