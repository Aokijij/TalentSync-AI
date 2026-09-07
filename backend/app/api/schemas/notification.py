from datetime import datetime

from pydantic import BaseModel


class NotificationResponse(BaseModel):
    id: int
    type: str
    title: str
    body: str
    action_url: str | None = None
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}
