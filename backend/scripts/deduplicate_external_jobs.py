"""Pause repeated external listings while preserving the richest visible record."""

import json
from collections import defaultdict
from datetime import datetime

from sqlalchemy.orm import joinedload

from app.application.use_cases.job_imports import listing_fingerprint
from app.infrastructure.database.models import Job
from app.infrastructure.database.session import SessionLocal


def deduplicate() -> dict[str, int]:
    with SessionLocal() as session:
        jobs = (
            session.query(Job)
            .options(joinedload(Job.company))
            .filter(Job.source_kind == "external", Job.status == "active")
            .all()
        )
        groups: dict[tuple[str, str, str, str], list[Job]] = defaultdict(list)
        for job in jobs:
            groups[
                listing_fingerprint(
                    job.company.name if job.company else "",
                    job.title,
                    job.location,
                    job.department,
                )
            ].append(job)

        paused = 0
        duplicate_groups = 0
        now = datetime.utcnow()
        for matches in groups.values():
            if len(matches) < 2:
                continue
            duplicate_groups += 1
            matches.sort(
                key=lambda item: (
                    len(item.skills or []),
                    len(item.description or ""),
                    item.created_at,
                    item.id,
                ),
                reverse=True,
            )
            for duplicate in matches[1:]:
                duplicate.status = "paused"
                duplicate.expires_at = now
                paused += 1
        session.commit()
        return {
            "active_reviewed": len(jobs),
            "duplicate_groups": duplicate_groups,
            "paused": paused,
        }


if __name__ == "__main__":
    print(json.dumps(deduplicate(), ensure_ascii=False))
