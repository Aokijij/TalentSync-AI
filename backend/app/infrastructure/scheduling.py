import asyncio
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


async def periodic_maintenance(stop_event: asyncio.Event) -> None:
    try:
        await asyncio.wait_for(
            stop_event.wait(),
            timeout=settings.periodic_maintenance_initial_delay_seconds,
        )
        return
    except TimeoutError:
        pass

    while not stop_event.is_set():
        try:
            await asyncio.to_thread(run_maintenance_cycle)
        except Exception:
            logger.exception("TalentSync periodic maintenance failed")
        try:
            await asyncio.wait_for(
                stop_event.wait(),
                timeout=settings.periodic_maintenance_interval_hours * 3_600,
            )
        except TimeoutError:
            continue


def run_maintenance_cycle() -> dict:
    from app.infrastructure.catalog_refresh import catalog_refresh
    return catalog_refresh.start(location="Colombia")
