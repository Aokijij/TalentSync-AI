from typing import Literal

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
