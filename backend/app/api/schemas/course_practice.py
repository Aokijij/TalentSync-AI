from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class PracticeDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=5, max_length=160)
    scenario: str = Field(min_length=20, max_length=1500)
    steps: list[str] = Field(min_length=3, max_length=8)
    calculation_prompt: str = Field(min_length=10, max_length=800)
    calculation_answer: float = Field(allow_inf_nan=False, ge=-1e9, le=1e9)
    calculation_feedback: str = Field(min_length=10, max_length=800)
    terms: list[str] = Field(min_length=3, max_length=8)
    meanings: list[str] = Field(min_length=3, max_length=8)

    @model_validator(mode="after")
    def valid_pairs(self):
        for key in ("steps", "terms", "meanings"):
            values = [value.strip() for value in getattr(self, key)]
            if any(len(value) < 2 or len(value) > 300 for value in values) or len(set(values)) != len(values):
                raise ValueError("Los pasos y conceptos deben ser distintos y tener entre 2 y 300 caracteres")
            setattr(self, key, values)
        if len(self.terms) != len(self.meanings):
            raise ValueError("Cada concepto necesita una definición")
        if not self.title.strip() or len(self.scenario.strip()) < 20:
            raise ValueError("Describe el título y el caso de la práctica")
        return self


class PracticeBinding(BaseModel):
    model_config = ConfigDict(extra="forbid")
    mode: Literal["none", "template", "custom"] = "none"
    template_id: str | None = None
    level: Literal["beginner", "intermediate", "advanced"] = "beginner"
    rationale: str = Field(default="", max_length=600)
    draft: PracticeDraft | None = None

    @model_validator(mode="after")
    def configured(self):
        if self.mode == "template":
            from app.domain.services.course_practices import TOPICS
            if self.template_id not in {row[0] for row in TOPICS}:
                raise ValueError("Elige una práctica disponible")
        if self.mode == "custom" and self.draft is None:
            raise ValueError("Completa las tres actividades de la práctica")
        if self.mode != "none" and len(self.rationale.strip()) < 20:
            raise ValueError("Explica con al menos 20 caracteres cómo se relaciona la práctica con el temario")
        if self.mode != "custom":
            self.draft = None
        if self.mode != "template":
            self.template_id = None
        return self
