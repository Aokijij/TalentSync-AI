from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_current_user, get_unit_of_work
from app.api.schemas.notification import NotificationResponse
from app.application.ports.unit_of_work import UnitOfWork
from app.application.use_cases import notifications as use_cases
from app.domain.entities.records import Notification, User

router = APIRouter()


@router.get("", response_model=list[NotificationResponse])
def list_notifications(
    unread_only: bool = Query(default=True),
    category: str | None = Query(default=None, pattern="^(applications|opportunities|system)$"),
    limit: int = Query(default=30, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: UnitOfWork = Depends(get_unit_of_work),
) -> list[Notification]:
    return use_cases.list_notifications(
        unread_only=unread_only,
        category=category,
        limit=limit,
        offset=offset,
        current_user=current_user,
        db=db,
    )


@router.get("/unread-count")
def unread_count(
    current_user: User = Depends(get_current_user),
    db: UnitOfWork = Depends(get_unit_of_work),
) -> dict[str, int]:
    return use_cases.unread_count(current_user=current_user, db=db)


@router.put("/{notification_id}/read", response_model=NotificationResponse)
def mark_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: UnitOfWork = Depends(get_unit_of_work),
) -> Notification:
    return use_cases.mark_read(
        notification_id=notification_id, current_user=current_user, db=db
    )


@router.put("/read-all")
def mark_all_read(
    current_user: User = Depends(get_current_user),
    db: UnitOfWork = Depends(get_unit_of_work),
) -> dict[str, bool]:
    return use_cases.mark_all_read(current_user=current_user, db=db)


@router.delete("/read")
def delete_read(
    current_user: User = Depends(get_current_user),
    db: UnitOfWork = Depends(get_unit_of_work),
) -> dict[str, int]:
    return use_cases.delete_read(current_user=current_user, db=db)


@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_notification(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: UnitOfWork = Depends(get_unit_of_work),
) -> None:
    return use_cases.delete_notification(notification_id, current_user, db)
