from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Identification(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    type: Literal["CC", "CE", "TI", "PPT", "passport", "other"]
    number: str = Field(min_length=3, max_length=40, pattern=r"^[\w .\-/]+$")


class PersonalVisibility(BaseModel):
    model_config = ConfigDict(extra="forbid")
    birth_date: bool = False
    identification: bool = False
