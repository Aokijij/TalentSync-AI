from datetime import datetime

from sqlalchemy import or_

from app.infrastructure.database.models import Job, Recommendation
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

    def for_user_active(self, user_id: int) -> list[Recommendation]:
        now = datetime.utcnow()
        return (
            self.session.query(Recommendation)
            .join(Job, Job.id == Recommendation.job_id)
            .filter(
                Recommendation.user_id == user_id,
                Job.status == "active",
                or_(Job.expires_at.is_(None), Job.expires_at >= now),
            )
            .order_by(Recommendation.match_percentage.desc())
            .all()
        )
