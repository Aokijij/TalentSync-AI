"""Observed demand, fixed anonymous cohorts and comparable published pay."""
import math
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from statistics import median
from types import SimpleNamespace
from urllib.parse import urlparse

from app.domain.services.career_coach import demand_report
from app.domain.services.personalization import synthetic_email
from app.domain.services.professions import PROFESSION_GROUPS
from app.domain.services.requirement_analysis import ROLE_FAMILIES
from app.domain.services.skill_context import fold
from app.domain.services.skills import skill_set
from app.domain.services.work_preferences import city_key

MINIMUM_SAMPLE = 20
FAMILIES = {"software": "Tecnología y desarrollo", "data": "Datos y analítica", "electronics": "Electrónica y telecomunicaciones", "civil": "Construcción y arquitectura", "business": "Administración y negocios", "finance": "Contabilidad y finanzas", "marketing": "Mercadeo y comunicación", "people": "Talento humano", "industrial": "Industria y operaciones", "health": "Salud", "legal": "Derecho", "education": "Educación", "sales": "Ventas", "service": "Servicio al cliente", "logistics": "Logística e inventarios", "design": "Diseño"}


def families_for(title):
    text = fold(title)
    found = {key for key, terms in ROLE_FAMILIES.items() if any(term in text for term in terms)}
    found.update(key for key, terms in PROFESSION_GROUPS.items() if any(fold(term) in text for term in terms))
    return found


def synthetic_job(job):
    text = fold(f"{job.title} {getattr(job, 'company_name', '')}")
    hostname = urlparse(getattr(job, "external_url", "") or "").hostname or ""
    return (getattr(job, "source_name", "") == "local-realistic" or getattr(job, "source_kind", "") == "demo" or "demo" in fold(getattr(job, "source_name", ""))
            or bool(re.search(r"\b(?:fictici\w*|demostracion|synthetic|demo)\b", text))
            or bool(re.search(r"(?:·\s*escenario|\(escenario|\bescenario\s*$)", fold(job.title)))
            or "sin contratacion real" in fold(job.description)
            or any(hostname == domain or hostname.endswith("." + domain) for domain in ("example.com", "example.org", "example.net")) or hostname.endswith((".test", ".invalid", ".localhost")))


def selected_jobs(jobs, filters, now):
    result, seen = [], set()
    words = fold(filters.get("search", "")).split()
    demo = filters.get("dataset") == "demo"
    for job in sorted(jobs, key=lambda item: (item.created_at, item.id), reverse=True):
        details = job.quality_details or {}
        if (job.status != ("draft" if demo else "active") or job.created_at < now - timedelta(days=90) or job.expires_at and job.expires_at < now
                or (getattr(job, "source_name", "") != "radar-demo" if demo else synthetic_job(job) and not (filters.get("allow_local_fixtures") and getattr(job, "source_name", "") == "local-realistic"))):
            continue
        if filters.get("family") and filters["family"] not in families_for(job.title):
            continue
        if filters.get("level") and details.get("seniority") != filters["level"]:
            continue
        if filters.get("location") and city_key(job.location) != city_key(filters["location"]):
            continue
        if filters.get("sector") and fold(filters["sector"]) != fold(job.sector):
            continue
        if filters.get("modality") and filters["modality"] != job.modality:
            continue
        if words and not all(word in fold(job.title) for word in words):
            continue
        key = (fold(getattr(job, "company_name", "") or str(job.company_id)), fold(job.title), city_key(job.location))
        if key not in seen:
            seen.add(key); result.append(job)
    return result


