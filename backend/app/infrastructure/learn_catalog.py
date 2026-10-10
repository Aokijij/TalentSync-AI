"""Authenticated Learn Platform metadata; explicit, bounded admin previews only."""
import copy
import re
import secrets
import threading
import time
from collections import OrderedDict
from datetime import datetime, timezone
from urllib.parse import parse_qs, urlsplit

import httpx
from pydantic import ValidationError

from app.api.schemas.learning import ResourceContent
from app.application.errors import UseCaseError

BASE = "https://learn.microsoft.com/api/v1"
VERSION = "2023-11-01-preview"


class LearnCatalog:
    def __init__(self, settings, transport=None):
        self.settings = settings
        self.transport = transport
        self._lock = threading.Lock()
        self._token = ("", 0)
        self._previews = OrderedDict()

    @property
    def configured(self):
        return bool(self.settings.learn_enabled and self.settings.learn_tenant_id
                    and self.settings.learn_client_id and self.settings.learn_client_secret)

    def _json(self, client, method, url, **kwargs):
        with client.stream(method, url, **kwargs) as response:
            if response.status_code != 200:
                detail = "Microsoft Learn rechazó el acceso; revisa los permisos de la aplicación." if response.status_code in {401, 403} else "Microsoft Learn no está disponible; intenta más tarde."
                raise UseCaseError(status_code=503, detail=detail)
            body = bytearray()
            for chunk in response.iter_bytes():
                body.extend(chunk)
                if len(body) > 2_000_000:
                    raise ValueError("response limit")
            import json
            value = json.loads(body)
            if not isinstance(value, dict):
                raise ValueError("response shape")
            return value

    def _access_token(self, client):
        with self._lock:
            token, expiry = self._token
            if expiry > time.monotonic():
                return token
            value = self._json(client, "POST", f"https://login.microsoftonline.com/{self.settings.learn_tenant_id}/oauth2/v2.0/token", data={
                "client_id": self.settings.learn_client_id, "client_secret": self.settings.learn_client_secret,
                "grant_type": "client_credentials", "scope": "https://learn.microsoft.com/.default",
            })
            token = value["access_token"]
            if not isinstance(token, str) or not token or len(token) > 16000:
                raise ValueError("token shape")
            self._token = (token, time.monotonic() + max(0, min(int(value.get("expires_in", 0)), 3600) - 60))
            return token

    @staticmethod
    def _page_url(cursor, kind):
        parsed = urlsplit(cursor)
        if (parsed.scheme != "https" or parsed.netloc != "learn.microsoft.com"
                or parsed.path != f"/api/v1/{kind}" or parsed.fragment or len(cursor) > 4000
                or parse_qs(parsed.query).get("api-version") != [VERSION]):
            raise UseCaseError(status_code=422, detail="La página de Microsoft Learn no es válida; inicia una nueva consulta.")
        return cursor

    @staticmethod
    def _resource(row):
        uid = row["id"]
        if not isinstance(uid, str) or not re.fullmatch(r"[\w.-]{1,200}", uid):
            raise ValueError("invalid identity")
        parsed = urlsplit(row["url"])
        if parsed.hostname != "learn.microsoft.com" or not parsed.path.startswith("/training/"):
            raise ValueError("invalid source link")
        # Product tags suggest a mapping for admin review; they do not accredit skills.
        skills = [product["name"] or product["id"] for product in row.get("products", [])][:20]
        if not skills:
            raise ValueError("no product tags")
        content = ResourceContent(title=row["title"], provider="Microsoft Learn", url=row["url"],
            instructions=row["summary"], skills=skills, hours=row["durationInMinutes"] / 60,
            category="technology", kind="course", cost="free", active=False).model_dump()
        return {"source_id": uid, "content": content,
                "source": {"provider": "microsoft_learn", "id": uid, "updated_at": str(row.get("updatedAt", ""))[:100],
                           "locale": str(row.get("locale", ""))[:20], "api_version": VERSION}}

    def preview(self, *, kind="modules", products="", cursor="", actor_id):
        if not self.configured:
            raise UseCaseError(status_code=503, detail="Microsoft Learn está preparado, pendiente de configurar la aplicación de Microsoft Entra.")
        if kind not in {"modules", "learning-paths"} or not re.fullmatch(r"[a-z0-9,-]{0,120}", products):
            raise UseCaseError(status_code=422, detail="Filtro de Microsoft Learn inválido")
        url = self._page_url(cursor, kind) if cursor else f"{BASE}/{kind}"
        params = None if cursor else {"api-version": VERSION, "locale": "es-es", "maxpagesize": 20, **({"products": products} if products else {})}
        try:
            with httpx.Client(transport=self.transport, timeout=10, follow_redirects=False, trust_env=False) as client:
                token = self._access_token(client)
                data = self._json(client, "GET", url, params=params, headers={"Authorization": f"Bearer {token}", "Accept": "application/json"})
            values = data["value"]
            if not isinstance(values, list) or len(values) > 100:
                raise ValueError("page size")
            rows, skipped, seen = [], 0, set()
            for row in values:
                try:
                    item = self._resource(row)
                    if item["source_id"] not in seen:
                        rows.append(item)
                        seen.add(item["source_id"])
                except (ValueError, TypeError, KeyError, ValidationError):
                    skipped += 1
            next_link = data.get("nextLink") or ""
            if next_link:
                self._page_url(next_link, kind)
            preview_id = secrets.token_urlsafe(24)
            fetched_at = datetime.now(timezone.utc).isoformat()
            with self._lock:
                # Memory is bounded and previews cannot be reused by another administrator.
                self._previews[preview_id] = (time.monotonic() + 600, actor_id, copy.deepcopy(rows), fetched_at)
                while len(self._previews) > 32:
                    self._previews.popitem(last=False)
            return {"preview_id": preview_id, "resources": rows, "skipped": skipped, "next_cursor": next_link,
                    "fetched_at": fetched_at, "expires_in": 600}
        except (httpx.HTTPError, ValueError, TypeError, KeyError, AttributeError, RecursionError):
            raise UseCaseError(status_code=503, detail="No pudimos leer el catálogo de Microsoft Learn. Revisa la conexión y vuelve a consultar.") from None

    def selected(self, preview_id, ids, *, actor_id):
        with self._lock:
            entry = self._previews.get(preview_id)
            if not entry or entry[0] <= time.monotonic() or entry[1] != actor_id:
                raise UseCaseError(status_code=409, detail="La vista previa venció; consulta Microsoft Learn de nuevo.")
            _, _, rows, fetched_at = entry
            selected = [copy.deepcopy(row) for row in rows if row["source_id"] in ids]
            if len(selected) != len(set(ids)) or not selected:
                raise UseCaseError(status_code=422, detail="Selecciona recursos de la vista previa actual")
            for row in selected:
                row["source"]["fetched_at"] = fetched_at
            return selected
