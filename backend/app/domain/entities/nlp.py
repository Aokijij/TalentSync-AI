from dataclasses import dataclass, field


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
    skill_context: list[dict] = field(default_factory=list)
    entity_review: dict = field(default_factory=dict)
