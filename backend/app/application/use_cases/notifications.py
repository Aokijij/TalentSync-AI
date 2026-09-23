from app.application.errors import UseCaseError
from app.application.ports.unit_of_work import UnitOfWork
from app.domain.entities.records import Notification, User


def list_notifications(
    unread_only: bool,
    current_user: User,
    db: UnitOfWork,
    category: str | None = None,
    limit: int = 30,
    offset: int = 0,
) -> list[Notification]:
    return db.notifications.for_user(
        current_user.id, unread_only, category, limit, offset
    )


def unread_count(current_user: User, db: UnitOfWork) -> dict[str, int]:
    count = db.notifications.count_unread(current_user.id)
    return {"count": count}


def mark_read(notification_id: int, current_user: User, db: UnitOfWork) -> Notification:
    notification = db.notifications.get(notification_id)
    if notification is None or notification.user_id != current_user.id:
        raise UseCaseError(status_code=404, detail="Notificacion no encontrada")
    notification.is_read = True
    db.commit()
    db.refresh(notification)
    return notification


def mark_all_read(current_user: User, db: UnitOfWork) -> dict[str, bool]:
    db.notifications.mark_all_read(current_user.id)
    db.commit()
    return {"ok": True}


def delete_notification(
    notification_id: int, current_user: User, db: UnitOfWork
) -> None:
    notification = db.notifications.get(notification_id)
    if notification is None or notification.user_id != current_user.id:
        raise UseCaseError(status_code=404, detail="Notificación no encontrada")
    db.delete(notification)
    db.commit()


def delete_read(current_user: User, db: UnitOfWork) -> dict[str, int]:
    deleted = db.notifications.delete_read(current_user.id)
    db.commit()
    return {"deleted": deleted}
