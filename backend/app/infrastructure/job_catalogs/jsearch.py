import json
import re
from datetime import datetime
from html import unescape
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from app.application.errors import CatalogProviderError
from app.domain.entities.catalog import CatalogJob, CatalogPage


class JSearchJobCatalog:
    def __init__(
        self,
        *,
        api_key: str | None,
        base_url: str = "https://api.openwebninja.com/jsearch/search-v2",
        country: str = "co",
        language: str = "es",
        timeout_seconds: float = 25,
    ):
        self._api_key = (api_key or "").strip()
        self._base_url = base_url
        self._country = country
        self._language = language
        self._timeout_seconds = timeout_seconds

    @property
    def source_name(self) -> str:
        return "JSearch"

    @property
    def registration_url(self) -> str:
        return "https://www.openwebninja.com/api/jsearch"

    @property
    def configured(self) -> bool:
        return bool(self._api_key)

    def search(
        self,
        *,
        keywords: str,
        location: str,
        page: int,
        result_count: int,
    ) -> CatalogPage:
        if not self.configured:
            raise CatalogProviderError(
                "JSearch aún no está conectado. Agrega JSEARCH_API_KEY en Azure."
            )
        query_text = " ".join(filter(None, [keywords, f"en {location}" if location else ""]))
        query = urlencode(
            {
                "query": query_text,
                "country": self._country,
                "language": self._language,
                "date_posted": "month",
            }
        )
        request = Request(
            f"{self._base_url}?{query}",
            headers={
                "Accept": "application/json",
                "User-Agent": "TalentSync/1.0",
                "x-api-key": self._api_key,
            },
        )
        try:
            with urlopen(request, timeout=self._timeout_seconds) as response:
                body = json.loads(response.read().decode("utf-8"))
        except HTTPError as error:
            message = (
                "JSearch rechazó la clave configurada."
                if error.code in {401, 403}
                else f"JSearch respondió con un error HTTP {error.code}."
            )
            raise CatalogProviderError(message) from error
        except (URLError, TimeoutError) as error:
            raise CatalogProviderError("JSearch no respondió a tiempo.") from error
        except (UnicodeDecodeError, json.JSONDecodeError, TypeError) as error:
            raise CatalogProviderError(
                "JSearch devolvió una respuesta que TalentSync no pudo interpretar."
            ) from error

        data = body.get("data", []) if isinstance(body, dict) else []
        # OpenWebNinja search-v2 currently wraps the result collection in
        # data.jobs. Keep support for the earlier flat data array as well.
        results = data.get("jobs", []) if isinstance(data, dict) else data
        if not isinstance(results, list):
            raise CatalogProviderError(
                "JSearch devolvió una respuesta que TalentSync no pudo interpretar."
            )
        jobs = [self._map_job(item) for item in results if isinstance(item, dict)]
        # search-v2 is cursor based. A page request intentionally reuses the current
        # result set until the provider exposes its cursor through the shared port.
        if page > 1:
            jobs = []
        return CatalogPage(jobs=jobs[:result_count], total=len(jobs))

    def _map_job(self, item: dict) -> CatalogJob:
        employment_types = item.get("job_employment_types") or []
        employment_type = item.get("job_employment_type") or (
            employment_types[0] if employment_types else ""
        )
        location = item.get("job_location") or ", ".join(
            filter(
                None,
                [item.get("job_city"), item.get("job_state"), item.get("job_country")],
            )
        )
        highlights = item.get("job_highlights") or {}
        skills = _strings(
            [
                *(item.get("required_technologies") or []),
                *(item.get("preferred_technologies") or []),
                *(item.get("soft_skills") or []),
                *(item.get("job_required_skills") or []),
            ]
        )
        description = _clean(item.get("job_description"))
        raw_title = _clean(item.get("job_title"))
        salary = _salary(
            item,
            title=raw_title,
            description=description,
            country=self._country,
        )
        return CatalogJob(
            external_id=str(item.get("job_id") or "").strip(),
            title=_title_without_salary(raw_title),
            company=_clean(item.get("employer_name")) or "Empresa confidencial",
            location=_clean(location),
            description=description,
            employment_type=_clean(employment_type),
            salary=salary,
            url=str(
                item.get("job_apply_link")
                or item.get("job_google_link")
                or ""
            ).strip(),
            published_at=_date(item.get("job_posted_at_datetime_utc")),
            skills=tuple(skills),
            benefits=tuple(
                _strings(
                    item.get("job_benefits_strings")
                    or item.get("job_benefits")
                    or []
                )
            ),
            company_url=str(item.get("employer_website") or "").strip() or None,
            remote=(
                True
                if item.get("job_is_remote") is True
                or str(item.get("work_arrangement") or "").lower() == "remote"
                else None
            ),
            requirements=_requirements(highlights, description),
        )


