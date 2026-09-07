from typing import Protocol

from app.domain.entities.records import Recommendation
from app.domain.repositories.entity import EntityRepository


class RecommendationRepository(EntityRepository[Recommendation], Protocol):
    def find_for_user_job(self, user_id: int, job_id: int) -> Recommendation | None: ...

    def count(self) -> int: ...
