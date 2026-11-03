import asyncio
import logging
from datetime import datetime, timedelta

from app.application.use_cases.account_data import process_erasure
from app.core.config import settings
from app.infrastructure.database.session import SessionLocal
from app.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork
from app.infrastructure.private_account_files import PrivateAccountFiles


def maintain_accounts():
    with SessionLocal() as session:
        db = SqlAlchemyUnitOfWork(session)
        for task in db.account_data.pending_erasures(datetime.utcnow()):
            process_erasure(db, task, PrivateAccountFiles())
        if settings.account_retention_enabled:
            db.account_data.retain(datetime.utcnow() - timedelta(days=settings.account_retention_days))
            db.commit()


async def periodic_accounts(stop):
    while not stop.is_set():
        try:
            await asyncio.to_thread(maintain_accounts)
        except Exception:
            logging.getLogger(__name__).error("Account maintenance failed; retry scheduled")
        try:
            await asyncio.wait_for(stop.wait(), timeout=60)
        except asyncio.TimeoutError:
            pass
