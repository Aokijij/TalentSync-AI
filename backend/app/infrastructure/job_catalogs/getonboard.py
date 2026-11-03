"""Get on Board's documented public job API; no candidate data is sent."""
import json
from datetime import datetime, timezone
from urllib.parse import urlencode

from app.application.errors import CatalogProviderError
from app.domain.entities.catalog import CatalogJob, CatalogPage
from app.domain.services.external_job_content import source_text
from app.infrastructure.public_http import PublicHTTP


class GetOnBoardCatalog:
    source_name = "GetOnBoard"
    configured = True

    def __init__(self, http=None):
        self.http = http or PublicHTTP(timeout=15, max_bytes=4_000_000)

    def search(self, *, keywords="", location="Colombia", page=1, result_count=100):
        query = urlencode({"query": " ".join(filter(None, [keywords, location])), "page": page,
                           "per_page": min(result_count, 100), "expand": '["company","tags","location_cities","location_regions","modality"]'})
        try:
            response = self.http.get("https://www.getonbrd.com/api/v0/search/jobs?" + query)
            if response.status != 200:
                raise ValueError("Source unavailable")
            body = json.loads(response.body)
            rows = body["data"]
            jobs = [job for row in rows if (job := self.map_job(row)) and (not location or self.colombia_eligible(row))]
            return CatalogPage(jobs=jobs, total=int((body.get("meta") or {}).get("total_pages", page)) * min(result_count, 100))
        except (ValueError, TypeError, KeyError, OSError) as error:
            raise CatalogProviderError("No se pudo consultar la API pública de Get on Board.") from error

    @staticmethod
    def colombia_eligible(row):
        value = row.get("attributes") or {}
        countries = " ".join(str(item) for item in value.get("countries", [])).casefold()
        zone = str(value.get("remote_zone") or "").casefold()
        regions = {str(item.get("id", "")).casefold() for item in (value.get("location_regions") or {}).get("data", [])}
        return "colombia" in countries or bool(value.get("remote") and (zone in {"worldwide", "anywhere", "latin america", "latam", "americas"} or regions & {"south_america", "latin_america", "americas", "worldwide"}))

    @staticmethod
    def map_job(row):
        value = row.get("attributes") or {}
        company = ((value.get("company") or {}).get("data") or {}).get("attributes") or {}
        url = (row.get("links") or {}).get("public_url", "")
        if not value.get("title") or not company.get("name") or not url.startswith("https://www.getonbrd.com/jobs/"):
            return None
        tags = [item.get("attributes", {}).get("name", "") for item in (value.get("tags") or {}).get("data", [])]
        tags = [tag for tag in tags if tag]
        description = "\n\n".join(heading + "\n" + source_text(text) for heading, text in [
            ("Funciones y responsabilidades", value.get("functions")), ("Requisitos", value.get("description")),
            ("Conocimientos deseables", value.get("desirable")), ("Beneficios", value.get("benefits")),
            ("Habilidades publicadas", ", ".join(tags)),
        ] if text)
        cities = [item.get("attributes", {}).get("name", "") for item in (value.get("location_cities") or {}).get("data", [])]
        regions = [item.get("attributes", {}).get("name", "") for item in (value.get("location_regions") or {}).get("data", [])]
        place = ", ".join([*filter(None, cities), *value.get("countries", []), *filter(None, regions)])[:120]
        published = datetime.fromtimestamp(float(value["published_at"]), timezone.utc).replace(tzinfo=None) if value.get("published_at") else None
        return CatalogJob(external_id=str(row["id"]), title=value["title"][:180], company=company["name"],
            description=description[:20_000], requirements=source_text(value.get("description")), location=place,
            employment_type=(((value.get("modality") or {}).get("data") or {}).get("attributes") or {}).get("locale_key", ""), salary="", url=url, published_at=published,
            skills=tuple(tags), remote=bool(value.get("remote")), company_url=company.get("web"))