def _strings(values: list[object]) -> list[str]:
    return list(
        dict.fromkeys(
            _clean(value).lower() for value in values if _clean(value)
        )
    )


def _salary(
    item: dict, *, title: str, description: str, country: str
) -> str:
    # The database currently stores salary as monthly COP without a currency
    # column. Do not present USD/EUR values as Colombian pesos.
    if country.casefold() != "co":
        return ""
    minimum = item.get("job_min_salary")
    maximum = item.get("job_max_salary")
    period = _clean(item.get("job_salary_period")).casefold()
    structured = [value for value in (minimum, maximum) if value is not None]
    if structured:
        values = [_monthly_cop(float(value), period) for value in structured]
        return "-".join(str(round(value)) for value in values)

    salary_string = _clean(item.get("job_salary_string"))
    inferred = _extract_colombian_salary(
        " ".join(value for value in (salary_string, title, description[:1_200]) if value)
    )
    return str(round(inferred)) if inferred is not None else ""


def _monthly_cop(value: float, period: str) -> float:
    if any(term in period for term in ("year", "annual", "año")):
        return value / 12
    if any(term in period for term in ("hour", "hora")):
        return value * 192
    return value


def _extract_colombian_salary(text: str) -> float | None:
    candidates: list[float] = []
    for match in re.finditer(
        r"(?:COP|\$)\s*(\d{7,8})|(?<!\d)(\d{7,8})\s*COP",
        text,
        flags=re.IGNORECASE,
    ):
        value = float(match.group(1) or match.group(2))
        if 1_000_000 <= value <= 50_000_000:
            candidates.append(value)
    for match in re.finditer(r"(?<!\d)(\d{1,2}(?:[.,]\d{3}){2})(?!\d)", text):
        value = float(re.sub(r"[.,]", "", match.group(1)))
        if 1_000_000 <= value <= 50_000_000:
            candidates.append(value)
    for match in re.finditer(
        r"(?<!\d)(\d{1,2}(?:[.,]\d{1,2})?)\s*mill(?:ó|o)?n(?:es)?",
        text.casefold(),
    ):
        value = float(match.group(1).replace(",", ".")) * 1_000_000
        if 1_000_000 <= value <= 50_000_000:
            candidates.append(value)
    return min(candidates) if candidates else None


def _title_without_salary(title: str) -> str:
    cleaned = re.sub(
        r"(?:\s*[-–|:]?\s*)(?:COP\s*|\$\s*)?\d{1,2}(?:[.,]\d{3}){2}(?:\s*(?:COP|mensuales?|al mes))?",
        "",
        title,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(
        r"(?:\s*[-–|:]?\s*)\d{1,2}(?:[.,]\d{1,2})?\s*mill(?:ó|o)?n(?:es)?(?:\s*(?:COP|mensuales?|al mes))?",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(
        r"(?:\s*[-–|:]?\s*)(?:COP\s*|\$\s*)?\d{7,8}(?:\s*(?:COP|mensuales?|al mes))?",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    return re.sub(r"\s{2,}", " ", cleaned).strip(" -–|:") or title


def _date(value: object) -> datetime | None:
    if isinstance(value, (int, float)):
        try:
            return datetime.utcfromtimestamp(value)
        except (OverflowError, OSError, ValueError):
            return None
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return None


def _requirements(highlights: object, description: str) -> str:
    if isinstance(highlights, dict):
        values = highlights.get("Qualifications") or highlights.get("qualifications")
        if isinstance(values, list):
            result = " ".join(_clean(value) for value in values if _clean(value))
            if result:
                return result

    lowered = description.casefold()
    headings = (
        "requisitos",
        "requirements",
        "qualifications",
        "qué necesitas",
        "que necesitas",
        "perfil requerido",
        "what you bring",
    )
    positions = [lowered.find(heading) for heading in headings]
    positions = [position for position in positions if position >= 0]
    if positions:
        return description[min(positions) :][:6_000]

    signals = (
        "experiencia",
        "conocimiento",
        "formación",
        "profesional",
        "requerimos",
        "buscamos",
        "nivel de",
        "years of experience",
        "knowledge of",
        "required",
        "bachelor",
        "skills",
    )
    sentences = [
        part.strip()
        for part in re.split(r"(?<=[.!?])\s+|\n+", description)
        if part.strip()
    ]
    selected = [
        sentence
        for sentence in sentences
        if any(signal in sentence.casefold() for signal in signals)
    ]
    if selected:
        return " ".join(selected)[:6_000]
    return description[-1_500:] if description else ""


def _clean(value: object) -> str:
    return " ".join(unescape(str(value or "")).split())
