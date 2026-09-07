from app.infrastructure.database.models import Company
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

    def count(self) -> int:
        return self.session.query(Company).count()

    def first_fifty(self) -> list[Company]:
        return self.session.query(Company).limit(50).all()

    def list_owned(self, owner_id: int | None) -> list[Company]:
        query = self.session.query(Company)
        if owner_id is not None:
            query = query.filter(Company.owner_user_id == owner_id)
        return query.all()
