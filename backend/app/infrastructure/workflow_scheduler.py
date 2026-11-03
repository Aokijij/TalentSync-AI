import asyncio
import logging

from app.application.use_cases.workflow import deadline_cycle
from app.infrastructure.database.session import SessionLocal
from app.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork

logger = logging.getLogger(__name__)


def run_workflow_cycle():
    with SessionLocal() as session:
        return deadline_cycle(SqlAlchemyUnitOfWork(session))


async def periodic_workflow(stop_event):
    while not stop_event.is_set():
        try:
            await asyncio.to_thread(run_workflow_cycle)
        except Exception:
            logger.exception("Workflow deadline cycle failed")
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=60)
        except TimeoutError:
            pass