def peer_report(profile, candidates, filters, now):
    # Fixed area/city/level partitions: search terms, sector and modality never
    # create arbitrary overlapping subsets of private candidate profiles.
    if not all(filters.get(key) for key in ("family", "level", "location")):
        return {"status": "choose_cohort", "minimum_sample": MINIMUM_SAMPLE, "skills": [], "note": "Elige área, nivel y ciudad para ver un grupo comparable."}
    cohort, used = [], set()
    demo = filters.get("dataset") == "demo"
    for row in candidates:
        consent = row.participation or {}
        local_fixture = bool(filters.get("allow_local_fixtures") and getattr(row, "is_local_fixture", False))
        date = consent.get("updated_at", "")
        try:
            recent = datetime.fromisoformat(date.replace("Z", "+00:00")).replace(tzinfo=None) >= now - timedelta(days=180)
        except (ValueError, TypeError, AttributeError):
            recent = False
        if (row.user_id == profile.user_id or row.user_id in used or not row.email_verified
                or (not getattr(row, "is_demo", False) if demo else getattr(row, "is_demo", False) or (not local_fixture and (getattr(row, "is_local_fixture", False) or synthetic_email(row.email) or row.email.lower().endswith((".invalid", ".localhost")))))
                or not consent.get("enabled") or (not demo and not local_fixture and not consent.get("confirmed_real")) or not recent
                or consent.get("family") != filters["family"] or consent.get("level") != filters["level"] or city_key(row.location) != city_key(filters["location"])):
            continue
        used.add(row.user_id); cohort.append(row)
    if len(cohort) < MINIMUM_SAMPLE:
        return {"status": "insufficient_data", "minimum_sample": MINIMUM_SAMPLE, "skills": [], "note": "Todavía no hay un grupo suficiente de participantes. No mostramos porcentajes de grupos pequeños."}
    counts = Counter(skill for row in cohort for skill in skill_set(row.skills))
    known = skill_set(profile.skills)
    rows = [{"skill": skill, "percentage": int(5 * round(100 * count / len(cohort) / 5)), "declared": skill in known} for skill, count in sorted(counts.items(), key=lambda row: (-row[1], row[0])) if 5 <= count <= len(cohort) - 5][:12]
    return {"status": "ready", "minimum_sample": MINIMUM_SAMPLE, "sample": len(cohort), "skills": rows,
            "note": "Habilidades declaradas por participantes voluntarios; no acreditan dominio. Porcentajes redondeados a cinco puntos y menciones infrecuentes ocultas. Se excluye tu cuenta. El texto de búsqueda, sector y modalidad no alteran este grupo."}


def percentile(values, ratio):
    ordered = sorted(values)
    index = (len(ordered) - 1) * ratio
    lower = math.floor(index)
    return round(ordered[lower] + (ordered[math.ceil(index)] - ordered[lower]) * (index - lower), 2)


def salary_report(jobs, filters):
    offers = [{"id": job.id, "title": job.title, "company": getattr(job, "company_name", ""), "location": job.location,
               "level": (job.quality_details or {}).get("seniority"), "modality": job.modality, "salary": job.salary,
               "salary_max": (job.quality_details or {}).get("salary_max"), "contract_type": (job.quality_details or {}).get("contract_type"),
               "weekly_hours": (job.quality_details or {}).get("weekly_hours")}
              for job in jobs if job.salary and math.isfinite(job.salary) and job.salary > 0
              and all((job.quality_details or {}).get(key) == value for key, value in (("salary_currency", "COP"), ("salary_period", "monthly"), ("salary_basis", "gross_base")))]
    observations = {"offers": sorted(offers, key=lambda row: (row["salary"], row["id"])), "total_offers": len(jobs), "offers_with_salary": len(offers)}
    if not all(filters.get(key) for key in ("family", "level", "location")):
        return {**observations, "status": "choose_cohort", "groups": [], "minimum_sample": MINIMUM_SAMPLE, "note": "Puedes consultar los salarios de las ofertas filtradas. Para una mediana comparable, elige área, nivel y ciudad."}
    groups = defaultdict(lambda: defaultdict(list))
    eligible = 0
    for job in jobs:
        d = job.quality_details or {}
        if (not job.salary or not math.isfinite(job.salary) or job.salary <= 0 or d.get("salary_currency") != "COP" or d.get("salary_period") != "monthly"
                or d.get("salary_basis") != "gross_base" or not d.get("contract_type") or not isinstance(d.get("weekly_hours"), (int, float)) or isinstance(d.get("weekly_hours"), bool) or not 1 <= d["weekly_hours"] <= 80):
            continue
        eligible += 1
        key = (job.modality, job.employment_type, d["contract_type"], d["weekly_hours"])
        groups[key][job.company_id].append(job.salary)
    results = []
    for key, companies in groups.items():
        values = [median(amounts) for amounts in companies.values()]
        if len(values) < MINIMUM_SAMPLE:
            continue
        results.append({"modality": key[0], "employment_type": key[1], "contract_type": key[2], "weekly_hours": key[3], "sample": len(values),
                        "offers": sum(len(amounts) for amounts in companies.values()), "median": round(median(values), 2), "p25": percentile(values, .25), "p75": percentile(values, .75)})
    return {**observations, "status": "ready" if results else "insufficient_data", "groups": sorted(results, key=lambda row: (-row["sample"], row["modality"], row["contract_type"], row["weekly_hours"])),
            "minimum_sample": MINIMUM_SAMPLE, "eligible_offers": eligible, "offers_with_salary": sum(bool(job.salary and job.salary > 0) for job in jobs), "total_offers": len(jobs),
            "currency": "COP", "period": "monthly", "basis": "gross_base",
            "note": "Mínimos fijos brutos publicados en COP al mes, no salarios pagados. Mediana por empresa y luego entre empresas; cada grupo separa contrato, modalidad, jornada y horas. No se infieren condiciones ausentes ni se incluyen pagos variables."}


