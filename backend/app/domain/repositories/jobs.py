from datetime import datetime
from typing import Protocol

from app.domain.entities.records import Job
from app.domain.repositories.entity import EntityRepository


class JobRepository(EntityRepository[Job], Protocol):
    def active(self) -> list[Job]: ...

    def count_active(self) -> int: ...

    def active_skill_rows(self) -> list[tuple[list[str]]]: ...

    def get_with_company(self, job_id: int) -> Job | None: ...

    def count(self) -> int: ...

    def recent(self) -> list[Job]: ...

    def search(
        self,
        search: str | None,
        modality: str | None,
        location: str | None,
        department: str | None,
        sector: str | None,
        employment_type: str | None,
        status_filter: str | None,
        min_salary: float | None = None,
        max_salary: float | None = None,
        created_after: datetime | None = None,
        sort: str = "newest",
    ) -> list[Job]: ...
