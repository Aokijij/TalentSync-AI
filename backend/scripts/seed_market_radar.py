"""Varied fictitious profiles and unpublished offers, isolated from real statistics."""
from datetime import datetime, timedelta
from secrets import token_urlsafe

from app.domain.entities.enums import UserRole
from app.infrastructure.database.models import Company, Job, Profile, User
from app.infrastructure.security.passwords import hash_password

SCENARIOS = [("software", "junior", "Medellín", "Desarrollador frontend", 2_800_000),
             ("software", "mid", "Medellín", "Desarrollador backend", 4_800_000),
             ("data", "junior", "Bogotá", "Analista de datos", 3_200_000)]
NAMES = ["Camila", "Andrés", "Valeria", "Diego", "Mariana", "Nicolás", "Laura", "Felipe", "Daniela", "Mateo", "Sara", "Julián", "Paula", "Santiago", "Lucía", "David", "Natalia", "Tomás", "Isabel", "Sebastián", "Ana", "Juan", "Elena", "Gabriel"]
SKILLS = {"software": ["javascript", "typescript", "react", "html", "css", "git", "python", "sql", "api rest", "pruebas de software", "docker", "fastapi"],
          "data": ["sql", "python", "excel", "power bi", "analisis de datos", "estadistica", "pandas", "git", "visualizacion de datos"]}


def seed(db):
    now = datetime.utcnow()
    # One random, undisclosed password is sufficient; these accounts are not login fixtures.
    password = hash_password(token_urlsafe(32))
    companies = []
    for index in range(24):
        email = f"company-{index}@radar.local.test"
        owner = db.query(User).filter_by(email=email).first()
        if owner is None:
            owner = User(name=f"Equipo radar {index + 1} (demostración)", email=email, role=UserRole.COMPANY, password_hash=password)
            db.add(owner); db.flush()
        company = db.query(Company).filter_by(owner_user_id=owner.id).first()
        if company is None:
            company = Company(owner_user_id=owner.id, name=f"Laboratorio {index + 1:02d} · empresa ficticia", nit=f"RADAR-DEMO-{index:03d}", source_name="radar-demo",
                              description="Organización ficticia para comparar escenarios del radar. No realiza contrataciones.", sector="Tecnología y software", location="Medellín", size="11-50",
                              mission="Crear soluciones de ejemplo que permitan recorrer las herramientas de TalentSync.", values=["Documentación", "Colaboración"], benefits=["Aprendizaje guiado"])
            db.add(company); db.flush()
        companies.append(company)
    for group, (family, level, city, title, base) in enumerate(SCENARIOS):
        for index, name in enumerate(NAMES):
            email = f"profile-{group}-{index}@radar.local.test"
            user = db.query(User).filter_by(email=email).first()
            if user is None:
                user = User(name=f"{name} · perfil ficticio {group + 1}-{index + 1}", email=email, role=UserRole.CANDIDATE, password_hash=password, email_verified=True)
                db.add(user); db.flush()
            # Balanced overlaps produce differences without universal or rare disclosures.
            skills = [skill for position, skill in enumerate(SKILLS[family]) if (index + position * 3) % 24 < 10 + position % 8]
            profile = user.profile
            if profile is None:
                profile = Profile(user_id=user.id); db.add(profile)
            domain = ["inventarios", "pedidos", "servicios internos", "ventas", "atención al cliente", "reportes de operación"][index % 6]
            description = (f"Participé en un proyecto de {domain}: revisé necesidades con el equipo y organicé las tareas. "
                           f"Usé {', '.join(skills[:3])} para preparar entregables y documentar decisiones. "
                           "Comprobé los resultados con casos de ejemplo y presenté los cambios al equipo. Perfil y trayectoria completamente ficticios.")
            profile.profession = title; profile.skills = skills; profile.experience = description
            profile.location = city; profile.department = "Antioquia" if city == "Medellín" else "Bogotá D.C."
            profile.experiences = [{"role": title, "company": f"Proyecto de demostración {domain}", "start_date": "2023-02" if level == "junior" else "2020-03", "end_date": "2025-11", "description": description}]
            profile.educations = [{"degree": "Desarrollo de sistemas" if family == "software" else "Estadística y análisis de información", "institution": "Instituto ficticio del radar", "level": "technologist" if index % 3 else "university", "start_year": "2019", "end_year": "2022", "is_current": False}]
            profile.certifications = [{"name": f"Taller de {skills[0]}", "issuer": "Laboratorio ficticio", "year": "2024"}]
            profile.languages = [{"name": "Español", "level": "NATIVE"}, {"name": "Inglés", "level": ["A2", "B1", "B2"][index % 3]}]
            profile.desired_salary = base + index * 85_000; profile.preferred_sector = "Tecnología y software"; profile.preferred_modality = "hybrid"; profile.availability = "two_weeks"
            profile.preferences = {"radar_demo": True, "market_participation": {"enabled": True, "confirmed_real": False, "family": family, "level": level, "updated_at": now.isoformat() + "Z"}}
            external_id = f"scenario-{group}-{index}"
            job = db.query(Job).filter_by(source_name="radar-demo", external_id=external_id).first()
            if job is None:
                job = Job(company_id=companies[index].id, source_name="radar-demo", external_id=external_id, title=title, description="", requirements="")
                db.add(job)
            job.title = f"{title} · ejemplo {index + 1:02d}"; job.status = "draft"; job.created_at = now - timedelta(days=index % 30)
            job.description = f"Escenario ficticio sobre {domain}. Define tareas con el equipo, construye entregables, revisa resultados y documenta el proceso. No es una oportunidad de contratación."
            job.requirements = f"Uso de {', '.join(skills[:4])}. Comparte un proyecto y explica tus decisiones técnicas."
            job.skills = skills; job.location = city; job.department = profile.department; job.sector = "Tecnología y software"; job.salary = base + index * 110_000
            job.modality = "hybrid"; job.employment_type = "full_time"
            job.quality_details = {"version": 1, "seniority": level, "salary_currency": "COP", "salary_period": "monthly", "salary_basis": "gross_base", "weekly_hours": 40, "contract_type": "indefinite", "schedule": "Lunes a viernes, 40 horas semanales", "salary_max": job.salary + 500_000}
    db.commit()
    return {"profiles": 72, "companies": 24, "unpublished_salary_scenarios": 72}


if __name__ == "__main__":
    from app.core.config import settings
    from app.infrastructure.database.session import SessionLocal

    if settings.environment != "development" or not settings.database_url.startswith("sqlite:///") or "/.local/" not in settings.database_url.replace("\\", "/"):
        raise SystemExit("Este generador solo admite la base SQLite de desarrollo en .local/")
    with SessionLocal() as db:
        print(seed(db))
