import csv
import hashlib
import io
import re
import unicodedata
from datetime import datetime, timedelta
from urllib.parse import parse_qsl, urlparse

from openpyxl import load_workbook

from app.application.errors import CatalogProviderError, UseCaseError
from app.application.ports.services import JobCatalog, TextAnalysis
from app.application.ports.unit_of_work import UnitOfWork
from app.application.use_cases.integration_observations import (
    record as record_integration,
)
from app.domain.entities.catalog import CatalogJob
from app.domain.entities.job_sectors import JOB_SECTORS
from app.domain.entities.records import User
from app.domain.services.external_job_content import (
    extract_content,
    extract_external_skills,
    infer_external_sector,
    publication_reasons,
    source_text,
)
from app.domain.services.external_sources import external_portal

MAX_IMPORT_ROWS = 2_000
IMPORT_HEADERS = (
    "fuente",
    "id_externo",
    "empresa",
    "cargo",
    "descripcion",
    "requisitos",
    "sector",
    "enlace_externo",
    "fecha_publicacion",
    "fecha_vencimiento",
    "salario",
    "departamento",
    "ciudad",
    "modalidad",
    "tipo_contrato",
    "habilidades",
    "beneficios",
    "idiomas",
    "sitio_empresa",
    "descripcion_empresa",
)


def _key(value: object) -> str:
    text = "".join(
        character
        for character in unicodedata.normalize("NFKD", str(value or ""))
        if not unicodedata.combining(character)
    )
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def _text(row: dict[str, object], name: str, *, required: bool = False) -> str:
    value = " ".join(str(row.get(name) or "").strip().split())
    if required and not value:
        raise ValueError(f"Falta la columna obligatoria “{name}”")
    return value


def _split(value: object) -> list[str]:
    return list(
        dict.fromkeys(
            item.strip().lower()
            for item in re.split(r"[|,]", str(value or ""))
            if item.strip()
        )
    )


def _salary(value: object) -> float | None:
    if value in (None, ""):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    raw = str(value).strip().lower()
    if any(term in raw for term in ("a convenir", "por definir", "no especific")):
        return None
    amounts: list[float] = []
    for token in re.findall(r"\d+(?:[.,]\d+)*", raw):
        groups = re.split(r"[.,]", token)
        if len(groups) > 1 and all(len(group) == 3 for group in groups[1:]):
            amounts.append(float("".join(groups)))
            continue
        normalized = token.replace(",", ".")
        try:
            amount = float(normalized)
        except ValueError:
            continue
        if "millon" in raw and amount < 1_000:
            amount *= 1_000_000
        amounts.append(amount)
    if not amounts:
        raise ValueError("El salario debe contener un valor numérico")
    # The current model stores one value. For a range, keep its lower bound so
    # salary filters do not promise more than the source actually offers.
    return min(amounts)


def _date(value: object, field: str) -> datetime | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value.replace(tzinfo=None)
    raw = str(value).strip()
    for pattern in ("%Y-%m-%d", "%d/%m/%Y", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(raw, pattern)
        except ValueError:
            continue
    raise ValueError(f"{field} debe usar AAAA-MM-DD")


def _url(value: object, field: str, *, required: bool = False) -> str | None:
    raw = str(value or "").strip()
    if not raw:
        if required:
            raise ValueError(f"Falta la columna obligatoria “{field}”")
        return None
    parsed = urlparse(raw)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"{field} debe ser una dirección web válida")
    if len(raw) > 1_000:
        raise ValueError(f"{field} es demasiado largo")
    return raw


def _languages(value: object) -> list[dict[str, str]]:
    languages: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in re.split(r"[|,]", str(value or "")):
        if not item.strip():
            continue
        name, separator, level = item.partition(":")
        name = " ".join(name.lower().strip().split())
        level = level.strip().upper()
        if not separator or level not in {"A1", "A2", "B1", "B2", "C1", "C2", "NATIVE"}:
            raise ValueError(
                "Los idiomas deben usar el formato idioma:nivel, por ejemplo inglés:B2"
            )
        if name in seen:
            raise ValueError(f"El idioma “{name}” está repetido")
        seen.add(name)
        languages.append({"name": name, "level": level})
    return languages


