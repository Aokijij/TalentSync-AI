from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field


class SummaryExperience(BaseModel):
    role: str = Field(default="", max_length=300)
    description: str = Field(default="", max_length=3000)
    is_current: bool = False
    start_date: str = Field(default="", max_length=7)
    end_date: str = Field(default="", max_length=7)
    start_year: str = Field(default="", max_length=20)
    end_year: str = Field(default="", max_length=20)


class SummaryEducation(BaseModel):
    degree: str = Field(default="", max_length=300)
    is_current: bool = False


class SummaryProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")
    profession: str = Field(default="", max_length=300)
    skills: list[Annotated[str, Field(min_length=1, max_length=100)]] = Field(default_factory=list, max_length=100)
    experience: str = Field(default="", max_length=3000)
    education: str = Field(default="", max_length=1000)
    experiences: list[SummaryExperience] = Field(default_factory=list, max_length=100)
    educations: list[SummaryEducation] = Field(default_factory=list, max_length=100)


class SummaryGeneration(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tone: Literal["professional", "concise"] = "professional"
    profile: SummaryProfile | None = None
