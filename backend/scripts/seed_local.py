"""Small fictional fixture. Refuses any database outside the isolated workspace."""
import json
import secrets
import zipfile
from datetime import datetime
from pathlib import Path

from app.application.use_cases.interviews import create as create_interview
from app.core.config import settings
from app.domain.entities.enums import ApplicationStatus, UserRole
from app.infrastructure.database.models import Application, Company, Job, Profile, User
from app.infrastructure.database.session import SessionLocal
from app.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork
from app.infrastructure.nlp.text_processor import text_processor
from app.infrastructure.security.passwords import hash_password

ROOT = Path(__file__).resolve().parents[2]


def main():
    expected = f"sqlite:///{(ROOT / '.local/talentsync.sqlite3').as_posix()}"
    if settings.environment != "development" or settings.database_url != expected:
        raise SystemExit("Esta semilla solo admite la base SQLite aislada de .local/.")
    accounts_file = ROOT / ".local/accounts.json"
    accounts = json.loads(accounts_file.read_text(encoding="utf-8")) if accounts_file.exists() else [
        {"role": role, "email": f"{role}@talentsync.example.com", "password": secrets.token_urlsafe(18)}
        for role in ("candidate", "company", "admin")
    ]
    with SessionLocal() as db:
        users = {}
        for account in accounts:
            user = db.query(User).filter_by(email=account["email"]).first()
            # EmailStr rejects special-use .test domains. Preserve seeded
            # accounts and passwords when moving to reserved example.com.
            if account["email"].endswith("@talentsync.test"):
                account["email"] = account["email"].replace("@talentsync.test", "@talentsync.example.com")
                if user is not None:
                    user.email = account["email"]
            if user is None:
                user = User(name={"candidate": "Alex Ejemplo", "company": "Equipo Nexo", "admin": "Administración Local"}[account["role"]],
                            email=account["email"], role=UserRole(account["role"]), password_hash=hash_password(account["password"]))
                user.profile = Profile(profession="Desarrollador de software" if account["role"] == "candidate" else None,
                                       skills=["python", "sql", "git"] if account["role"] == "candidate" else [],
                                       preferred_modality="remote", desired_salary=4_000_000,
                                       embedding=text_processor.embed("desarrollo de software python sql git"))
                db.add(user)
                db.flush()
            users[account["role"]] = user
        company = db.query(Company).filter_by(nit="LOCAL-FICTICIA-001").first()
        if company is None:
            company = Company(owner_user_id=users["company"].id, name="Nexo Laboratorio (ficticia)", nit="LOCAL-FICTICIA-001",
                              description="Organización ficticia para pruebas locales.", sector="Tecnologia y software")
            db.add(company)
            db.flush()
        if not db.query(Job).filter_by(company_id=company.id).first():
            for title, skills, salary in [("Desarrollador Python", ["python", "sql", "fastapi"], 5_000_000),
                                         ("Analista de datos", ["sql", "excel", "power bi"], 4_000_000),
                                         ("Desarrollador Java", ["java", "spring boot", "microservicios"], 6_000_000)]:
                job = Job(company_id=company.id, title=title, description=f"Construye soluciones con {', '.join(skills)}.",
                          requirements=f"Experiencia práctica en {', '.join(skills)}.", skills=skills,
                          salary=salary, modality="remote", sector="Tecnologia y software",
                          pipeline_stages=[{"id": value, "title": label} for value, label in
                                           [("submitted", "Recibidas"), ("reviewing", "En revisión"), ("interview", "Entrevista"), ("hired", "Seleccionado"), ("rejected", "No seleccionado")]],
                          embedding=text_processor.embed(f"{title} {' '.join(skills)}"))
                db.add(job)
                db.flush()
                if title == "Desarrollador Python":
                    db.add(Application(user_id=users["candidate"].id, job_id=job.id, pipeline_stage="submitted"))
        db.commit()
        demo_job = db.query(Job).filter_by(company_id=company.id, title="Desarrollador Java").first()
        if demo_job:
            demo = db.query(Application).filter_by(user_id=users["candidate"].id, job_id=demo_job.id).first()
            if demo is None:
                demo = Application(user_id=users["candidate"].id, job_id=demo_job.id,
                    status=ApplicationStatus.TECHNICAL_INTERVIEW, pipeline_stage="interview", identity_revealed_at=datetime.utcnow())
                db.add(demo)
                db.commit()
                create_interview(SqlAlchemyUnitOfWork(db), users["company"], demo.id, "Entrevista de demostración local")
    accounts_file.write_text(json.dumps(accounts, ensure_ascii=False, indent=2), encoding="utf-8")
    demo_zip = ROOT / ".local/demo-project.zip"
    if not demo_zip.exists():
        with zipfile.ZipFile(demo_zip, "x", compression=zipfile.ZIP_STORED) as project:
            project.writestr("demo/requirements.txt", "fastapi\npytest\n")
            project.writestr("demo/src/api.py", "# Proyecto ficticio para demostrar el análisis estático.\ndef health():\n    return {'status': 'demo'}\n")
            project.writestr("demo/package.json", json.dumps({"devDependencies": {"typescript": "*"}}))
            project.writestr("demo/web/main.ts", "// Archivo ficticio de demostración; no se ejecuta.\n")
    print("Datos ficticios preparados sin duplicados. Credenciales: scripts/local.py accounts")
    print("ZIP ficticio para probar Compatibilidad: .local/demo-project.zip")


if __name__ == "__main__":
    main()
