import asyncio
import logging

from app.core.config import settings
from app.infrastructure.job_catalogs import (
    AdzunaJobCatalog,
    JSearchJobCatalog,
)

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


def _scheduled_searches():
    keywords = [
        value.strip()
        for value in settings.catalog_sync_keywords.split(",")
        if value.strip()
    ]
    if settings.jsearch_api_key:
        colombia = JSearchJobCatalog(
            api_key=settings.jsearch_api_key,
            base_url=settings.jsearch_api_base_url,
            country="co",
            language="es",
            timeout_seconds=settings.jsearch_timeout_seconds,
        )
        international = JSearchJobCatalog(
            api_key=settings.jsearch_api_key,
            base_url=settings.jsearch_api_base_url,
            country="us",
            language="en",
            timeout_seconds=settings.jsearch_timeout_seconds,
        )
        for value in keywords:
            yield colombia, value, "Colombia"
            yield international, f"remote {value}", "United States"
        return

    adzuna = AdzunaJobCatalog(
        app_id=settings.adzuna_app_id,
        app_key=settings.adzuna_app_key,
        country=settings.adzuna_country,
        base_url=settings.adzuna_api_base_url,
        timeout_seconds=settings.adzuna_timeout_seconds,
    )
    if adzuna.configured:
        for value in keywords:
            yield adzuna, f"remote {value}", "United States"
