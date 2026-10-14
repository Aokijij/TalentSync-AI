from typing import Protocol

from app.domain.entities.records import Profile
from app.domain.repositories.entity import EntityRepository


class ProfileRepository(EntityRepository[Profile], Protocol):
    def lock_owner(self, user_id): ...
    def coach_state(self, user_id): ...
    def new_coach_state(self, user_id): ...
