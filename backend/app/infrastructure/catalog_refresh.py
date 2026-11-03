"""Background catalogue refresh, with progress and current source evidence."""
import threading
from collections import Counter
from datetime import datetime, timedelta

from app.application.errors import UseCaseError
from app.application.use_cases.job_imports import sync_job_catalog
from app.application.use_cases.maintenance import maintain_job_catalog
from app.core.config import settings
from app.domain.entities.catalog import CatalogPage
from app.domain.services.external_job_content import extract_content
from app.infrastructure.database.session import SessionLocal
from app.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork
from app.infrastructure.job_availability import JobAvailability, ats_reference
from app.infrastructure.job_catalogs.ats import EmployerBoardCatalog
from app.infrastructure.job_catalogs.getonboard import GetOnBoardCatalog
from app.infrastructure.job_catalogs.jsearch import JSearchJobCatalog
from app.infrastructure.nlp.text_processor import text_processor

KEY = "external-catalog-refresh"


class SourceFeed:
    configured = True

    def __init__(self, name, jobs):
        self.source_name, self.jobs = name, jobs

    def search(self, **kwargs):
        return CatalogPage(jobs=self.jobs, total=len(self.jobs))


class CatalogRefreshService:
    def __init__(self):
        self.lock = threading.Lock()
        self.thread = None

    def status(self):
        from app.domain.services.job_freshness import externally_available
        with SessionLocal() as session:
            db = SqlAlchemyUnitOfWork(session)
            snapshot = db.learning.source_snapshot(KEY)
            jobs = db.jobs.external_listings()
            counts = Counter("active" if job.status == "active" and externally_available(job) else "closed" if job.status == "closed" else "review" for job in jobs)
            return {"run": snapshot.content[0] if snapshot and snapshot.content else {"state": "idle"},
                    "total": len(jobs), "active": counts["active"], "review": counts["review"], "closed": counts["closed"], "target": settings.catalog_target_active}

    def start(self, keywords="", location="Colombia"):
        with self.lock:
            if self.thread is None or not self.thread.is_alive():
                self.thread = threading.Thread(target=self._run, args=(keywords, location), daemon=True, name="catalog-refresh")
                self.thread.start()
        return {"state": "running", "message": "La sincronización continúa en segundo plano. Puedes seguir usando la plataforma."}

    @staticmethod
    def _save(db, progress):
        now = datetime.utcnow()
        snapshot = db.learning.source_snapshot(KEY)
        if snapshot is None:
            snapshot = db.learning.new_source_snapshot(id=KEY, content=[])
            db.add(snapshot)
        snapshot.content = [{**progress, "updated_at": now.isoformat() + "Z"}]
        snapshot.fetched_at = snapshot.attempted_at = now
        snapshot.error = ""
        db.commit()

    def _run(self, keywords, location):
        progress = {"state": "running", "started_at": datetime.utcnow().isoformat() + "Z", "source": "Preparando catálogo", "created": 0, "updated": 0, "rejected": 0, "sources_checked": 0, "errors": []}
        with SessionLocal() as session:
            db = SqlAlchemyUnitOfWork(session)
            try:
                self._save(db, progress)
                admin = db.users.first_admin()
                if admin is None:
                    raise ValueError("Administrator required")
                maintain_job_catalog(db)
                # Re-evaluate source facts with the current policy. A recent
                # source check is still required before making a role visible.
                jobs = db.jobs.external_listings()
                for job in jobs:
                    content, details, _, _ = extract_content(job.title, job.description, job.requirements, published_at=job.external_published_at)
                    job.external_content = {**(job.external_content or {}), **content}
                    job.quality_details = {**(job.quality_details or {}), **details}
                db.commit()
                boards = set()
                boards.update({"https://job-boards.greenhouse.io/agencywithin", "https://job-boards.greenhouse.io/goodsservices"})
                boards.update({"https://jobs.ashbyhq.com/addi", "https://jobs.ashbyhq.com/nubank"})
                for job in jobs:
                    try:
                        reference = ats_reference(job.external_url)
                    except ValueError:
                        continue
                    if reference:
                        provider, board, _ = reference
                        boards.add(("https://job-boards.greenhouse.io/" if provider == "greenhouse" else "https://jobs.eu.lever.co/" if provider == "lever_eu" else "https://jobs.lever.co/") + board)

                def ingest(catalog, found, *, direct):
                    if not found:
                        return
                    result = sync_job_catalog(keywords="", location=location, pages=1, result_count=100,
                        current_user=admin, db=db, nlp=text_processor, catalog=SourceFeed(catalog.source_name, found))
                    for name in ("created", "updated", "rejected"):
                        progress[name] += result.get(name, 0)
                    for source_job in found:
                        saved = db.jobs.find_external(catalog.source_name, source_job.external_id)
                        if saved is None:
                            continue
                        # A provider response confirms the ATS feeds directly.
                        # Aggregators require a check of the actual destination.
                        check = None if direct else JobAvailability().check(saved.external_url)
                        state = "verified" if direct else check.state
                        saved.external_checked_at = datetime.utcnow()
                        saved.external_check_state = state
                        saved.external_check_reason = "source_api" if direct else check.reason
                        saved.external_next_check_at = datetime.utcnow() + timedelta(hours=24 if state == "verified" else 6)
                        if state == "verified":
                            saved.external_verified_at = datetime.utcnow()
                            if not saved.external_admission_reasons and (not saved.expires_at or saved.expires_at > datetime.utcnow()):
                                saved.status = "active"
                        elif state == "closed":
                            saved.status = "closed"
                    db.commit()

                def run_source(name, operation):
                    progress["source"] = name
                    self._save(db, progress)
                    try:
                        operation()
                    except UseCaseError as failure:
                        session.rollback()
                        details = failure.detail if isinstance(failure.detail, dict) else {}
                        if failure.status_code == 422 and details.get("errors"):
                            progress["rejected"] += len(details["errors"])
                        else:
                            progress["errors"].append({"source": name, "message": "La consulta necesita un reintento. Se conserva lo anterior."})
                    except Exception:
                        session.rollback()
                        progress["errors"].append({"source": name, "message": "La fuente no pudo completar esta consulta. Se conserva lo anterior."})
                    progress["sources_checked"] += 1
                    self._save(db, progress)

                # Colombian portals are discovered through the configured API;
                # employer feeds retain all their original structured sections.
                if settings.jsearch_api_key:
                    catalog = JSearchJobCatalog(api_key=settings.jsearch_api_key, base_url=settings.jsearch_api_base_url, country="co", language="es", timeout_seconds=20)
                    queries = [part.strip() for part in (keywords or settings.catalog_sync_keywords).split(",") if part.strip()][:4]
                    for query in queries:
                        for page in (1, 2):
                            run_source("JSearch · " + query, lambda query=query, page=page: ingest(catalog, catalog.search(keywords=query, location=location, page=page, result_count=100).jobs, direct=False))
                for board_url in sorted(boards):
                    catalog = EmployerBoardCatalog(board_url)
                    run_source(catalog.source_name + " · " + catalog.board, lambda catalog=catalog: ingest(catalog, catalog.preview(location=location)[0], direct=True))
                catalog = GetOnBoardCatalog()
                for market, page in [("Colombia", 1), ("Colombia", 2), ("Bogota", 1), ("Medellin", 1), ("LATAM", 1), ("Remote", 1)]:
                    run_source("Get on Board · " + market, lambda market=market, page=page: ingest(catalog, catalog.search(location=market, page=page, result_count=100).jobs, direct=True))
                progress.update(state="completed", source="Sincronización terminada", finished_at=datetime.utcnow().isoformat() + "Z")
                self._save(db, progress)
            except Exception:
                session.rollback()
                progress.update(state="failed", source="La sincronización no pudo completarse")
                self._save(db, progress)


catalog_refresh = CatalogRefreshService()
