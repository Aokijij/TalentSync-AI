import asyncio
import logging

from app.application.errors import UseCaseError
from app.application.use_cases.job_imports import sync_job_catalog
from app.application.use_cases.maintenance import maintain_job_catalog
from app.core.config import settings
from app.infrastructure.database.session import SessionLocal
from app.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork
from app.infrastructure.job_catalogs import (
    AdzunaJobCatalog,
    JSearchJobCatalog,
)
from app.infrastructure.nlp.text_processor import text_processor

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
    session = SessionLocal()
    db = SqlAlchemyUnitOfWork(session)
    summary: dict[str, object] = {}
    try:
        summary.update(
            maintain_job_catalog(
                db,
                max_age_days=settings.catalog_max_age_days,
                min_skills=settings.catalog_min_skills,
            )
        )
        admin = db.users.first_admin()
        if admin is None:
            return summary
        imports: list[dict] = []
        for catalog, keywords, location in _scheduled_searches():
            try:
                imports.append(
                    sync_job_catalog(
                        keywords=keywords,
                        location=location,
                        pages=1,
                        result_count=20,
                        current_user=admin,
                        db=db,
                        nlp=text_processor,
                        catalog=catalog,
                    )
                )
            except UseCaseError as error:
                logger.warning(
                    "Catalog sync skipped for %s: %s",
                    catalog.source_name,
                    error.detail,
                )
        summary["imports"] = imports
        return summary
    finally:
        session.close()


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
