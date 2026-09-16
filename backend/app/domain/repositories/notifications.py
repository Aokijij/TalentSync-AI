from typing import Protocol

from app.domain.entities.records import Notification
from app.domain.repositories.entity import EntityRepository


class NotificationRepository(EntityRepository[Notification], Protocol):
    def count_unread(self, user_id: int) -> int: ...

    def mark_all_read(self, user_id: int) -> int: ...

    def for_user(self, user_id: int, unread_only: bool) -> list[Notification]: ...

    def find_unread(
        self, user_id: int, notification_type: str, action_url: str
    ) -> Notification | None: ...
