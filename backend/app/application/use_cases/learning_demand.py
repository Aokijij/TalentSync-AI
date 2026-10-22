from collections import Counter, defaultdict
from datetime import datetime

from app.application.use_cases.learning_resources import resources
from app.domain.services.match_explanations import requirements_for
from app.domain.services.skills import skill_key, skill_set


def report(db):
    now = datetime.utcnow()
    jobs = [job for job in db.jobs.active() if not job.expires_at or job.expires_at > now]
    demand, companies = Counter(), defaultdict(set)
    for job in jobs:
        for key in {skill_key(row["skill"]) for row in requirements_for(job)}:
            demand[key] += 1
            if job.company_id is not None:
                companies[key].add(job.company_id)
    catalog = resources(db, include_inactive=True)
    skills = []
    for key, count in demand.most_common(100):
        related = [row for row in catalog if key in skill_set(row.get("skills", []))]
        skills.append({"skill": key, "vacancies": count, "companies": len(companies[key]), "resources": len(related), "published_resources": sum(row.get("active", True) for row in related)})
    return {"vacancy_sample": len(jobs), "skills": skills, "notice": "Requisitos de vacantes activas de TalentSync. Cada habilidad cuenta una vez por vacante; no representa todo el mercado laboral."}
