from pydantic import BaseModel, EmailStr, Field, field_validator

from app.domain.entities.enums import UserRole


class RegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8)
    role: UserRole = UserRole.CANDIDATE
    profession: str | None = Field(default=None, max_length=160)
    skills: list[str] = Field(default_factory=list)
    experience: str | None = None
    education: str | None = None
    company_name: str | None = Field(default=None, min_length=2, max_length=180)
    nit: str | None = Field(default=None, min_length=3, max_length=80)
    company_description: str | None = None

    @field_validator("role")
    @classmethod
    def public_roles_only(cls, value: UserRole) -> UserRole:
        if value == UserRole.ADMIN:
            raise ValueError("No se puede registrar un administrador por este canal")
        return value


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: UserRole

    model_config = {"from_attributes": True}
