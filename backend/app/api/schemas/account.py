from typing import Literal

from pydantic import BaseModel, EmailStr, Field


class EmailRequest(BaseModel):
    email: EmailStr


class ActionRequest(BaseModel):
    token: str = Field(min_length=20, max_length=200)
    purpose: Literal["verify", "reset", "email"]
    password: str | None = Field(default=None, min_length=12, max_length=72)


class PasswordRequest(BaseModel):
    password: str = Field(min_length=1, max_length=72)


class SocialAccountRequest(PasswordRequest):
    code: str | None = Field(default=None, min_length=6, max_length=128)


class MfaCode(BaseModel):
    code: str = Field(min_length=6, max_length=128)


class MfaDisable(PasswordRequest):
    code: str = Field(min_length=6, max_length=128)


class ChangeEmail(PasswordRequest):
    email: EmailStr


class PrivacyRequest(BaseModel):
    share_evidence: bool
    notify_new_skills: bool
    personalize_recommendations: bool
