"""Add three review examples to the owned SQLite database, without replacing data."""
import json
from copy import deepcopy
from pathlib import Path

from app.core.config import settings
from app.domain.services.pipeline import default_stages
from app.infrastructure.database.models import Company, EventLog, Job, OfferFeedback
from app.infrastructure.database.session import SessionLocal
from app.infrastructure.nlp.text_processor import text_processor

ROOT = Path(__file__).resolve().parents[2]
SOURCE = "local-quality-demo"


def main():
    expected = f"sqlite:///{(ROOT / '.local/talentsync.sqlite3').as_posix()}"
    if settings.environment != "development" or settings.database_url != expected:
        raise SystemExit("Los ejemplos requieren la base SQLite local aislada.")
    registry = json.loads((ROOT / ".local/escenarios/accounts.json").read_text(encoding="utf-8"))
    owner = next(row for row in registry["accounts"] if row["key"] == "empresa")
    with SessionLocal() as db:
        company = db.query(Company).filter_by(owner_user_id=owner["id"]).one()
        if company.verification_status != "verified":
            raise SystemExit("La empresa ficticia de revisión debe estar verificada.")
        existing = db.query(Job).filter_by(company_id=company.id, source_name=SOURCE).all()
        if existing:
            jobs = existing
        else:
            details = {"version": 1, "salary_max": 4500000, "variable_pay": "Sin pagos variables en este ejemplo.", "contract_type": "indefinite",
                       "schedule": "Lunes a viernes, 8:00 a 17:00, con una hora de descanso", "seniority": "junior", "experience_years": 0,
                       "learnable_skills": ["power bi"], "missions": [{"outcome": "Preparar un tablero semanal de ventas con sus fuentes documentadas", "measure": "Revisión con el equipo comercial y conciliación con el reporte de origen", "days": 60, "skill": "sql"}],
                       "interview_count": 2, "process_days": 14}
            jobs = []
            for key, label in [("incompleta", "oferta por mejorar"), ("clara", "oferta clara"), ("diagnostico", "diagnóstico con opiniones")]:
                title = f"Analista de datos · {label} (demostración)"
                description = "Analizará reportes de ventas con el equipo comercial, revisará diferencias entre fuentes y preparará un tablero semanal para apoyar las decisiones. Oferta ficticia para revisar TalentSync localmente; no representa contratación real."
                requirements = "Fundamentos de SQL y análisis de datos. Se aceptan proyectos de formación o ejemplos de trabajo como evidencia. La empresa acompaña el aprendizaje de Power BI."
                current = deepcopy(details)
                salary, status = 3500000, "active"
                if key == "incompleta":
                    description = "Buscamos un guerrero dinámico con trabajo bajo presión. Oferta ficticia para revisión local."
                    requirements = "Cargo junior: experiencia mínima de 7 años con SQL. Ejemplo ficticio con contradicciones que deben corregirse."
                    current.update(contract_type="", schedule="", experience_years=7, missions=[], interview_count=None, process_days=None, salary_max=None)
                    salary, status = None, "draft"
                if key == "diagnostico":
                    description += " Buscamos un perfil dinámico."
                analysis = text_processor.analyze_job(f"{title} {description} {requirements}")
                job = Job(company_id=company.id, title=title, description=description, requirements=requirements,
                          salary=salary, location="Colombia", modality="remote", employment_type="full_time", sector="Tecnologia y software",
                          status=status, benefits=["Acompañamiento inicial", "Plan de formación"], languages=[], skills=analysis.skills, embedding=analysis.embedding,
                          skill_requirements=[{"skill": "sql", "essential": True, "weight": 4}, {"skill": "excel", "essential": False, "weight": 2}],
                          quality_details=current, quality_revision=1, response_days=7, blind_hiring=True, pipeline_stages=default_stages(), source_kind="internal", source_name=SOURCE)
                db.add(job)
                db.flush()
                jobs.append(job)
                if key == "diagnostico":
                    candidates = [row for row in registry["accounts"] if row["role"] == "candidate"][:5]
                    for candidate, reason in zip(candidates, ["salary", "salary", "requirements", "requirements", "process"], strict=True):
                        db.add(OfferFeedback(user_id=candidate["id"], job_id=job.id, reason=reason, revision=1))
            db.add(EventLog(event_type="demo.offer_quality_created", entity_type=SOURCE, entity_id=company.id, details={}))
            db.commit()
        output = {"company_id": company.id, "account_key": "empresa", "jobs": [{"id": job.id, "title": job.title, "status": job.status,
                  "review_url": f"http://127.0.0.1:5173/empresa/calidad?vacante={job.id}", "candidate_url": f"http://127.0.0.1:5173/vacantes/{job.id}"} for job in jobs]}
        (ROOT / ".local/quality-offers.json").write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
