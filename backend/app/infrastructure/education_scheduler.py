"""Daily refresh while the application runs; never discovers/publishes new courses."""
import asyncio
import logging

from app.application.use_cases.learning_sources import refresh_sapiencia, refresh_sena
from app.domain.entities.enums import UserRole
from app.infrastructure.database.models import User
from app.infrastructure.database.session import SessionLocal
from app.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork
from app.infrastructure.public_learning import PublicLearningCatalog

logger = logging.getLogger(__name__)


def refresh_cycle():
    gateway = PublicLearningCatalog()
    with SessionLocal() as session:
        actor = session.query(User).filter_by(role=UserRole.ADMIN).order_by(User.id).first()
        if actor is None:
            return
        db = SqlAlchemyUnitOfWork(session)
        refresh_sena(db, actor, gateway, limit=40, budget_seconds=45)
        refresh_sapiencia(db, actor, gateway)


async def periodic_education(stop_event):
    # Delayed start leaves startup responsive and permits a clean immediate stop.
    try:
        await asyncio.wait_for(stop_event.wait(), timeout=15)
        return
    except TimeoutError:
        pass
    while not stop_event.is_set():
        try:
            await asyncio.to_thread(refresh_cycle)
        except Exception:
            # Provider errors are public, but never log request bodies or user data.
            logger.warning("Educational source refresh could not complete; previous metadata retained")
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=24 * 3600)
        except TimeoutError:
            continue
