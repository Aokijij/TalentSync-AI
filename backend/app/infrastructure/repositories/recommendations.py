from app.infrastructure.database.models import Recommendation
from app.infrastructure.repositories.entity import SqlAlchemyRepository


class RecommendationRepository(SqlAlchemyRepository[Recommendation]):
    def find_for_user_job(self, user_id: int, job_id: int) -> Recommendation | None:
        return (
            self.session.query(Recommendation)
            .filter(Recommendation.user_id == user_id, Recommendation.job_id == job_id)
            .first()
        )

    def count(self) -> int:
        return self.session.query(Recommendation).count()
