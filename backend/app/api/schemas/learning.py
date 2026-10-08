import ipaddress
from typing import Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.domain.services.skills import normalize_skills


class ResourceContent(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=3, max_length=160)
    provider: str = Field(min_length=2, max_length=120)
    kind: Literal["course", "workshop", "documentation"] = "course"
    instructions: str = Field(min_length=10, max_length=2000)
    url: str = Field(min_length=10, max_length=1000)
    skills: list[str] = Field(min_length=1, max_length=20)
    hours: float = Field(gt=0, le=1000, allow_inf_nan=False)
    cost: Literal["free", "paid", "unknown"] = "unknown"
    sponsored: bool = False
    affiliate: bool = False
    disclosure: str = Field(default="", max_length=500)
    active: bool = True

    @field_validator("title", "provider", "instructions", "disclosure")
    @classmethod
    def trimmed(cls, value):
        value = value.strip()
        if not value:
            return ""
        return value

    @field_validator("url")
    @classmethod
    def public_https(cls, value):
        try:
            parsed = urlsplit(value)
            host = parsed.hostname or ""
            if (parsed.scheme != "https" or not host or parsed.username or parsed.password
                    or parsed.port not in {None, 443} or "." not in host or any(char.isspace() for char in value)
                    or host.endswith((".localhost", ".local", ".internal", ".test", ".invalid"))):
                raise ValueError()
            try:
                ipaddress.ip_address(host)
            except ValueError:
                pass
            else:
                raise ValueError()
        except ValueError:
            raise ValueError("Usa un enlace HTTPS público, sin credenciales ni direcciones IP") from None
        return value

    @field_validator("skills")
    @classmethod
    def normalized(cls, value):
        result = normalize_skills(value)
        if not result or any(not skill or len(skill) > 100 for skill in result):
            raise ValueError("Indica habilidades válidas de hasta cien caracteres")
        return result

    @model_validator(mode="after")
    def transparent(self):
        if not self.title or not self.provider or len(self.instructions) < 10:
            raise ValueError("Completa título, proveedor y descripción")
        if (self.sponsored or self.affiliate) and len(self.disclosure) < 10:
            raise ValueError("Los recursos patrocinados o afiliados requieren una explicación visible")
        return self


class ResourceUpdate(ResourceContent):
    version: int = Field(ge=1)


class ResourceImport(BaseModel):
    resources: list[ResourceContent] = Field(min_length=1, max_length=50)