def _rows(filename: str, content: bytes) -> list[dict[str, object]]:
    suffix = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    if suffix == "csv":
        try:
            decoded = content.decode("utf-8-sig")
        except UnicodeDecodeError as error:
            raise UseCaseError(
                status_code=400, detail="El CSV debe estar guardado en formato UTF-8"
            ) from error
        try:
            dialect = csv.Sniffer().sniff(decoded[:4_096], delimiters=",;\t")
        except csv.Error:
            dialect = csv.excel
        reader = csv.DictReader(io.StringIO(decoded), dialect=dialect)
        if not reader.fieldnames:
            raise UseCaseError(
                status_code=400, detail="El archivo no contiene encabezados"
            )
        return [
            {_key(name): value for name, value in row.items() if name}
            for row in reader
            if any(str(value or "").strip() for value in row.values())
        ]
    if suffix == "xlsx":
        try:
            workbook = load_workbook(
                io.BytesIO(content), read_only=True, data_only=True
            )
            sheet = workbook.active
            values = sheet.iter_rows(values_only=True)
            headers = [_key(value) for value in next(values, ())]
            if not any(headers):
                raise ValueError("El archivo no contiene encabezados")
            return [
                {
                    headers[index]: value
                    for index, value in enumerate(row)
                    if index < len(headers)
                }
                for row in values
                if any(str(value or "").strip() for value in row)
            ]
        except (OSError, ValueError, TypeError) as error:
            raise UseCaseError(
                status_code=400, detail=f"El Excel no es válido: {error}"
            ) from error
    raise UseCaseError(status_code=400, detail="Selecciona un archivo CSV o XLSX")


def _mapped(value: str, mapping: dict[str, str], default: str, field: str) -> str:
    if not value:
        return default
    result = mapping.get(_key(value))
    if result is None:
        raise ValueError(f"Valor no reconocido en {field}: {value}")
    return result


def _sector(value: str) -> str:
    sectors = {_key(item): item for item in JOB_SECTORS}
    result = sectors.get(_key(value))
    if result is None:
        raise ValueError(f"Sector laboral no reconocido: {value}")
    return result


def _company_nit(source: str, name: str) -> str:
    digest = hashlib.sha256(f"{source}:{name}".encode("utf-8")).hexdigest()[:20]
    return f"EXT-{digest}"


def listing_fingerprint(
    company: str,
    title: str,
    location: str | None,
    department: str | None = None,
) -> tuple[str, str, str, str]:
    """Stable identity for an advertised role, independent of aggregator IDs."""
    def identity_part(value: object) -> str:
        return (
            _key(value)
            .replace("s_a_s", "sas")
            .replace("s_a", "sa")
            .replace("l_t_d_a", "ltda")
        )

    return tuple(
        identity_part(value) for value in (company, title, location, department)
    )


def listing_url_identity(url: str):
    parsed = urlparse(url)
    query = tuple(sorted((k, v) for k, v in parse_qsl(parsed.query)
                         if not k.startswith("utm_") and k not in {"gh_src", "source", "ref"}))
    return parsed.hostname, parsed.path.rstrip("/"), query


def template_csv() -> bytes:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(IMPORT_HEADERS)
    return ("\ufeff" + output.getvalue()).encode("utf-8")


def import_jobs(
    filename: str,
    content: bytes,
    current_user: User,
    db: UnitOfWork,
    *,
    nlp: TextAnalysis,
) -> dict:
    rows = _rows(filename, content)
    return _import_rows(rows, current_user, db, nlp=nlp)


