"""Public employer boards: no API key, candidate data or application submission."""
import json
import re
import unicodedata
from datetime import datetime, timezone
from urllib.parse import urlsplit

from app.application.errors import CatalogProviderError
from app.domain.entities.catalog import CatalogJob
from app.domain.services.external_job_content import source_text
from app.infrastructure.job_availability import ats_reference
from app.infrastructure.public_http import PublicHTTP, PublicHTTPError, public_url


def board_reference(url):
    parsed = urlsplit(public_url(url))
    board = parsed.path.strip("/")
    if parsed.query or not re.fullmatch(r"[a-zA-Z0-9_-]{1,80}", board):
        raise ValueError("Usa la dirección del portal de empleos de una empresa, sin un ID de vacante")
    if parsed.hostname in {"boards.greenhouse.io", "job-boards.greenhouse.io"}:
        return "greenhouse", board
    if parsed.hostname in {"jobs.lever.co", "jobs.eu.lever.co"}:
        return "lever_eu" if parsed.hostname == "jobs.eu.lever.co" else "lever", board
    if parsed.hostname == "jobs.ashbyhq.com":
        return "ashby", board
    raise ValueError("Usa un portal público de Greenhouse, Lever o Ashby")


def plain(value):
    return source_text(value)[:20_000]


def folded(value):
    return "".join(c for c in unicodedata.normalize("NFKD", value.casefold()) if not unicodedata.combining(c))


def monthly_cop(description):
    """Only an explicitly denominated, monthly COP amount; never convert USD."""
    amount = r"(\d{1,3}(?:[.,]\d{3}){2,3}|\d{7,9})"
    match = re.search(r"(?:COP\s*\$?\s*" + amount + r"|\$?\s*" + amount +
                      r"\s*COP)\s*(?:mensuales?|monthly|al mes)\b", description, re.I)
    if not match:
        return ""
    return re.sub(r"[.,]", "", match.group(1) or match.group(2))


def published_date(row, provider):
    try:
        if provider == "greenhouse" and row.get("first_published"):
            value = datetime.fromisoformat(row["first_published"].replace("Z", "+00:00"))
            return value.astimezone(timezone.utc).replace(tzinfo=None)
        if provider != "greenhouse" and row.get("createdAt"):
            return datetime.fromtimestamp(float(row["createdAt"]) / 1000, timezone.utc).replace(tzinfo=None)
        if provider == "ashby" and row.get("publishedAt"):
            return datetime.fromisoformat(row["publishedAt"].replace("Z", "+00:00")).astimezone(timezone.utc).replace(tzinfo=None)
    except (ValueError, TypeError, OverflowError, OSError):
        pass
    return None


class EmployerBoardCatalog:
    def __init__(self, board_url, http=None):
        self.provider, self.board = board_reference(board_url)
        self.board_url = public_url(board_url)
        self.http = http or PublicHTTP(timeout=20, max_bytes=16_000_000)
        self.source_name = {"greenhouse": "Greenhouse", "ashby": "Ashby"}.get(self.provider, "Lever")

    def preview(self, *, keywords="", location="Colombia"):
        endpoint = (f"https://api.ashbyhq.com/posting-api/job-board/{self.board}" if self.provider == "ashby" else f"https://boards-api.greenhouse.io/v1/boards/{self.board}/jobs?content=true" if self.provider == "greenhouse" else
                    f"https://api{'.eu' if self.provider == 'lever_eu' else ''}.lever.co/v0/postings/{self.board}?mode=json&limit=1000")
        try:
            response = self.http.get(endpoint)
            expected, actual = urlsplit(endpoint), urlsplit(response.url)
            if (actual.hostname, actual.path.rstrip("/")) != (expected.hostname, expected.path.rstrip("/")):
                raise PublicHTTPError("Unexpected source redirect")
            if response.status != 200:
                raise PublicHTTPError("Source unavailable")
            value = json.loads(response.body)
            rows = value.get("jobs") if isinstance(value, dict) else value
            if not isinstance(rows, list) or len(rows) > 5000:
                raise ValueError("Invalid board response")
            jobs = []
            for row in rows:
                if not isinstance(row, dict):
                    continue
                if self.provider == "ashby":
                    if not row.get("isListed"):
                        continue
                    title, url = row.get("title"), row.get("jobUrl")
                    places = [{"location": row.get("location", ""), "address": (row.get("address") or {}).get("postalAddress", {})}, *(row.get("secondaryLocations") or [])]
                    published_places = [str(item.get("location") or "") + (", Colombia" if str((item.get("address") or {}).get("addressCountry", "")).casefold() in {"co", "col", "colombia"} else "") for item in places]
                    place = next((item for item in published_places if "colombia" in folded(item)), published_places[0])
                    description = plain(row.get("descriptionHtml") or row.get("descriptionPlain"))
                    contract = {"FullTime": "full_time", "PartTime": "part_time", "Intern": "internship", "Contract": "contract", "Temporary": "temporary"}.get(row.get("employmentType"), "")
                    remote = row.get("workplaceType") == "Remote"
                elif self.provider == "greenhouse":
                    title, url = row.get("title"), row.get("absolute_url")
                    place = (row.get("location") or {}).get("name", "")
                    description = plain(row.get("content"))
                    contract, remote = "", None
                else:
                    title, url = row.get("text"), row.get("hostedUrl")
                    category = row.get("categories") or {}
                    place = category.get("location", "")
                    description = plain(row.get("descriptionPlain") or row.get("description"))
                    description += "\n\n" + "\n\n".join(plain(item.get("text")) + "\n" + plain(item.get("content")) for item in row.get("lists", []) if isinstance(item, dict))
                    contract, remote = category.get("commitment", ""), row.get("workplaceType") == "remote"
                if not isinstance(title, str) or not isinstance(place, str) or not isinstance(url, str):
                    continue
                if self.provider == "ashby":
                    if not url.startswith(f"https://jobs.ashbyhq.com/{self.board}/") or urlsplit(url).path.strip("/").split("/") != [self.board, str(row.get("id"))]:
                        continue
                else:
                    reference = ats_reference(url)
                    if not reference or reference[:2] != (self.provider, self.board) or reference[2] != str(row.get("id")):
                        continue
                # Explicit locations only: "remote" alone never means eligible in Colombia.
                if location and folded(location) not in folded(place):
                    continue
                if keywords and folded(keywords) not in folded(title + " " + description):
                    continue
                if not contract and re.search(r"\b(?:intern|internship|practicante|pasante)\b", folded(title)):
                    contract = "internship"
                company = row.get("company_name") if self.provider == "greenhouse" else {"addi": "Addi", "nubank": "Nu"}.get(self.board, self.board)
                jobs.append(CatalogJob(external_id=str(row["id"]), title=title[:180], company=company or self.board,
                    location=place[:120], description=description[:20_000], employment_type=contract,
                    salary=monthly_cop(description), url=url, company_url=self.board_url, remote=remote,
                    published_at=published_date(row, self.provider)))
            return jobs[:100], len(rows)
        except (PublicHTTPError, ValueError, TypeError, AttributeError, RecursionError) as error:
            raise CatalogProviderError("No fue posible consultar el portal público. Revisa la dirección y vuelve a intentarlo.") from error
