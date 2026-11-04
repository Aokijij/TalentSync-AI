"""Editorial facts and local states never manufacture a successful source check."""
import hashlib
from datetime import datetime, timezone
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from app.domain.services.external_job_content import clarity_reasons, extract_content


def exclusion_key(url):
    parts = urlsplit(url or "")
    query = [(k, v) for k, v in parse_qsl(parts.query) if not k.lower().startswith("utm_") and k.lower() not in {"ref", "source", "fbclid", "gclid"}]
    canonical = urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path.rstrip("/"), urlencode(sorted(query)), ""))
    return hashlib.sha256(canonical.encode()).hexdigest()


def source_value(value):
    return value.isoformat() + "Z" if isinstance(value, datetime) else value


EDITABLE_FIELDS = {"title", "description", "requirements", "salary", "skills", "skill_requirements", "languages", "required_education_level", "required_study_fields", "location", "department", "modality", "employment_type", "sector", "benefits", "external_published_at"}


def apply_editorial(job, *, refresh_source=False):
    metadata = getattr(job, "editorial_overrides", None) or {}
    fields = metadata.get("fields") or {}
    if refresh_source and fields:
        metadata = {**metadata, "source": {key: source_value(getattr(job, key, None)) for key in fields}}
        job.editorial_overrides = metadata
    # A local pause/closure is independent of the source's next refresh.
    if metadata.get("catalog_status") in {"draft", "paused", "closed"}:
        job.status = metadata["catalog_status"]
    if not fields:
        return
    previous_requirements = {row["skill"]: row for row in (job.skill_requirements or [])}
    for key, value in fields.items():
        if key in EDITABLE_FIELDS:
            if key in {"external_published_at"} and value is not None:
                value = datetime.fromisoformat(value.replace("Z", "+00:00")) if isinstance(value, str) else value
                if value.tzinfo:
                    value = value.astimezone(timezone.utc).replace(tzinfo=None)
            setattr(job, key, value)
    if "skill_requirements" in fields:
        job.skills = [row["skill"] for row in fields["skill_requirements"]]
    elif "skills" in fields:
        job.skill_requirements = [previous_requirements.get(skill, {"skill": skill, "essential": False, "level": "unspecified", "weight": 1}) for skill in fields["skills"]]
    content, extracted, _, _ = extract_content(job.title, job.description, job.requirements, published_at=job.external_published_at)
    details = {**(job.quality_details or {}), **extracted, **(fields.get("quality_details") or {})}
    # These inputs have been explicitly transcribed into the named editorial fields.
    # They do not need a particular heading for the parser to recognize them.
    for field, key, title in [("description", "responsibilities", "Funciones y responsabilidades"), ("requirements", "requirements", "Requisitos del cargo")]:
        if field in fields:
            text = fields[field]
            if key == "requirements" or not any(row["key"] == key for row in content["sections"]):
                content["sections"] = [row for row in content["sections"] if row["key"] != key] + [{"key": key, "title": title, "text": text}]
    if "required_education_level" in fields or "required_study_fields" in fields:
        content["education"] = {**content["education"], "status": "required" if job.required_education_level else "unspecified", "level": job.required_education_level, "fields": job.required_study_fields or [], "accepts_students": bool(details.get("education_accepts_in_progress"))}
    reasons = clarity_reasons(content, details)
    blocking = [reason for reason in reasons if reason in {"responsibilities_unclear", "requirements_unclear"}]
    content["admission"] = {**content["admission"], "clarity_passed": not blocking, "clarity_reasons": blocking, "information_gaps": [reason for reason in reasons if reason not in blocking]}
    content["evidence"] = {**content.get("evidence", {}), "editorial_fields": sorted(fields)}
    job.external_content = {**(job.external_content or {}), **content}
    job.quality_details = details
