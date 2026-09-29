"""Normalize salaries/titles and close duplicate active JSearch listings."""

import json
from collections import defaultdict

from app.infrastructure.database.models import Job
from app.infrastructure.database.session import SessionLocal
from app.infrastructure.job_catalogs.jsearch import (
    _extract_colombian_salary,
    _title_without_salary,
)


def normalize_catalog() -> dict[str, int]:
    titles_updated = salaries_updated = duplicates_closed = 0
    with SessionLocal() as session:
        jobs = (
            session.query(Job)
            .filter(Job.source_name == "JSearch")
            .order_by(Job.id.asc())
            .all()
        )
        groups: dict[tuple[int, str, str], list[Job]] = defaultdict(list)
        for job in jobs:
            original_title = job.title
            clean_title = _title_without_salary(original_title)
            inferred_salary = _extract_colombian_salary(
                f"{original_title} {job.description or ''}"
            )
            if clean_title != original_title:
                job.title = clean_title
                titles_updated += 1
            if job.salary is None and inferred_salary is not None:
                job.salary = inferred_salary
                salaries_updated += 1
            key = (
                job.company_id,
                clean_title.casefold(),
                (job.location or "").strip().casefold(),
            )
            groups[key].append(job)

        for duplicates in groups.values():
            active = [job for job in duplicates if job.status == "active"]
            if len(active) < 2:
                continue
            keep = max(
                active,
                key=lambda job: (
                    len(job.description or "") + len(job.requirements or ""),
                    job.last_seen_at or job.created_at,
                    job.id,
                ),
            )
            for job in active:
                if job.id != keep.id:
                    job.status = "closed"
                    duplicates_closed += 1
        session.commit()
    return {
        "jsearch_jobs": len(jobs),
        "titles_updated": titles_updated,
        "salaries_updated": salaries_updated,
        "duplicates_closed": duplicates_closed,
    }


if __name__ == "__main__":
    print(json.dumps(normalize_catalog(), ensure_ascii=False))
