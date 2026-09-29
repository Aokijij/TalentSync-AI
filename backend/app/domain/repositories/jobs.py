from datetime import datetime
from typing import Protocol

from app.domain.entities.records import Job
from app.domain.repositories.entity import EntityRepository


class JobRepository(EntityRepository[Job], Protocol):
    def active(self) -> list[Job]: ...

    def count_active(self) -> int: ...

    def active_skill_rows(self) -> list[tuple[list[str]]]: ...

    def active_external(self) -> list[Job]: ...

    def company_attention_jobs(self, created_before: datetime) -> list[Job]: ...

    def get_with_company(self, job_id: int) -> Job | None: ...

    def find_external(self, source_name: str, external_id: str) -> Job | None: ...

    def count(self) -> int: ...

    def admin_page(
        self,
        *,
        offset: int,
        limit: int,
        search: str | None = None,
        scope: str = "platform",
    ) -> tuple[list[Job], int]: ...

    def count_by_scope(self, scope: str) -> int: ...

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
