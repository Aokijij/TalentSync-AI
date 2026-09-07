from typing import Protocol

from app.domain.entities.records import Profile
from app.domain.repositories.entity import EntityRepository


class ProfileRepository(EntityRepository[Profile], Protocol):
    pass
