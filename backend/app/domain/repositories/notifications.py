from typing import Protocol

from app.domain.entities.records import Notification
from app.domain.repositories.entity import EntityRepository


class NotificationRepository(EntityRepository[Notification], Protocol):
    def count_unread(self, user_id: int) -> int: ...

    def mark_all_read(self, user_id: int) -> int: ...

    def for_user(
        self,
        user_id: int,
        unread_only: bool,
        category: str | None = None,
        limit: int = 30,
        offset: int = 0,
    ) -> list[Notification]: ...

    def delete_read(self, user_id: int) -> int: ...

    def find_unread(
        self, user_id: int, notification_type: str, action_url: str
    ) -> Notification | None: ...
