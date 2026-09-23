from pydantic import BaseModel, Field


class CompanyCreate(BaseModel):
    name: str = Field(min_length=2, max_length=180)
    nit: str = Field(min_length=3, max_length=80)
    description: str | None = None
    website: str | None = Field(default=None, max_length=255)
    sector: str | None = Field(default=None, max_length=120)
    size: str | None = Field(default=None, max_length=80)
    location: str | None = Field(default=None, max_length=160)
    mission: str | None = None
    values: list[str] = Field(default_factory=list)
    benefits: list[str] = Field(default_factory=list)


class CompanyUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=180)
    nit: str | None = Field(default=None, min_length=3, max_length=80)
    description: str | None = None
    website: str | None = Field(default=None, max_length=255)
    sector: str | None = Field(default=None, max_length=120)
    size: str | None = Field(default=None, max_length=80)
    location: str | None = Field(default=None, max_length=160)
    mission: str | None = None
    values: list[str] | None = None
    benefits: list[str] | None = None


class CompanyResponse(CompanyCreate):
    id: int
    owner_user_id: int
    logo_url: str | None = None
    cover_url: str | None = None
    is_external: bool = False
    source_name: str | None = None

    model_config = {"from_attributes": True}


class CompanyFollowSettings(BaseModel):
    min_match: float = Field(default=60, ge=0, le=100)


class CompanyFollowResponse(BaseModel):
    company_id: int
    is_following: bool
    min_match: float = 60
