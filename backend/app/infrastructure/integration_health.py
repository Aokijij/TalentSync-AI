"""Automatic connection checks without messages, events or interactive sign-ins."""
import asyncio
import logging
from datetime import datetime

import httpx

from app.core.config import settings
from app.infrastructure.database.models import CalendarConnection
from app.infrastructure.database.session import SessionLocal
from app.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork
from app.infrastructure.google_calendar import GoogleCalendar
from app.infrastructure.security.accounts import AccountSecurity
from app.infrastructure.security.gmail import GmailDelivery

logger = logging.getLogger(__name__)


def cycle():
    now = datetime.utcnow()
    rows = []
    with SessionLocal() as session, httpx.Client(timeout=12, follow_redirects=False, trust_env=False) as client:
        db = SqlAlchemyUnitOfWork(session)

        def check(provider, method, operation):
            try:
                operation()
                state, error = "available", ""
            except Exception:
                state, error = "error", "No se pudo completar la comprobación automática de esta conexión."
            rows.append({"provider": provider, "state": state, "method": method, "checked_at": now.isoformat() + "Z", "error": error})

        def public(url):
            with client.stream("GET", url) as response:
                response.raise_for_status()

        if settings.gmail_mail_enabled:
            check("mail", "credentials_refresh", lambda: GmailDelivery(settings)._access(client))
        calendar = GoogleCalendar(settings)
        if calendar.configured:
            connection = session.query(CalendarConnection).filter(CalendarConnection.refresh_cipher != "").first()
            if connection:
                def refresh_calendar():
                    security = AccountSecurity()
                    _, rotated = calendar.refresh(security.decrypt_secret(connection.refresh_cipher))
                    if rotated:
                        connection.refresh_cipher = security.encrypt_secret(rotated)
                check("calendar", "credentials_refresh", refresh_calendar)
            else:
                check("calendar", "provider_metadata", lambda: public("https://accounts.google.com/.well-known/openid-configuration"))
        for key, configured, url in [
            ("social_google", settings.oauth_google_client_id, "https://accounts.google.com/.well-known/openid-configuration"),
            ("social_github", settings.oauth_github_client_id, "https://api.github.com/meta"),
            ("social_linkedin", settings.oauth_linkedin_client_id, "https://www.linkedin.com/oauth/.well-known/openid-configuration"),
        ]:
            if configured:
                check(key, "provider_metadata", lambda url=url: public(url))
        if settings.youtube_learning_enabled and settings.youtube_api_key:
            def youtube():
                with client.stream("GET", "https://www.googleapis.com/youtube/v3/i18nLanguages", params={"part": "snippet", "key": settings.youtube_api_key}) as response:
                    response.raise_for_status()
            check("youtube", "source_api", youtube)
        snapshot = db.learning.source_snapshot("integration-health")
        if snapshot is None:
            snapshot = db.learning.new_source_snapshot(id="integration-health", content=rows)
            db.add(snapshot)
        snapshot.content, snapshot.fetched_at, snapshot.attempted_at, snapshot.error = rows, now, now, ""
        db.commit()
    return rows


async def periodic_integration_health(stop_event):
    try:
        await asyncio.wait_for(stop_event.wait(), timeout=45)
        return
    except TimeoutError:
        pass
    while not stop_event.is_set():
        try:
            await asyncio.to_thread(cycle)
        except Exception:
            logger.warning("Connection health check interrupted; the next cycle will retry")
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=6 * 3600)
        except TimeoutError:
            continue
