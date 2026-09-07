from collections import Counter
from datetime import date, timedelta
from itertools import combinations
from time import perf_counter

from app.application.errors import UseCaseError
from app.application.ports.services import ResumeReader, TextAnalysis
from app.application.ports.unit_of_work import UnitOfWork
from app.domain.entities.records import User


def platform_stats(current_user: User, db: UnitOfWork) -> dict[str, int]:
    return {
        "users": db.users.count(),
        "companies": db.companies.count(),
        "jobs": db.jobs.count(),
        "applications": db.applications.count(),
        "recommendations": db.recommendations.count(),
    }


def platform_analytics(
    current_user: User, db: UnitOfWork, *, nlp: TextAnalysis, resumes: ResumeReader
) -> dict:
    """Operational analytics used by the live administration dashboard."""
    today = date.today()
    days = [today - timedelta(days=offset) for offset in range(13, -1, -1)]
    user_counts = Counter(
        (created_at.date() for created_at in db.users.creation_dates())
    )
    application_counts = Counter(
        (created_at.date() for created_at in db.applications.creation_dates())
    )
    recommendations = db.recommendations.count()
    recommended_applications = db.applications.count_recommended()
    hires = sum(
        (
            1
            for (application_status,) in db.applications.status_rows()
            if (
                application_status.value
                if hasattr(application_status, "value")
                else str(application_status)
            )
            in {"accepted", "hired"}
        )
    )
    skill_counts: Counter[str] = Counter()
    edge_counts: Counter[tuple[str, str]] = Counter()
    for (skills,) in db.jobs.active_skill_rows():
        normalized = sorted(
            {str(skill).strip().title() for skill in skills or [] if str(skill).strip()}
        )[:10]
        skill_counts.update(normalized)
        edge_counts.update(combinations(normalized, 2))
    top_skills = {name for name, _ in skill_counts.most_common(12)}
    graph_edges = [
        {"source": source, "target": target, "weight": weight}
        for (source, target), weight in edge_counts.most_common(24)
        if source in top_skills and target in top_skills
    ]
    started = perf_counter()
    db.ping()
    db_latency = round((perf_counter() - started) * 1000, 1)
    storage_ok = resumes.storage_available()
    started = perf_counter()
    nlp_dimensions = len(nlp.embed("comprobacion de salud"))
    nlp_latency = round((perf_counter() - started) * 1000, 1)
    return {
        "timeline": [
            {
                "date": day.isoformat(),
                "users": user_counts[day],
                "applications": application_counts[day],
            }
            for day in days
        ],
        "active_jobs": db.jobs.count_active(),
        "conversion_rate": round(recommended_applications / recommendations * 100, 1)
        if recommendations
        else 0.0,
        "recommended_applications": recommended_applications,
        "hires": hires,
        "skill_graph": {
            "nodes": [
                {"id": name, "count": count}
                for name, count in skill_counts.most_common(12)
            ],
            "edges": graph_edges,
        },
        "infrastructure": [
            {
                "service": "Base de datos",
                "status": "healthy",
                "detail": "Consultas operativas",
                "latency_ms": db_latency,
            },
            {
                "service": "Almacenamiento",
                "status": "healthy" if storage_ok else "warning",
                "detail": "Directorio de CV disponible"
                if storage_ok
                else "Directorio pendiente de inicializacion",
                "latency_ms": None,
            },
            {
                "service": "Motor NLP",
                "status": "healthy" if nlp_dimensions else "error",
                "detail": f"Vectorizador activo ({nlp_dimensions} dimensiones)",
                "latency_ms": nlp_latency,
            },
        ],
    }


def list_users(current_user: User, db: UnitOfWork) -> list[dict]:
    return [
        {"id": user.id, "name": user.name, "email": user.email, "role": user.role.value}
        for user in db.users.recent()
    ]


def list_admin_companies(current_user: User, db: UnitOfWork) -> list[dict]:
    return [
        {
            "id": company.id,
            "name": company.name,
            "nit": company.nit,
            "description": company.description,
            "jobs": len(company.jobs),
        }
        for company in db.companies.first_fifty()
    ]


def list_admin_jobs(current_user: User, db: UnitOfWork) -> list[dict]:
    return [
        {
            "id": job.id,
            "title": job.title,
            "company_id": job.company_id,
            "salary": job.salary,
            "skills": job.skills,
            "applications": len(job.applications),
        }
        for job in db.jobs.recent()
    ]


def delete_admin_job(job_id: int, current_user: User, db: UnitOfWork) -> None:
    job = db.jobs.get(job_id)
    if job is None:
        raise UseCaseError(status_code=404, detail="Vacante no encontrada")
    db.delete(job)
    db.commit()


def delete_admin_company(company_id: int, current_user: User, db: UnitOfWork) -> None:
    company = db.companies.get(company_id)
    if company is None:
        raise UseCaseError(status_code=404, detail="Empresa no encontrada")
    db.delete(company)
    db.commit()


def delete_admin_user(user_id: int, current_user: User, db: UnitOfWork) -> None:
    if user_id == current_user.id:
        raise UseCaseError(
            status_code=400, detail="No puedes eliminar tu propia cuenta"
        )
    user = db.users.get(user_id)
    if user is None:
        raise UseCaseError(status_code=404, detail="Usuario no encontrado")
    company = db.companies.find_by_owner(user.id)
    if company is not None:
        db.delete(company)
    db.delete(user)
    db.commit()
