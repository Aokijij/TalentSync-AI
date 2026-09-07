from datetime import datetime

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

    def creation_dates(self) -> list[datetime]:
        return [
            created_at for (created_at,) in self.session.query(User.created_at).all()
        ]

    def recent(self) -> list[User]:
        return self.session.query(User).order_by(User.created_at.desc()).limit(50).all()
