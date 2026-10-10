import asyncio
import logging

from app.application.use_cases.mail_delivery import deliver_outbox
from app.core.config import settings
from app.infrastructure.database.session import SessionLocal
from app.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork
from app.infrastructure.security.resend import ResendDelivery
from app.infrastructure.security.smtp import SmtpDelivery

logger = logging.getLogger(__name__)


def run_mail_cycle():
    with SessionLocal() as session:
        gateway = ResendDelivery(settings) if settings.resend_enabled else SmtpDelivery(settings)
        return deliver_outbox(SqlAlchemyUnitOfWork(session), gateway)


async def periodic_mail(stop_event):
    while not stop_event.is_set():
        try:
            await asyncio.to_thread(run_mail_cycle)
        except Exception:
            # SMTP/SQL exceptions can contain recipient addresses, tokens or credentials.
            logger.warning("Mail cycle failed; delivery leases will expire before retry")
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=30)
        except TimeoutError:
            pass
