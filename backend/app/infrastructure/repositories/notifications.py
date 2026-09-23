from app.infrastructure.database.models import Notification
from app.infrastructure.repositories.entity import SqlAlchemyRepository


class NotificationRepository(SqlAlchemyRepository[Notification]):
    def count_unread(self, user_id: int) -> int:
        return (
            self.session.query(Notification)
            .filter(Notification.user_id == user_id, Notification.is_read.is_(False))
            .count()
        )

    def mark_all_read(self, user_id: int) -> int:
        return (
            self.session.query(Notification)
            .filter(Notification.user_id == user_id, Notification.is_read.is_(False))
            .update({Notification.is_read: True})
        )

    def for_user(
        self,
        user_id: int,
        unread_only: bool,
        category: str | None = None,
        limit: int = 30,
        offset: int = 0,
    ) -> list[Notification]:
        query = self.session.query(Notification).filter(Notification.user_id == user_id)
        if unread_only:
            query = query.filter(Notification.is_read.is_(False))
        application_types = {
            "application_received",
            "application_updated",
            "application_status",
            "application_interview",
            "application_selected",
            "application_not_selected",
        }
        opportunity_types = {"company_job_match", "candidate_invitation"}
        if category == "applications":
            query = query.filter(Notification.type.in_(application_types))
        elif category == "opportunities":
            query = query.filter(Notification.type.in_(opportunity_types))
        elif category == "system":
            query = query.filter(
                Notification.type.notin_(application_types | opportunity_types)
            )
        return (
            query.order_by(Notification.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    def delete_read(self, user_id: int) -> int:
        return (
            self.session.query(Notification)
            .filter(Notification.user_id == user_id, Notification.is_read.is_(True))
            .delete(synchronize_session=False)
        )

    def find_unread(
        self, user_id: int, notification_type: str, action_url: str
    ) -> Notification | None:
        return (
            self.session.query(Notification)
            .filter(
                Notification.user_id == user_id,
                Notification.type == notification_type,
                Notification.action_url == action_url,
                Notification.is_read.is_(False),
            )
            .first()
        )
