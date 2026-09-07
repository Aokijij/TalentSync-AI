from datetime import datetime
from typing import Protocol

from app.domain.entities.records import User
from app.domain.repositories.entity import EntityRepository


class UserRepository(EntityRepository[User], Protocol):
    def find_by_email(self, email: str) -> User | None: ...

    def candidates_with_profiles(self) -> list[User]: ...

    def count(self) -> int: ...

    def creation_dates(self) -> list[datetime]: ...

    def recent(self) -> list[User]: ...
