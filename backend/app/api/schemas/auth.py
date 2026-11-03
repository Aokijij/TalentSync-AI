from typing import Literal

from pydantic import BaseModel, EmailStr, Field, StrictBool, field_validator

from app.domain.entities.enums import UserRole


class LegalAcceptanceRequest(BaseModel):
    data_processing_accepted: StrictBool
    terms_accepted: StrictBool
    privacy_version: str = Field(min_length=1, max_length=40)
    terms_version: str = Field(min_length=1, max_length=40)


class RegisterRequest(LegalAcceptanceRequest):
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
    invitation_token: str | None = Field(default=None, min_length=20, max_length=200)

    @field_validator("email")
    @classmethod
    def normalized_email(cls, value):
        return value.casefold()

    @field_validator("password")
    @classmethod
    def password_bytes(cls, value):
        if len(value.encode("utf-8")) > 72:
            raise ValueError("La contraseña no puede superar 72 bytes")
        return value

    @field_validator("role")
    @classmethod
    def public_roles_only(cls, value: UserRole) -> UserRole:
        if value == UserRole.ADMIN:
            raise ValueError("No se puede registrar un administrador por este canal")
        return value


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(max_length=72)
    code: str | None = Field(default=None, max_length=128)
    remember: bool = False
    portal: Literal["candidate", "company"] | None = None

    @field_validator("email")
    @classmethod
    def normalized_email(cls, value):
        return value.casefold()

    @field_validator("password")
    @classmethod
    def password_bytes(cls, value):
        if len(value.encode("utf-8")) > 72:
            raise ValueError("La contraseña no puede superar 72 bytes")
        return value


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: UserRole
    email_verified: bool = False
    mfa_enabled: bool = False
    registration_pending: bool = False

    model_config = {"from_attributes": True}


class SocialRegistrationRequest(LegalAcceptanceRequest):
    name: str = Field(min_length=2, max_length=120)
    profession: str = Field(min_length=2, max_length=160)
    confirmed: bool

    @field_validator("name", "profession", mode="before")
    @classmethod
    def clean_text(cls, value):
        return " ".join(value.split()) if isinstance(value, str) else value

    @field_validator("name")
    @classmethod
    def personal_name(cls, value):
        import unicodedata
        if (sum(char.isalpha() for char in value) < 2
                or any(not (char.isalpha() or char in " '-’." or unicodedata.category(char).startswith("M")) for char in value)):
            raise ValueError("Escribe tu nombre, sin números, usuarios de redes ni símbolos")
        return value
