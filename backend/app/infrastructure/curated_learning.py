"""Versioned editorial connectors to official course pages; no provider API claims."""
import copy
import json
from functools import lru_cache
from hashlib import sha256
from pathlib import Path
from urllib.parse import urlsplit

from app.api.schemas.learning import ResourceContent
from app.application.errors import UseCaseError

CATALOG_PATH = Path(__file__).resolve().parents[1] / "data" / "education_catalog.json"


@lru_cache(maxsize=1)
def _catalog():
    payload = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    revision = sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:24]
    providers = {row["id"]: row for row in payload["providers"]}
    rows, seen = [], set()
    for row in payload["resources"]:
        provider = providers[row["provider_id"]]
        content = ResourceContent(**row["content"], active=False).model_dump()
        if row["source_id"] in seen or urlsplit(content["url"]).hostname not in provider["hosts"]:
            raise ValueError("Invalid editorial course identity or provider host")
        seen.add(row["source_id"])
        rows.append({"source_id": row["source_id"], "provider_id": row["provider_id"], "content": content,
                     "source": {"provider": row["provider_id"], "id": row["source_id"], "mode": "editorial",
                                "reviewed_at": payload["reviewed_at"], "reference_url": content["url"],
                                "catalog_revision": revision}})
    return {"revision": revision, "reviewed_at": payload["reviewed_at"], "resources": rows,
            "providers": [{"id": key, "name": provider["name"], "url": provider["url"],
                           "count": sum(row["provider_id"] == key for row in rows), "mode": "editorial"}
                          for key, provider in providers.items()]}


def catalog():
    return copy.deepcopy(_catalog())


def selected(revision, ids):
    current = catalog()
    if revision != current["revision"]:
        raise UseCaseError(status_code=409, detail="La selección editorial cambió; recarga sus fuentes antes de importar.")
    indexed = {row["source_id"]: row for row in current["resources"]}
    if not ids or len(ids) != len(set(ids)) or any(key not in indexed for key in ids):
        raise UseCaseError(status_code=422, detail="Selecciona cursos distintos de las fuentes oficiales disponibles.")
    return [indexed[key] for key in ids]
