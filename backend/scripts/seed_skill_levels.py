"""Add varied proficiency declarations only to isolated recruiting fixtures."""
import json
import sqlite3
from datetime import datetime
from pathlib import Path

from sqlalchemy import select

from app.domain.services.skills import skill_key
from app.infrastructure.database.models import Job, Profile


def populate(db):
    profiles = jobs = 0
    levels = ["basic", "intermediate", "advanced", "expert"]
    for profile in db.scalars(select(Profile)):
        prefs = profile.preferences or {}
        if not prefs.get("local_fixture") or "skill_levels" in prefs:
            continue
        profile.preferences = {**prefs, "skill_levels": {skill_key(skill): levels[(profile.user_id + index) % len(levels)] for index, skill in enumerate(profile.skills or [])}}
        profiles += 1
    for job in db.scalars(select(Job).where(Job.source_name == "local-realistic")):
        if (job.quality_revision or 0) > 2 or not (job.external_id or "").endswith("-v2"):
            continue
        requirements = job.skill_requirements or []
        if not requirements or any("level" in row for row in requirements):
            continue
        seniority = (job.quality_details or {}).get("seniority")
        level = "advanced" if seniority in {"senior", "lead"} else "intermediate" if seniority == "mid" else "basic"
        job.skill_requirements = [{**row, "level": level if row.get("essential") else "basic"} for row in requirements]
        job.quality_revision = (job.quality_revision or 0) + 1
        jobs += 1
    return {"profiles_with_declared_levels": profiles, "jobs_with_minimum_levels": jobs}


def main():
    from app.core.config import settings
    from app.infrastructure.database.session import SessionLocal
    root = Path(__file__).resolve().parents[2]
    target = root / ".local/talentsync.sqlite3"
    if settings.environment != "development" or settings.database_url != f"sqlite:///{target.as_posix()}":
        raise SystemExit("This update requires the isolated development database.")
    backup = root / f".local/backups/before-skill-levels-{datetime.now():%Y%m%d-%H%M%S}.sqlite3"
    backup.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(target) as source, sqlite3.connect(backup) as destination:
        source.backup(destination)
    with SessionLocal() as db:
        report = populate(db)
        db.commit()
    report["backup"] = str(backup)
    (root / ".local/verification/skill-levels-fixtures.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
