from sqlalchemy.orm import joinedload

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

    def first_fifty(self) -> list[Company]:
        return self.session.query(Company).limit(50).all()

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
