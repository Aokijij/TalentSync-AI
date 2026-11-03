"""Additional fictional local accounts. Never replaces existing users or passwords."""
import json
import secrets
from pathlib import Path

from app.core.config import settings
from app.domain.entities.enums import UserRole
from app.infrastructure.database.models import Application, Company, Job, Profile, User
from app.infrastructure.database.session import SessionLocal
from app.infrastructure.nlp.text_processor import text_processor
from app.infrastructure.security.passwords import hash_password

ROOT = Path(__file__).resolve().parents[2]
CANDIDATES = [
    ("ventas", "Valentina · revisión local", "Asesora comercial", ["comunicacion", "servicio al cliente"], "Ventas y comercio"),
    ("finanzas", "Felipe · revisión local", "Auxiliar contable", ["excel", "contabilidad"], "Contabilidad y finanzas"),
    ("logistica", "Laura · revisión local", "Auxiliar de logística", ["inventarios", "organizacion"], "Logística y operaciones"),
    ("salud", "Sofía · revisión local", "Auxiliar administrativa en salud", ["servicio al cliente", "gestion documental"], "Salud: atención y procesos"),
]
COMPANIES = [
    ("comercio", "Comercio Aurora (ficticia)", "Ventas y comercio", [("Asesor de ventas consultivas", ["ventas", "comunicacion"], 2800000, "hybrid"), ("Auxiliar de servicio al cliente", ["servicio al cliente", "comunicacion"], 2200000, "remote")]),
    ("operaciones", "Ruta Clara (ficticia)", "Logistica y transporte", [("Auxiliar de inventarios", ["inventarios", "organizacion"], 2400000, "onsite"), ("Auxiliar contable", ["contabilidad", "conciliacion bancaria", "excel"], 3000000, "hybrid")]),
    ("bienestar", "Bienestar Horizonte (ficticia)", "Salud y bienestar", [("Auxiliar de atención administrativa", ["confidencialidad", "servicio al cliente"], 2600000, "onsite"), ("Asistente de gestión documental", ["gestion documental", "organizacion"], 2500000, "hybrid")]),
]


def main():
    expected = f"sqlite:///{(ROOT / '.local/talentsync.sqlite3').as_posix()}"
    if settings.environment != "development" or settings.database_url != expected:
        raise SystemExit("Solo admite la base SQLite aislada de .local/.")
    file = ROOT / ".local/review-accounts.json"
    saved = json.loads(file.read_text(encoding="utf-8")) if file.exists() else []
    by_email = {row["email"]: row for row in saved}
    with SessionLocal() as db:
        def account(key, role, name, profession=None, skills=None):
            email = f"revision.{key}@example.com"
            user = db.query(User).filter_by(email=email).first()
            if user is None:
                password = "Local-" + secrets.token_urlsafe(10) + "!"
                user = User(name=name, email=email, role=UserRole(role), password_hash=hash_password(password), email_verified=True)
                user.profile = Profile(profession=profession, skills=skills or [], embedding=text_processor.embed(" ".join([profession or "", *(skills or [])])))
                db.add(user)
                db.flush()
                by_email[email] = {"role": role, "label": name, "email": email, "password": password, "first_login_mfa_setup": role != "candidate"}
            elif email not in by_email:
                raise SystemExit("Hay una cuenta existente sin credencial de revisión. No se modifica su contraseña.")
            return user
        candidates = [account(key, "candidate", name, profession, skills) for key, name, profession, skills, _ in CANDIDATES]
        jobs = []
        for key, name, sector, offers in COMPANIES:
            owner = account(key, "company", name)
            company = db.query(Company).filter_by(nit=f"LOCAL-REVIEW-{key}").first()
            if company is None:
                company = Company(owner_user_id=owner.id, name=name, nit=f"LOCAL-REVIEW-{key}", description="Organización ficticia para explorar flujos locales. No representa una oferta laboral real.", sector=sector,
                                  location="Bogotá", verification_required=True, verification_status="verified", verification_feedback="Empresa ficticia aprobada exclusivamente para la revisión local.")
                db.add(company)
                db.flush()
            elif company.verification_status == "approved":
                # Repair only the obsolete status of this fixture, never user organizations.
                company.verification_status = "verified"
            for title, skills, salary, modality in offers:
                job = db.query(Job).filter_by(company_id=company.id, title=title).first()
                if job is None:
                    job = Job(company_id=company.id, title=title, sector=sector, salary=salary, modality=modality, location="Bogotá", blind_hiring=True,
                              description=f"Vacante ficticia de revisión local. Desarrolla tareas de {title.lower()} y colabora con el equipo para registrar y mejorar resultados. Horario de lunes a viernes, 8:00 a 17:00.",
                              requirements=f"Requisitos esenciales: {', '.join(skills)}. Experiencia inicial o formación relacionada. Proceso: revisión de perfil y entrevista, con respuesta en siete días.",
                              skills=skills, skill_requirements=[{"skill": skill, "essential": True, "weight": 1} for skill in skills],
                              benefits=["Acompañamiento inicial", "Plan de formación"], embedding=text_processor.embed(f"{title} {' '.join(skills)}"))
                    db.add(job)
                    db.flush()
                jobs.append(job)
        for candidate, job in zip(candidates, [jobs[0], jobs[3], jobs[2], jobs[4]], strict=True):
            if not db.query(Application).filter_by(user_id=candidate.id, job_id=job.id).first():
                db.add(Application(user_id=candidate.id, job_id=job.id, pipeline_stage="submitted"))
        account("admin", "admin", "Administración · revisión local")
        db.commit()
    file.write_text(json.dumps(list(by_email.values()), ensure_ascii=False, indent=2), encoding="utf-8")
    print("Revisión preparada: 4 candidatos, 3 empresas, 6 vacantes y 1 administrador. Credenciales privadas en .local/review-accounts.json.")


if __name__ == "__main__":
    main()
