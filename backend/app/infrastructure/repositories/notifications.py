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

    def for_user(self, user_id: int, unread_only: bool) -> list[Notification]:
        query = self.session.query(Notification).filter(Notification.user_id == user_id)
        if unread_only:
            query = query.filter(Notification.is_read.is_(False))
        return query.order_by(Notification.created_at.desc()).all()
