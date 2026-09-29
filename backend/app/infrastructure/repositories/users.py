from datetime import datetime

from sqlalchemy import or_

from app.domain.entities.enums import UserRole
from app.infrastructure.database.models import Profile, User
from app.infrastructure.repositories.entity import SqlAlchemyRepository


class UserRepository(SqlAlchemyRepository[User]):
    def find_by_email(self, email: str) -> User | None:
        return self.session.query(User).filter(User.email == email).first()

    def candidates_with_profiles(self) -> list[User]:
        return (
            self.session.query(User)
            .join(Profile)
            .filter(User.role == UserRole.CANDIDATE)
            .all()
        )

    def count(self) -> int:
        return self.session.query(User).count()

    def count_candidates(self) -> int:
        return self.session.query(User).filter(User.role == UserRole.CANDIDATE).count()

    def first_admin(self) -> User | None:
        return self.session.query(User).filter(User.role == UserRole.ADMIN).first()

    def creation_dates(self) -> list[datetime]:
        return [
            created_at for (created_at,) in self.session.query(User.created_at).all()
        ]

    def admin_page(
        self,
        *,
        offset: int,
        limit: int,
        search: str | None = None,
        role: str | None = None,
    ) -> tuple[list[User], int]:
        query = self.session.query(User)
        if role:
            query = query.filter(User.role == UserRole(role))
        if search:
            pattern = f"%{search.strip()}%"
            query = query.filter(
                or_(User.name.ilike(pattern), User.email.ilike(pattern))
            )
        total = query.count()
        return (
            query.order_by(User.created_at.desc(), User.id.desc())
            .offset(offset)
            .limit(limit)
            .all(),
            total,
        )