def sync_job_catalog(
    *,
    keywords: str,
    location: str,
    pages: int,
    result_count: int,
    current_user: User,
    db: UnitOfWork,
    nlp: TextAnalysis,
    catalog: JobCatalog,
    max_age_days: int = 90,
    min_skills: int = 3,
) -> dict:
    source_name = getattr(catalog, "source_name", "Jooble")
    effective_min_skills = min_skills if hasattr(catalog, "source_name") else 0
    if not catalog.configured:
        raise UseCaseError(
            status_code=503,
            detail=(
                f"{source_name} aún no está conectado. "
                "Completa sus credenciales en la configuración del servidor."
            ),
        )
    rows: list[dict[str, object]] = []
    provider_total = 0
    try:
        for page_number in range(1, pages + 1):
            result = catalog.search(
                keywords=keywords,
                location=location,
                page=page_number,
                result_count=result_count,
            )
            provider_total = result.total
            rows.extend(
                _catalog_row(
                    job,
                    source_name=source_name,
                    max_age_days=max_age_days,
                )
                for job in result.jobs
            )
            if not result.jobs:
                break
    except CatalogProviderError as error:
        record_integration(db, source_name.casefold(), "provider_error")
        raise UseCaseError(status_code=502, detail=str(error)) from error
    record_integration(db, source_name.casefold())

    if not rows:
        raise UseCaseError(
            status_code=404,
            detail=(
                f"{source_name} no encontró vacantes para esa búsqueda y ubicación."
            ),
        )
    result = _import_rows(
        rows,
        current_user,
        db,
        nlp=nlp,
        max_age_days=max_age_days,
        min_skills=effective_min_skills,
    )
    return {
        **result,
        "fetched": len(rows),
        "provider_total": provider_total,
        "source": source_name,
    }