def market_report(profile, jobs, candidates, courses, filters, now=None):
    now = now or datetime.utcnow()
    selected = selected_jobs(jobs, filters, now)
    demo = filters.get("dataset") == "demo"
    demand_jobs = [SimpleNamespace(**{key: getattr(job, key, None) for key in ("id", "company_id", "company_name", "title", "created_at", "expires_at", "sector", "location", "skills", "source_name")}, status="active") for job in selected] if demo else selected
    demand = demand_report(profile, demand_jobs, courses, now=now)
    observed = {row["skill"]: row for row in demand["skills"]}
    demand["own_skills"] = [observed.get(skill, {"skill": skill, "count": 0, "percentage": None, "declared": True,
        "courses": [{key: course.get(key) for key in ("id", "title", "provider", "hours", "url")} for course in courses if skill in skill_set(course.get("skills", []))][:3]}) for skill in sorted(skill_set(profile.skills))]
    demand["own_skills"].sort(key=lambda row: (-row["count"], row["skill"]))
    demand["note"] = "Ofertas publicadas activas de los últimos 90 días, sin duplicados por empresa, cargo y ubicación. Se excluyen demos identificables. La demanda observada no representa todo el mercado."
    peers, salary = peer_report(profile, candidates, filters, now), salary_report(selected, filters)
    if demo:
        demand.update(jobs=[], note="Demostración con ofertas ficticias variadas. Los conteos sirven para probar el radar; no describen demanda real ni son vacantes para postularse.", sources={"Escenarios de demostración": len(selected)})
        peers["note"] = "Comparación de perfiles ficticios creados para probar la plataforma. Las habilidades declaradas y porcentajes son de ejemplo." if peers["status"] == "ready" else peers["note"]
        salary["note"] = "Salarios simulados en COP al mes para recorrer el radar. No representan remuneraciones del mercado. Cada grupo conserva contrato, modalidad y horas iguales."
    local_data = bool(filters.get("allow_local_fixtures") and any(getattr(job, "source_name", "") == "local-realistic" for job in jobs))
    cohorts = Counter((family, (job.quality_details or {}).get("seniority"), job.location) for job in jobs if not synthetic_job(job) or (local_data and getattr(job, "source_name", "") == "local-realistic") for family in families_for(job.title))
    available = [{"family": family, "level": level, "location": city, "offers": count} for (family, level, city), count in cohorts.most_common() if level and city and count >= MINIMUM_SAMPLE][:8]
    if local_data:
        demand["note"] = "Ofertas activas del entorno local de pruebas. Empresas, procesos y salarios recreados; no son ofertas oficiales ni estadísticas del mercado real."
        peers["note"] = "Comparación agregada de perfiles de prueba del mismo grupo. " + peers["note"]
        salary["note"] = "Salarios de las vacantes de prueba, no remuneraciones oficiales. " + salary["note"]
    return {"dataset": "demo" if demo else "real", "local_data": local_data, "available_cohorts": available, "as_of": now.isoformat() + "Z", "since": (now - timedelta(days=90)).date().isoformat(), "filters": {key: value for key, value in filters.items() if key != "allow_local_fixtures"}, "demand": demand,
            "peers": peers, "salary": salary, "families": FAMILIES,
            "aspiration": profile.desired_salary, "participation": (profile.preferences or {}).get("market_participation", {})}
