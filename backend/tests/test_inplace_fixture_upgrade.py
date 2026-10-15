from collections import Counter

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.api.schemas.job import ScreeningQuestionConfig
from app.api.schemas.job_quality import QualityDetails
from app.domain.services.market_radar import market_report
from app.infrastructure.database.models import Application, EventLog, Job, Profile, User
from app.infrastructure.database.session import Base
from scripts.enrich_realistic import upgrade
from scripts.seed_realistic import seed


def test_upgrade_preserves_processes_and_identity_and_adds_complete_different_offers():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        seed(db, "Isolated-test-password!2026")
        db.commit()
        users_before = [(row.id, row.email, row.password_hash) for row in db.scalars(select(User))]
        processes = [(row.id, row.user_id, row.job_id, row.status, row.pipeline_stage, row.created_at) for row in db.scalars(select(Application))]
        events = db.query(EventLog).count()
        jobs = list(db.scalars(select(Job).order_by(Job.id)))
        protected = jobs[0]
        protected.description = "Oferta modificada por el usuario; conservar contenido y preguntas."
        protected.quality_revision = 2
        first = upgrade(db)
        db.commit()
        assert first["upgraded_jobs"] == 359 and first["added_profiles"] == 168
        assert first["protected_edited_jobs"] == [protected.id]
        assert protected.description.startswith("Oferta modificada")
        assert processes == [(row.id, row.user_id, row.job_id, row.status, row.pipeline_stage, row.created_at) for row in db.scalars(select(Application))]
        assert db.query(EventLog).count() == events
        assert all(db.get(User, key).email == email and db.get(User, key).password_hash == password for key, email, password in users_before)
        upgraded = [job for job in jobs if job.id != protected.id]
        assert len({job.description for job in upgraded}) == 359
        assert set(first["levels"]) == {"entry", "junior", "mid", "senior", "lead"}
        assert first["skills"] > 130
        assert all(QualityDetails(**job.quality_details) for job in upgraded)
        assert all(len(job.application_questions) == 3 for job in upgraded)
        assert all(ScreeningQuestionConfig(**question) for job in upgraded for question in job.application_questions)
        assert all(job.quality_summary["can_publish"] for job in upgraded)
        assert all(job.salary >= 2_000_000 for job in upgraded if job.employment_type == "full_time")
        assert all(application.screening_answers for application in db.scalars(select(Application).where(Application.job_id != protected.id)))
        assert len({job.quality_summary["score"] for job in upgraded}) > 1
        profiles = list(db.scalars(select(Profile)))
        cohorts = Counter(((row.preferences or {}).get("market_participation", {}).get("family"), (row.preferences or {}).get("market_participation", {}).get("level")) for row in profiles)
        assert all(cohorts[("software", level)] >= 24 for level in ("entry", "junior", "mid", "senior", "lead"))
        second = upgrade(db)
        db.commit()
        assert second["upgraded_jobs"] == second["added_profiles"] == second["fixture_applications_enriched"] == 0
        upgraded[0].salary = 1_100_000
        adjusted = upgrade(db)
        assert adjusted["adjusted_salary_floors"] == 1
        assert upgraded[0].salary == 2_000_000 and upgraded[0].quality_details["salary_max"] >= 2_000_000
        assert upgrade(db)["adjusted_salary_floors"] == 0


def test_market_keeps_counts_beyond_twelve_skills_and_allows_arbitrary_salary_filters():
    from test_market_radar import FILTERS, NOW, job, own
    profile = own()
    profile.skills = ["skill 14", "python", "not requested"]
    rows = [job(i, skills=["python", *[f"skill {j}" for j in range(15)]]) for i in range(6)]
    result = market_report(profile, rows, [], [], FILTERS, NOW)
    assert len(result["demand"]["skills"]) == 16
    own_skills = {row["skill"]: row["count"] for row in result["demand"]["own_skills"]}
    assert own_skills == {"python": 6, "skill 14": 6, "not requested": 0}
    assert result["demand"]["own_skills"][-1]["skill"] == "not requested"
    all_areas = market_report(profile, rows, [], [], {**FILTERS, "family": "", "level": "", "location": ""}, NOW)
    assert len(all_areas["salary"]["offers"]) == 6
    assert not all_areas["salary"]["groups"]  # Never pool incompatible roles into a median.