def _import_rows(
    rows: list[dict[str, object]],
    current_user: User,
    db: UnitOfWork,
    *,
    nlp: TextAnalysis,
    max_age_days: int | None = None,
    min_skills: int = 0,
) -> dict:
    if not rows:
        raise UseCaseError(status_code=400, detail="El archivo no contiene vacantes")
    if len(rows) > MAX_IMPORT_ROWS:
        raise UseCaseError(
            status_code=400,
            detail=f"Cada archivo puede contener máximo {MAX_IMPORT_ROWS} vacantes",
        )

    created = updated = companies_created = 0
    errors: list[dict[str, object]] = []
    seen_keys: set[tuple[str, str]] = set()
    seen_listings: set[tuple[str, str, str, str]] = set()
    seen_urls = set()
    existing_urls = {}
    existing_listings: dict[tuple[str, str, str, str], object] = {}
    for existing in db.jobs.external_listings():
        if existing.external_url:
            existing_urls[listing_url_identity(existing.external_url)] = existing
        fingerprint = listing_fingerprint(
            existing.company.name if existing.company else "",
            existing.title,
            existing.location,
            existing.department,
        )
        current = existing_listings.get(fingerprint)
        if current is None or (
            current.status != "active" and existing.status == "active"
        ):
            existing_listings[fingerprint] = existing
    now = datetime.utcnow()
    modality_map = {
        "remoto": "remote",
        "remote": "remote",
        "hibrido": "hybrid",
        "hybrid": "hybrid",
        "presencial": "onsite",
        "onsite": "onsite",
    }
    contract_map = {
        "tiempo_completo": "full_time",
        "full_time": "full_time",
        "medio_tiempo": "part_time",
        "part_time": "part_time",
        "contrato": "contract",
        "contract": "contract",
        "practicas": "internship",
        "practica": "internship",
        "internship": "internship",
        "temporal": "temporary",
        "temporary": "temporary",
    }

    for row_number, row in enumerate(rows, start=2):
        try:
            source = _text(row, "fuente", required=True)[:80]
            external_id = _text(row, "id_externo", required=True)[:180]
            identity = (source.casefold(), external_id.casefold())
            if identity in seen_keys:
                raise ValueError("La vacante está repetida dentro del archivo")
            seen_keys.add(identity)
            company_name = _text(row, "empresa", required=True)
            title = _text(row, "cargo", required=True)
            description = source_text(row.get("descripcion"))
            requirements = source_text(row.get("requisitos"))
            if len(company_name) > 180 or len(title) > 180:
                raise ValueError(
                    "El nombre de la empresa o el cargo supera 180 caracteres"
                )
            if len(description) < 40:
                raise ValueError(
                    "La descripción necesita al menos 40 caracteres y contenido del cargo"
                )
            sector = _sector(_text(row, "sector", required=True))
            external_url = _url(
                row.get("enlace_externo"), "enlace_externo", required=True
            )
            url_identity = listing_url_identity(external_url)
            if url_identity in seen_urls:
                raise ValueError("La dirección original de la oferta ya apareció en esta importación")
            company_url = _url(row.get("sitio_empresa"), "sitio_empresa")
            published_at = _date(row.get("fecha_publicacion"), "fecha_publicacion")
            date_reasons = publication_reasons(published_at, now=now)
            if date_reasons:
                raise ValueError({"publication_missing": "Falta una fecha de publicación de la fuente",
                                  "publication_too_old": "La publicación supera tres meses",
                                  "publication_in_future": "La fecha de publicación está en el futuro"}[date_reasons[0]])
            if (
                max_age_days is not None
                and published_at is not None
                and published_at < now - timedelta(days=max_age_days)
            ):
                raise ValueError(f"La vacante supera {max_age_days} días de antigüedad")
            expires_at = _date(row.get("fecha_vencimiento"), "fecha_vencimiento")
            if expires_at and expires_at < now:
                raise ValueError("La fecha de vencimiento ya pasó")
            modality = _mapped(
                _text(row, "modalidad"), modality_map, "unspecified", "modalidad"
            )
            employment_type = _mapped(
                _text(row, "tipo_contrato"),
                contract_map,
                "unspecified",
                "tipo_contrato",
            )
            location = _text(row, "ciudad") or None
            department = _text(row, "departamento") or None
            fingerprint = listing_fingerprint(company_name, title, location, department)
            if fingerprint in seen_listings:
                raise ValueError(
                    "La misma oferta ya apareció en esta importación, aunque use otro ID"
                )
            seen_listings.add(fingerprint)
            explicit_skills = _split(row.get("habilidades"))
            benefits = _split(row.get("beneficios"))
            languages = _languages(row.get("idiomas"))
            content, extracted_details, extracted_requirements, relevant_text = extract_content(title, description, requirements, published_at=published_at)
            requirements = extracted_requirements
            skill_text = relevant_text + "\n" + "\n".join(explicit_skills)
            analysis = nlp.analyze_job(skill_text)
            skills = extract_external_skills(skill_text, analysis.skills)[:40]
            minimum_skills = max(3, min_skills)
            if len(skills) < minimum_skills:
                raise ValueError(
                    f"Solo se identificaron {len(skills)} habilidades; "
                    f"se requieren al menos {minimum_skills} habilidades distintas del anuncio"
                )
            if not content["admission"]["clarity_passed"]:
                raise ValueError("La oferta no supera el filtro de claridad: " + ", ".join(content["admission"]["clarity_reasons"]))
            content["admission"] = {**content["admission"], "passed": True, "minimum_skills": 3, "maximum_age_months": 3}
            content["declared_skills"] = explicit_skills
            sector = infer_external_sector(title, sector)

            job_by_provider_id = db.jobs.find_external(source, external_id)
            job = existing_urls.get(url_identity) or existing_listings.get(fingerprint) or job_by_provider_id
            company = job.company if job is not None and job.company and job.company.is_external else db.companies.find_external(source, company_name)
            if company is None:
                company = db.companies.new(
                    owner_user_id=current_user.id,
                    name=company_name,
                    nit=_company_nit(source, company_name),
                    description=_text(row, "descripcion_empresa")
                    or f"Empresa incluida mediante el catálogo autorizado de {source}.",
                    website=company_url,
                    sector=sector,
                    location=", ".join(
                        filter(
                            None,
                            [_text(row, "ciudad"), _text(row, "departamento")],
                        )
                    )
                    or None,
                    is_external=True,
                    source_name=source,
                )
                db.add(company)
                db.flush()
                companies_created += 1
            else:
                if company_url:
                    company.website = company_url
                company.sector = company.sector or sector

            values = {
                "company_id": company.id,
                "title": title,
                "description": description,
                "requirements": requirements,
                "salary": _salary(row.get("salario")),
                "location": location,
                "department": department,
                "modality": modality,
                "employment_type": employment_type,
                "sector": sector,
                "status": "active",
                "benefits": benefits,
                "languages": languages,
                "required_education_level": content["education"]["level"] if content["education"]["status"] == "required" else None,
                "required_study_fields": content["education"]["fields"] if content["education"]["status"] == "required" else [],
                "skills": skills,
                "skill_requirements": [{"skill": skill, "level": "unspecified", "essential": False} for skill in skills],
                "quality_details": extracted_details,
                "external_published_at": published_at,
                "external_content": content,
                "embedding": analysis.embedding,
                "source_kind": "external",
                "source_name": source,
                "external_id": external_id,
                "external_url": external_url,
                "expires_at": expires_at,
                "last_seen_at": now,
                # A catalogue/import timestamp is not proof of an open original listing.
                "external_check_state": "pending",
                "external_next_check_at": now,
                "external_check_reason": "",
            }
            if values["salary"] is not None and row.get("moneda_salario") == "COP" and row.get("periodo_salario") == "monthly":
                values["quality_details"] = {
                    **extracted_details,
                    "salary_currency": "COP", "salary_period": "monthly",
                }
            if job is None:
                job = db.jobs.new(**values, created_at=published_at or now)
                db.add(job)
                db.flush()
                existing_listings[fingerprint] = job
                created += 1
            else:
                # JSearch can publish one listing through several aggregators.
                if job.external_url == external_url and job.status == "active":
                    for check_key in ("external_check_state", "external_next_check_at", "external_check_reason"):
                        values.pop(check_key, None)
                # Preserve the first stable external ID when the semantic listing
                # already exists and only refresh its content.
                if job.external_id != external_id:
                    values["external_id"] = job.external_id
                    values["source_name"] = job.source_name
                for key, value in values.items():
                    setattr(job, key, value)
                if published_at:
                    job.created_at = published_at
                existing_listings[fingerprint] = job
                updated += 1
            seen_urls.add(url_identity)
            existing_urls[url_identity] = job
        except ValueError as error:
            errors.append({"row": row_number, "detail": str(error)})

    if not created and not updated:
        raise UseCaseError(
            status_code=422,
            detail={
                "message": "Ninguna vacante pudo importarse",
                "errors": errors[:50],
            },
        )
    db.commit()
    return {
        "created": created,
        "updated": updated,
        "companies_created": companies_created,
        "rejected": len(errors),
        "errors": errors[:50],
        "availability_note": "Las ofertas externas solo se mostrarán al confirmar su vigencia en la fuente original.",
    }


