import json
from datetime import datetime
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from app.application.errors import CatalogProviderError
from app.domain.entities.catalog import CatalogJob, CatalogPage


class AdzunaJobCatalog:
    def __init__(
        self,
        *,
        app_id: str | None,
        app_key: str | None,
        country: str = "us",
        base_url: str = "https://api.adzuna.com/v1/api/jobs",
        timeout_seconds: float = 20,
    ):
        self._app_id = (app_id or "").strip()
        self._app_key = (app_key or "").strip()
        self._country = country.strip().lower() or "us"
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds

    @property
    def source_name(self) -> str:
        return "Adzuna"

    @property
    def registration_url(self) -> str:
        return "https://developer.adzuna.com/"

    @property
    def configured(self) -> bool:
        return bool(self._app_id and self._app_key)

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
                "Adzuna necesita ADZUNA_APP_ID y ADZUNA_APP_KEY en Azure."
            )
        query = urlencode(
            {
                "app_id": self._app_id,
                "app_key": self._app_key,
                "results_per_page": min(result_count, 50),
                "what": keywords,
                "where": location,
                "sort_by": "date",
                "max_days_old": 60,
                "content-type": "application/json",
            }
        )
        request = Request(
            f"{self._base_url}/{self._country}/search/{page}?{query}",
            headers={"Accept": "application/json", "User-Agent": "TalentSync/1.0"},
        )
        try:
            with urlopen(request, timeout=self._timeout_seconds) as response:
                body = json.loads(response.read().decode("utf-8"))
        except HTTPError as error:
            message = (
                "Adzuna rechazó las credenciales configuradas."
                if error.code in {401, 403}
                else f"Adzuna respondió con un error HTTP {error.code}."
            )
            raise CatalogProviderError(message) from error
        except (URLError, TimeoutError) as error:
            raise CatalogProviderError("Adzuna no respondió a tiempo.") from error
        except (UnicodeDecodeError, json.JSONDecodeError, TypeError) as error:
            raise CatalogProviderError(
                "Adzuna devolvió una respuesta que TalentSync no pudo interpretar."
            ) from error

        results = body.get("results", []) if isinstance(body, dict) else []
        if not isinstance(results, list):
            raise CatalogProviderError(
                "Adzuna devolvió una respuesta que TalentSync no pudo interpretar."
            )
        jobs = [self._map_job(item) for item in results if isinstance(item, dict)]
        return CatalogPage(jobs=jobs, total=int(body.get("count") or len(jobs)))

    @staticmethod
    def _map_job(item: dict) -> CatalogJob:
        company = item.get("company") or {}
        location = item.get("location") or {}
        created = _date(item.get("created"))
        salary_min = item.get("salary_min")
        salary_max = item.get("salary_max")
        salary = ""
        if salary_min is not None and salary_max is not None:
            salary = f"{salary_min}-{salary_max}"
        elif salary_min is not None:
            salary = str(salary_min)
        elif salary_max is not None:
            salary = str(salary_max)
        return CatalogJob(
            external_id=str(item.get("id") or "").strip(),
            title=_clean(item.get("title")),
            company=_clean(company.get("display_name")) or "Empresa confidencial",
            location=_clean(location.get("display_name")),
            description=_clean(item.get("description")),
            employment_type=_clean(
                item.get("contract_time") or item.get("contract_type")
            ),
            salary=salary,
            url=str(item.get("redirect_url") or "").strip(),
            published_at=created,
        )


def _date(value: object) -> datetime | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return None


def _clean(value: object) -> str:
    return " ".join(str(value or "").split())
