"""Source-backed additions never change source availability or dates."""
import hashlib
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from app.domain.services.external_job_content import extract_content


def exclusion_key(url):
    parts = urlsplit(url or "")
    query = [(k, v) for k, v in parse_qsl(parts.query) if not k.lower().startswith("utm_") and k.lower() not in {"ref", "source", "fbclid", "gclid"}]
    canonical = urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path.rstrip("/"), urlencode(sorted(query)), ""))
    return hashlib.sha256(canonical.encode()).hexdigest()


def apply_editorial(job, *, refresh_source=False):
    metadata = getattr(job, "editorial_overrides", None) or {}
    fields = metadata.get("fields") or {}
    if not fields:
        return
    if refresh_source:
        metadata = {**metadata, "source": {key: getattr(job, key, None) for key in fields}}
        job.editorial_overrides = metadata
    for key, value in fields.items():
        if key in {"description", "requirements", "salary", "skills", "required_education_level", "required_study_fields"}:
            setattr(job, key, value)
    if "skills" in fields:
        job.skill_requirements = [{"skill": skill, "essential": False, "level": "unspecified"} for skill in fields["skills"]]
    content, details, _, _ = extract_content(job.title, job.description, job.requirements, published_at=job.external_published_at)
    job.external_content = {**(job.external_content or {}), **content}
    job.quality_details = {**(job.quality_details or {}), **details}

