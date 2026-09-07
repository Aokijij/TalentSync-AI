from dataclasses import dataclass


@dataclass(frozen=True)
class NLPResult:
    clean_text: str
    profession: str | None
    skills: list[str]
    experience: str | None
    education: str | None
    location: str | None
    phone: str | None
    experiences: list[dict]
    educations: list[dict]
    certifications: list[dict]
    embedding: list[float]
