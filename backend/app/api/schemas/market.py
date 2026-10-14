from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, StrictBool, model_validator

MarketFamily = Literal["", "software", "data", "electronics", "civil", "business", "finance", "marketing", "people", "industrial", "health", "legal", "education", "sales", "service", "logistics", "design"]
MarketLevel = Literal["", "entry", "junior", "mid", "senior", "lead"]


class MarketFilters(BaseModel):
    search: str = Field(default="", max_length=160)
    family: MarketFamily = ""
    level: MarketLevel = ""
    location: str = Field(default="", max_length=120)
    sector: str = Field(default="", max_length=120)
    modality: Literal["", "remote", "hybrid", "onsite"] = ""


class MarketParticipation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enabled: StrictBool
    family: MarketFamily = ""
    level: MarketLevel = ""
    confirm_real_profile: StrictBool = False

    @model_validator(mode="after")
    def explicit_choice(self):
        if self.enabled and (not self.family or not self.level or not self.confirm_real_profile):
            raise ValueError("Elige tu área y nivel y confirma que compartes datos reales de tu perfil")
        return self


class MarketSkill(BaseModel):
    model_config = ConfigDict(extra="forbid")
    skill: str = Field(min_length=1, max_length=120)
    confirm: StrictBool
