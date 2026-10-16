from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class JobMission(BaseModel):
    model_config = ConfigDict(extra="forbid")
    outcome: str = Field(default="", max_length=500)
    measure: str = Field(default="", max_length=300)
    days: int = Field(default=90, ge=1, le=365)
    skill: str = Field(default="", max_length=100)


class WorkSchedule(BaseModel):
    model_config = ConfigDict(extra="forbid")
    mode: Literal["fixed", "rotating", "flexible", "custom"] = "fixed"
    days: list[Literal["mon", "tue", "wed", "thu", "fri", "sat", "sun"]] = Field(default_factory=list, max_length=7)
    start: str = Field(default="", pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$|^$")
    end: str = Field(default="", pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$|^$")
    break_minutes: int = Field(default=0, ge=0, le=240)
    notes: str = Field(default="", max_length=180)


class RemoteScope(BaseModel):
    model_config = ConfigDict(extra="forbid")
    mode: Literal["global", "regions"] = "global"
    countries: list[str] = Field(default_factory=list, max_length=250)
    continents: list[Literal["AF", "AM", "AS", "EU", "OC", "AN"]] = Field(default_factory=list, max_length=6)

    @field_validator("countries")
    @classmethod
    def valid_countries(cls, value):
        from app.domain.services.remote_locations import countries
        codes = list(dict.fromkeys(code.upper().strip() for code in value))
        if any(code not in countries() for code in codes):
            raise ValueError("Selecciona países del catálogo")
        return codes

    @model_validator(mode="after")
    def consistent_scope(self):
        if self.mode == "global" and (self.countries or self.continents):
            raise ValueError("El alcance mundial no puede tener restricciones seleccionadas")
        return self


class QualityDetails(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: Literal[1] = 1
    salary_max: float | None = Field(default=None, ge=0, le=1_000_000_000, allow_inf_nan=False)
    variable_pay: str = Field(default="", max_length=500)
    salary_currency: Literal["COP"] | None = None
    salary_period: Literal["monthly"] | None = None
    salary_basis: Literal["gross_base"] | None = None
    weekly_hours: float | None = Field(default=None, gt=0, le=80, allow_inf_nan=False)
    contract_type: Literal["", "indefinite", "fixed_term", "services", "apprenticeship", "project"] = ""
    schedule: str = Field(default="", max_length=300)
    work_schedule: WorkSchedule | None = None
    seniority: Literal["", "entry", "junior", "mid", "senior", "lead"] = ""
    experience_years: int | None = Field(default=None, ge=0, le=50)
    experience_months: int | None = Field(default=None, ge=0, le=600)
    education_accepts_in_progress: bool = False
    remote_scope: RemoteScope | None = None
    learnable_skills: list[str] = Field(default_factory=list, max_length=20)
    missions: list[JobMission] = Field(default_factory=list, max_length=5)
    interview_count: int | None = Field(default=None, ge=0, le=10)
    process_days: int | None = Field(default=None, ge=1, le=180)

    @model_validator(mode="after")
    def derive_weekly_hours(self):
        schedule = self.work_schedule
        if schedule is None:
            return self  # Preserve legacy schedules until the structured editor is used.
        self.weekly_hours = None
        if schedule.mode == "fixed" and schedule.days and schedule.start and schedule.end:
            start = sum(int(part) * factor for part, factor in zip(schedule.start.split(":"), (60, 1)))
            end = sum(int(part) * factor for part, factor in zip(schedule.end.split(":"), (60, 1)))
            duration = (end - start) % 1440 - schedule.break_minutes
            if start != end and duration > 0:
                hours = round(duration * len(set(schedule.days)) / 60, 2)
                if hours > 80:
                    raise ValueError("Revisa la jornada: el total calculado supera 80 horas semanales")
                self.weekly_hours = hours
        return self


FeedbackReason = Literal["salary", "requirements", "unclear", "modality", "process", "other"]


class OfferFeedbackInput(BaseModel):
    reason: FeedbackReason
