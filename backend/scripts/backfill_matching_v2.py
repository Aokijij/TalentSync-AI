"""Backfill explicit education signals and remove legacy automatic answer scores."""

import json

from app.domain.services.professions import infer_education_level, infer_study_fields, normalize
from app.infrastructure.database.models import Application, Job
from app.infrastructure.database.session import SessionLocal


def run() -> dict[str, int]:
    with SessionLocal() as session:
        colombian_departments = {normalize(item) for item in ("Amazonas", "Antioquia", "Arauca", "Atlántico", "Bogotá D.C.", "Bolívar", "Boyacá", "Caldas", "Caquetá", "Casanare", "Cauca", "Cesar", "Chocó", "Córdoba", "Cundinamarca", "Guainía", "Guaviare", "Huila", "La Guajira", "Magdalena", "Meta", "Nariño", "Norte de Santander", "Putumayo", "Quindío", "Risaralda", "San Andrés y Providencia", "Santander", "Sucre", "Tolima", "Valle del Cauca", "Vaupés", "Vichada")}
        jobs_updated = 0
        for job in session.query(Job).all():
            text = f"{job.title} {job.requirements}"
            level = job.required_education_level or infer_education_level(text)
            fields = job.required_study_fields or infer_study_fields(text)
            if level != job.required_education_level or fields != (job.required_study_fields or []):
                job.required_education_level = level
                job.required_study_fields = fields
                jobs_updated += 1
            if job.source_kind == "external" and job.modality == "remote" and job.department and normalize(job.department) not in colombian_departments and normalize(job.department) != "remoto internacional":
                job.department = "Remoto internacional"
                jobs_updated += 1
        applications_updated = 0
        for application in session.query(Application).all():
            manual = sum(float(item.get("reviewer_adjustment", 0) or 0) for item in (application.screening_answers or []))
            manual = max(-20.0, min(20.0, manual))
            if float(application.screening_adjustment or 0) != manual:
                application.screening_adjustment = manual
                applications_updated += 1
        session.commit()
        return {"jobs_updated": jobs_updated, "applications_updated": applications_updated}


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False))
