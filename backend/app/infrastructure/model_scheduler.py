import asyncio
import logging

from app.application.use_cases.personalization import train
from app.infrastructure.database.session import SessionLocal
from app.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork
from app.infrastructure.nlp.interest_trainer import InterestTrainer
from app.infrastructure.nlp.text_processor import text_processor

logger = logging.getLogger(__name__)


def run_model_cycle():
    with SessionLocal() as session:
        return train(SqlAlchemyUnitOfWork(session), text_processor, InterestTrainer(), scheduled=True)


async def periodic_models(stop_event):
    # Revisit hourly; train at most daily, only when real consented data is enough.
    while not stop_event.is_set():
        try:
            await asyncio.to_thread(run_model_cycle)
        except Exception:
            logger.exception("Local model evaluation failed")
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=3600)
        except TimeoutError:
            pass
