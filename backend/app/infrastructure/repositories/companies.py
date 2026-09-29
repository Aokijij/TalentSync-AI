from sqlalchemy import or_
from sqlalchemy.orm import joinedload, selectinload

from app.infrastructure.database.models import Company, CompanyFollower
from app.infrastructure.repositories.entity import SqlAlchemyRepository


class CompanyRepository(SqlAlchemyRepository[Company]):
    def find_by_owner(self, owner_id: int) -> Company | None:
        return (
            self.session.query(Company)
            .filter(Company.owner_user_id == owner_id)
            .first()
        )

    def find_by_nit(self, nit: str) -> Company | None:
        return self.session.query(Company).filter(Company.nit == nit).first()

    def find_external(self, source_name: str, name: str) -> Company | None:
        return (
            self.session.query(Company)
            .filter(
                Company.is_external.is_(True),
                Company.source_name == source_name,
                Company.name == name,
            )
            .first()
        )

    def count(self) -> int:
        return self.session.query(Company).count()

    @staticmethod
    def _scope(query, scope: str):
        if scope == "platform":
            return query.filter(Company.is_external.is_(False))
        if scope == "external":
            return query.filter(Company.is_external.is_(True))
        return query

    def admin_page(
        self,
        *,
        offset: int,
        limit: int,
        search: str | None = None,
        scope: str = "platform",
    ) -> tuple[list[Company], int]:
        query = self._scope(self.session.query(Company), scope)
        if search:
            pattern = f"%{search.strip()}%"
            query = query.filter(
                or_(Company.name.ilike(pattern), Company.nit.ilike(pattern))
            )
        total = query.count()
        items = (
            query.options(selectinload(Company.jobs))
            .order_by(Company.name.asc(), Company.id.asc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return items, total

    def count_by_scope(self, scope: str) -> int:
        return self._scope(self.session.query(Company), scope).count()

    def list_owned(self, owner_id: int | None) -> list[Company]:
        query = self.session.query(Company)
        if owner_id is not None:
            query = query.filter(Company.owner_user_id == owner_id)
        return query.all()

    def find_follow(
        self, candidate_user_id: int, company_id: int
    ) -> CompanyFollower | None:
        return (
            self.session.query(CompanyFollower)
            .filter(
                CompanyFollower.candidate_user_id == candidate_user_id,
                CompanyFollower.company_id == company_id,
            )
            .first()
        )

    def new_follow(self, **values) -> CompanyFollower:
        return CompanyFollower(**values)

    def followers_for_company(self, company_id: int) -> list[CompanyFollower]:
        return (
            self.session.query(CompanyFollower)
            .options(joinedload(CompanyFollower.candidate))
            .filter(CompanyFollower.company_id == company_id)
            .all()
        )
