from datetime import datetime

from sqlalchemy import and_
from sqlalchemy.orm import joinedload

from app.domain.entities.enums import ApplicationStatus
from app.infrastructure.database.models import Application, Job, Recommendation
from app.infrastructure.repositories.entity import SqlAlchemyRepository


class ApplicationRepository(SqlAlchemyRepository[Application]):
    def count(self) -> int:
        return self.session.query(Application).count()

    def creation_dates(self) -> list[datetime]:
        return [
            created_at
            for (created_at,) in self.session.query(Application.created_at).all()
        ]

    def status_rows(self) -> list[tuple[ApplicationStatus]]:
        return self.session.query(Application.status).all()

    def count_recommended(self) -> int:
        return (
            self.session.query(Application)
            .join(
                Recommendation,
                and_(
                    Recommendation.user_id == Application.user_id,
                    Recommendation.job_id == Application.job_id,
                ),
            )
            .count()
        )

    def find_for_user_job(self, user_id: int, job_id: int) -> Application | None:
        return (
            self.session.query(Application)
            .filter(Application.user_id == user_id, Application.job_id == job_id)
            .first()
        )

    def for_user(self, user_id: int) -> list[Application]:
        return (
            self.session.query(Application)
            .filter(Application.user_id == user_id)
            .order_by(Application.created_at.desc())
            .all()
        )

    def for_job(self, job_id: int) -> list[Application]:
        return (
            self.session.query(Application)
            .options(joinedload(Application.user))
            .filter(Application.job_id == job_id)
            .all()
        )

    def mark_submitted_seen(self, job_id: int) -> int:
        return (
            self.session.query(Application)
            .filter(
                Application.job_id == job_id,
                Application.status == ApplicationStatus.SUBMITTED,
            )
            .update(
                {Application.status: ApplicationStatus.SEEN}, synchronize_session=False
            )
        )

    def find_for_candidate_company(
        self, candidate_id: int, company_id: int
    ) -> Application | None:
        return (
            self.session.query(Application)
            .join(Job, Application.job_id == Job.id)
            .filter(Application.user_id == candidate_id, Job.company_id == company_id)
            .first()
        )

    def candidate_ids(self, job_id: int) -> list[tuple[int]]:
        return (
            self.session.query(Application.user_id)
            .filter(Application.job_id == job_id)
            .all()
        )
