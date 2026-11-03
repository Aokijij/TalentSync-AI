import asyncio
import logging

from app.application.use_cases.job_availability import check_due
from app.infrastructure.database.session import SessionLocal
from app.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork
from app.infrastructure.job_availability import JobAvailability

logger = logging.getLogger(__name__)


def cycle():
    with SessionLocal() as session:
        return check_due(SqlAlchemyUnitOfWork(session), JobAvailability())


async def periodic_vacancy_checks(stop_event):
    while not stop_event.is_set():
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=300)
        except TimeoutError:
            try:
                await asyncio.to_thread(cycle)
            except Exception:
                # No job URLs or private response bodies in logs.
                logger.warning("External vacancy checks could not finish; pending checks retained")