def _catalog_row(
    job: CatalogJob, *, source_name: str, max_age_days: int
) -> dict[str, object]:
    city, department = _location_parts(job.location)
    colombian_departments = {"amazonas", "antioquia", "arauca", "atlantico", "bogota d.c.", "bolivar", "boyaca", "caldas", "caqueta", "casanare", "cauca", "cesar", "choco", "cordoba", "cundinamarca", "guainia", "guaviare", "huila", "la guajira", "magdalena", "meta", "narino", "norte de santander", "putumayo", "quindio", "risaralda", "san andres y providencia", "santander", "sucre", "tolima", "valle del cauca", "vaupes", "vichada"}
    if job.remote and _key(department).replace("_", " ") not in colombian_departments and "colombia" not in _key(job.location):
        department = "Remoto internacional"
        city = city or "Internacional"
    text = f"{job.title} {job.description}".casefold()
    published_at = job.published_at
    # Review window starts at import. An ATS still advertising an old role is
    # not evidence of closure; source checks independently enforce freshness.
    expires_at = datetime.utcnow() + timedelta(days=min(max_age_days, 30))
    portal = external_portal(job.url, job.location)
    provider_description = (
        f"{portal} publica el detalle completo de requisitos y condiciones. "
        "Confirma la información directamente en el anuncio original."
    )
    return {
        "fuente": source_name,
        "id_externo": job.external_id,
        "empresa": job.company,
        "cargo": job.title,
        "descripcion": job.description
        or f"Consulta la descripción completa de esta oportunidad en {portal}.",
        "requisitos": job.requirements or provider_description,
        "sector": _infer_sector(text),
        "enlace_externo": job.url,
        "fecha_publicacion": published_at,
        "fecha_vencimiento": expires_at,
        "salario": job.salary,
        "moneda_salario": "COP" if job.salary and source_name in {"JSearch", "Greenhouse", "Lever"} else "",
        "periodo_salario": "monthly" if job.salary and source_name in {"JSearch", "Greenhouse", "Lever"} else "",
        "departamento": department,
        "ciudad": city,
        "modalidad": "remoto" if job.remote else _infer_modality(text),
        "tipo_contrato": _infer_contract(job.employment_type),
        "habilidades": "|".join(job.skills),
        "beneficios": "|".join(job.benefits),
        "sitio_empresa": job.company_url,
        "descripcion_empresa": (f"Empresa con una oportunidad publicada en {portal}."),
    }


