from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class CatalogJob:
    external_id: str
    title: str
    company: str
    location: str
    description: str
    employment_type: str
    salary: str
    url: str
    published_at: datetime | None = None
    skills: tuple[str, ...] = ()
    benefits: tuple[str, ...] = ()
    company_url: str | None = None
    remote: bool | None = None
    requirements: str = ""


@dataclass(frozen=True)
class CatalogPage:
    jobs: list[CatalogJob]
    total: int
