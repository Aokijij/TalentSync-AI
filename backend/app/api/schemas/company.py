from pydantic import BaseModel, Field


class CompanyCreate(BaseModel):
    name: str = Field(min_length=2, max_length=180)
    nit: str = Field(min_length=3, max_length=80)
    description: str | None = None


class CompanyUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=180)
    nit: str | None = Field(default=None, min_length=3, max_length=80)
    description: str | None = None


class CompanyResponse(CompanyCreate):
    id: int
    owner_user_id: int

    model_config = {"from_attributes": True}
