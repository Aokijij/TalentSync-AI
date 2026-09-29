from typing import Protocol

from app.domain.entities.records import Company, CompanyFollower
from app.domain.repositories.entity import EntityRepository


class CompanyRepository(EntityRepository[Company], Protocol):
    def find_by_owner(self, owner_id: int) -> Company | None: ...

    def find_by_nit(self, nit: str) -> Company | None: ...

    def find_external(self, source_name: str, name: str) -> Company | None: ...

    def count(self) -> int: ...

    def admin_page(
        self,
        *,
        offset: int,
        limit: int,
        search: str | None = None,
        scope: str = "platform",
    ) -> tuple[list[Company], int]: ...

    def count_by_scope(self, scope: str) -> int: ...

    def list_owned(self, owner_id: int | None) -> list[Company]: ...

    def find_follow(
        self, candidate_user_id: int, company_id: int
    ) -> CompanyFollower | None: ...

    def new_follow(self, **values) -> CompanyFollower: ...

    def followers_for_company(self, company_id: int) -> list[CompanyFollower]: ...