def _location_parts(location: str) -> tuple[str, str]:
    parts = [part.strip() for part in location.split(",") if part.strip()]
    if len(parts) >= 2:
        return parts[0], parts[-1]
    return (parts[0], "") if parts else ("", "")


def _infer_modality(text: str) -> str:
    if any(term in text for term in ("remoto", "remote", "teletrabajo")):
        return "remoto"
    if any(term in text for term in ("híbrido", "hibrido", "hybrid")):
        return "híbrido"
    if any(term in text for term in ("presencial", "on-site", "onsite", "on site")):
        return "presencial"
    return ""


def _infer_contract(value: str) -> str:
    normalized = _key(value)
    if any(term in normalized for term in ("part_time", "medio_tiempo")):
        return "medio tiempo"
    if any(term in normalized for term in ("intern", "practica", "pasantia")):
        return "prácticas"
    if any(term in normalized for term in ("temporary", "temporal")):
        return "temporal"
    if any(term in normalized for term in ("contract", "contrato")):
        return "contrato"
    return "tiempo completo" if any(term in normalized for term in ("full_time", "fulltime", "tiempo_completo")) else ""


def _infer_sector(text: str) -> str:
    rules = (
        ("Salud y bienestar", ("salud", "médic", "medic", "enfermer", "clínic")),
        ("Educacion", ("docente", "profesor", "educación", "colegio", "universidad")),
        ("Finanzas y banca", ("contable", "contador", "financ", "banco", "tesorer")),
        (
            "Ventas y comercio",
            (
                "venta",
                "comercial",
                "vendedor",
                "asesor comercial",
                "servicio al cliente",
            ),
        ),
        (
            "Logistica y transporte",
            ("logística", "logistica", "conductor", "transporte", "bodega"),
        ),
        ("Recursos humanos", ("recursos humanos", "talento humano", "reclut")),
        (
            "Marketing y publicidad",
            ("marketing", "mercadeo", "publicidad", "contenido"),
        ),
        ("Turismo y hoteleria", ("hotel", "turismo", "restaurante", "cocina")),
        (
            "Construccion e ingenieria",
            ("construcción", "construccion", "obra", "ingeniero civil"),
        ),
        ("Manufactura", ("producción", "produccion", "operario", "planta")),
        (
            "Tecnologia y software",
            (
                "software",
                "desarrollador",
                "programador",
                "sistemas",
                "datos",
                "soporte técnico",
            ),
        ),
        (
            "Sector publico y social",
            ("trabajo social", "fundación", "fundacion", "comunitario"),
        ),
    )
    for sector, terms in rules:
        if any(term in text for term in terms):
            return sector
    return "Retail y consumo masivo"


