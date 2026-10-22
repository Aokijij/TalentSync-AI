from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class Facts(BaseModel):
    model_config = ConfigDict(extra="forbid")
    situation: str = Field(min_length=1, max_length=700)
    task: str = Field(min_length=1, max_length=700)
    action: str = Field(min_length=1, max_length=700)
    result: str = Field(min_length=1, max_length=700)


class WritingProposal(BaseModel):
    experience_index: int = Field(ge=0, le=99)
    source_version: str = Field(min_length=64, max_length=64)
    facts: Facts


class WritingDecision(BaseModel):
    action: Literal["apply", "undo"]
    text: str | None = Field(default=None, min_length=1, max_length=3000)


class WritingGeneration(BaseModel):
    model_config = ConfigDict(extra="forbid")
    experience_index: int = Field(ge=0, le=99)
    source_version: str = Field(min_length=64, max_length=64)
    style: Literal["paragraph", "bullets"] = "paragraph"
    result: str = Field(default="", max_length=700)


class ResumeVersionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request_key: UUID
    source_version: str = Field(pattern=r"^[a-f0-9]{64}$")
    job_version: str = Field(pattern=r"^[a-f0-9]{64}$")
    summary: str | None = Field(default=None, max_length=3000)
    experience_indices: list[int] | None = Field(default=None, max_length=100)
    skills: list[str] | None = Field(default=None, max_length=100)
    style: Literal["classic", "modern", "minimal"] = "modern"
    include_photo: bool = True


class InterviewAnswer(BaseModel):
    model_config = ConfigDict(extra="forbid")
    situation: str = Field(default="", max_length=1500)
    task: str = Field(default="", max_length=1500)
    action: str = Field(default="", max_length=1500)
    result: str = Field(default="", max_length=1500)


class InterviewPreparationUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expected_version: int = Field(ge=0)
    revision: str = Field(pattern=r"^[a-f0-9]{64}$")
    answers: dict[str, InterviewAnswer] = Field(default_factory=dict, max_length=10)
