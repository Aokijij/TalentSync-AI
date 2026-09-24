import json
import re
from datetime import datetime
from html import unescape
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from app.application.errors import CatalogProviderError
from app.domain.entities.catalog import CatalogJob, CatalogPage


class JoobleJobCatalog:
    def __init__(self, api_key: str | None, base_url: str, timeout_seconds: float):
        self._api_key = (api_key or "").strip()
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds

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
                "Jooble aún no está conectado. Agrega JOOBLE_API_KEY en Azure."
            )
        payload = json.dumps(
            {
                "keywords": keywords,
                "location": location,
                "radius": "80",
                "page": page,
                "ResultOnPage": result_count,
                "SearchMode": 0,
                "companysearch": False,
            }
        ).encode("utf-8")
        request = Request(
            f"{self._base_url}/{quote(self._api_key, safe='')}",
            data=payload,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "User-Agent": "TalentSync/1.0",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=self._timeout_seconds) as response:
                body = json.loads(response.read().decode("utf-8"))
        except HTTPError as error:
            if error.code == 403:
                message = "Jooble rechazó la clave configurada. Verifica la clave de Colombia."
            elif error.code == 404:
                message = "No se encontró la API regional de Jooble configurada."
            else:
                message = f"Jooble respondió con un error HTTP {error.code}."
            raise CatalogProviderError(message) from error
        except (URLError, TimeoutError) as error:
            raise CatalogProviderError(
                "Jooble no respondió a tiempo. Intenta la sincronización nuevamente."
            ) from error
        except (UnicodeDecodeError, json.JSONDecodeError, TypeError) as error:
            raise CatalogProviderError(
                "Jooble devolvió una respuesta que TalentSync no pudo interpretar."
            ) from error

        if not isinstance(body, dict) or not isinstance(body.get("jobs", []), list):
            raise CatalogProviderError(
                "Jooble devolvió una respuesta que TalentSync no pudo interpretar."
            )
        jobs = [self._map_job(item) for item in body.get("jobs", []) if isinstance(item, dict)]
        return CatalogPage(jobs=jobs, total=int(body.get("totalCount") or len(jobs)))

    @staticmethod
    def _map_job(item: dict) -> CatalogJob:
        updated = None
        raw_updated = str(item.get("updated") or "").strip()
        if raw_updated:
            try:
                normalized = re.sub(
                    r"(\.\d{6})\d+", r"\1", raw_updated.rstrip("Z")
                )
                updated = datetime.fromisoformat(normalized)
            except ValueError:
                updated = None
        return CatalogJob(
            external_id=str(item.get("id") or "").strip(),
            title=_clean(item.get("title")),
            company=_clean(item.get("company")) or "Empresa confidencial",
            location=_clean(item.get("location")),
            description=_clean(item.get("snippet")),
            employment_type=_clean(item.get("type")),
            url=str(item.get("link") or "").strip(),
            published_at=updated,
        )


def _clean(value: object) -> str:
    text = unescape(str(value or ""))
    result: list[str] = []
    inside_tag = False
    for character in text:
        if character == "<":
            inside_tag = True
        elif character == ">":
            inside_tag = False
            result.append(" ")
        elif not inside_tag:
            result.append(character)
    return " ".join("".join(result).split())