def _board_preview(payload, db, catalog):
    from app.application.errors import CatalogProviderError
    from app.application.use_cases.integration_observations import record
    provider = "greenhouse" if catalog.provider == "greenhouse" else "lever"
    try:
        jobs, scanned = catalog.preview(keywords=payload.keywords.strip(), location=payload.location.strip())
    except CatalogProviderError as failure:
        record(db, provider, "provider_error")
        raise UseCaseError(status_code=502, detail=str(failure)) from None
    record(db, provider)
    return catalog, jobs, scanned


def preview_employer_board(payload, db, nlp, *, catalog):
    from app.domain.services.external_job_content import (
        admission_reasons,
        extract_content,
        extract_external_skills,
    )

    catalog, jobs, scanned = _board_preview(payload, db, catalog)
    items = []
    for job in jobs:
        content, details, _, text = extract_content(job.title, job.description, job.requirements, published_at=job.published_at)
        skills = extract_external_skills(text, [*job.skills, *nlp.analyze_job(text).skills])
        reasons = admission_reasons(job.published_at, skills) + content["admission"]["clarity_reasons"]
        items.append({"id": job.external_id, "title": job.title, "company": job.company, "location": job.location,
                      "url": job.url, "description": content["summary"][:600], "published_at": job.published_at,
                      "skills": skills, "seniority": details.get("seniority"), "eligible": not reasons, "rejection_reasons": reasons})
    return {"provider": catalog.source_name, "scanned": scanned, "items": items, "note": "Solo se incorporan publicaciones de los últimos tres meses, con fecha de fuente y al menos tres habilidades distintas. Después se exige vigencia comprobada. La ubicación se conserva sin asumir elegibilidad por decir remoto."}


def import_employer_board(payload, current_user, db, nlp, *, catalog):
    if not payload.authorized or not payload.selected_ids:
        raise UseCaseError(status_code=422, detail="Selecciona ofertas y confirma que tienes autorización para incorporarlas")
    catalog, jobs, scanned = _board_preview(payload, db, catalog)
    selected = set(payload.selected_ids)
    selected_jobs = [job for job in jobs if job.external_id in selected]
    if len(selected_jobs) != len(selected):
        raise UseCaseError(status_code=409, detail="El portal cambió. Consulta de nuevo y revisa la selección")
    rows = [_catalog_row(job, source_name=catalog.source_name, max_age_days=30) for job in selected_jobs]
    result = _import_rows(rows, current_user, db, nlp=nlp)
    from datetime import datetime, timedelta
    # The explicit selection was re-fetched from the published source, not trusted from the browser.
    for job in selected_jobs:
        saved = db.jobs.find_external(catalog.source_name, job.external_id)
        if saved and saved.external_url == job.url:
            saved.external_check_state, saved.external_checked_at, saved.external_verified_at = "verified", datetime.utcnow(), datetime.utcnow()
            saved.external_check_reason, saved.external_next_check_at = "source_api", datetime.utcnow() + timedelta(hours=24)
    db.commit()
    return {**result, "source": catalog.source_name, "fetched": len(selected_jobs), "provider_total": scanned}
