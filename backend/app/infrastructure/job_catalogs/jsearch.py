import json
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

        results = body.get("data", []) if isinstance(body, dict) else []
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

    @staticmethod
    def _map_job(item: dict) -> CatalogJob:
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
        salary = _salary(item)
        skills = _strings(
            [
                *(item.get("required_technologies") or []),
                *(item.get("preferred_technologies") or []),
                *(item.get("soft_skills") or []),
            ]
        )
        return CatalogJob(
            external_id=str(item.get("job_id") or "").strip(),
            title=_clean(item.get("job_title")),
            company=_clean(item.get("employer_name")) or "Empresa confidencial",
            location=_clean(location),
            description=_clean(item.get("job_description")),
            employment_type=_clean(employment_type),
            salary=salary,
            url=str(
                item.get("job_apply_link")
                or item.get("job_google_link")
                or ""
            ).strip(),
            published_at=_date(item.get("job_posted_at_datetime_utc")),
            skills=tuple(skills),
            benefits=tuple(_strings(item.get("job_benefits") or [])),
            company_url=str(item.get("employer_website") or "").strip() or None,
            remote=(
                True
                if item.get("job_is_remote") is True
                or str(item.get("work_arrangement") or "").lower() == "remote"
                else None
            ),
        )


def _strings(values: list[object]) -> list[str]:
    return list(
        dict.fromkeys(
            _clean(value).lower() for value in values if _clean(value)
        )
    )


def _salary(item: dict) -> str:
    minimum = item.get("job_min_salary")
    maximum = item.get("job_max_salary")
    if minimum is not None and maximum is not None:
        return f"{minimum}-{maximum}"
    return str(minimum if minimum is not None else maximum or "")


def _date(value: object) -> datetime | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return None


def _clean(value: object) -> str:
    return " ".join(unescape(str(value or "")).split())
