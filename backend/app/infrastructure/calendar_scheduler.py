import asyncio
import logging
from datetime import datetime

from app.application.use_cases.calendars import process_event
from app.core.config import settings
from app.infrastructure.database.session import SessionLocal
from app.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork
from app.infrastructure.google_calendar import GoogleCalendar
from app.infrastructure.security.accounts import AccountSecurity

logger = logging.getLogger(__name__)


def cycle():
    gateway = GoogleCalendar(settings)
    if not gateway.configured:
        return
    with SessionLocal() as session:
        db = SqlAlchemyUnitOfWork(session)
        for row in db.calendars.due(datetime.utcnow(), limit=20):
            user = db.users.get(row.user_id)
            if user:
                process_event(db, row, user, gateway, AccountSecurity(), public_app_url=settings.public_app_url)


async def periodic_calendar(stop_event):
    while not stop_event.is_set():
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=30)
        except TimeoutError:
            try:
                await asyncio.to_thread(cycle)
            except Exception:
                logger.warning("Calendar synchronization cycle failed; pending operations remain available")
