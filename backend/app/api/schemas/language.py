from pydantic import BaseModel, Field, field_validator

from app.domain.services.languages import language_level, language_name


class LanguageLevel(BaseModel):
    name: str = Field(min_length=2, max_length=60)
    level: str

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        name = language_name(value)
        if len(name) < 2:
            raise ValueError("Escribe el nombre del idioma")
        return name

    @field_validator("level")
    @classmethod
    def validate_level(cls, value: str) -> str:
        level = language_level(value)
        if level not in {"A1", "A2", "B1", "B2", "C1", "C2", "NATIVE"}:
            raise ValueError("Elige un nivel de idioma entre A1 y C2 o Nativo")
        return level


def unique_languages(items):
    if items and len({item.name for item in items}) != len(items):
        raise ValueError("No repitas un idioma; selecciona su nivel en una sola fila")
    return items or []
