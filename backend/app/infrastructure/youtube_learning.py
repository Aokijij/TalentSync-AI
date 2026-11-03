"""Read-only public playlist previews. API metadata is never persisted as courses."""
import json
import re
import secrets
import threading
import time
from collections import OrderedDict
from datetime import datetime, timezone
from urllib.parse import parse_qs, urlsplit

import httpx

from app.application.errors import UseCaseError

BASE = "https://www.googleapis.com/youtube/v3"


def playlist_id(value):
    value = value.strip()
    if re.fullmatch(r"[A-Za-z0-9_-]{10,100}", value):
        return value
    try:
        parsed = urlsplit(value)
        ids = parse_qs(parsed.query).get("list", [])
        if (parsed.scheme != "https" or parsed.netloc not in {"youtube.com", "www.youtube.com", "m.youtube.com"}
                or parsed.path not in {"/playlist", "/watch"} or parsed.fragment or len(ids) != 1
                or not re.fullmatch(r"[A-Za-z0-9_-]{10,100}", ids[0])):
            raise ValueError()
        return ids[0]
    except ValueError:
        raise UseCaseError(status_code=422, detail="Usa el identificador o el enlace HTTPS de una lista de reproducción de YouTube.") from None


class YouTubeLearning:
    def __init__(self, settings, transport=None):
        self.settings, self.transport = settings, transport
        self._lock = threading.Lock()
        self._day, self._requests = "", 0
        # Tokens contain only a playlist ID and actor, never titles/descriptions.
        self._previews = OrderedDict()

    @property
    def configured(self):
        return bool(self.settings.youtube_learning_enabled and self.settings.youtube_api_key)

    def status(self):
        with self._lock:
            day = datetime.now(timezone.utc).date().isoformat()
            used = self._requests if self._day == day else 0
        return {"configured": self.configured, "request_limit": self.settings.youtube_learning_daily_requests,
                "requests_used": used, "limit_scope": "process_utc_day", "preview_requests": 2}

    def _json(self, client, endpoint, params):
        with self._lock:
            today = datetime.now(timezone.utc).date().isoformat()
            if self._day != today:
                self._day, self._requests = today, 0
            if self._requests >= self.settings.youtube_learning_daily_requests:
                raise UseCaseError(status_code=429, detail="Se alcanzó el límite local diario de consultas a YouTube. Intenta mañana.")
            self._requests += 1  # Count failed attempts as well as successful calls.
        with client.stream("GET", f"{BASE}/{endpoint}", params=params,
                           headers={"X-Goog-Api-Key": self.settings.youtube_api_key, "Accept": "application/json"}) as response:
            if response.status_code != 200:
                detail = "YouTube rechazó la consulta; revisa la clave, las restricciones y la cuota del proyecto." if response.status_code in {400, 401, 403} else "La lista no está disponible públicamente o YouTube no respondió."
                raise UseCaseError(status_code=503, detail=detail)
            body = bytearray()
            for chunk in response.iter_bytes():
                body.extend(chunk)
                if len(body) > 300_000:
                    raise ValueError("response limit")
            data = json.loads(body)
            if not isinstance(data, dict) or not isinstance(data.get("items"), list) or len(data["items"]) > 20:
                raise ValueError("response shape")
            return data

    def preview(self, url, *, actor_id):
        identifier = playlist_id(url)
        if not self.configured:
            raise UseCaseError(status_code=503, detail="YouTube está preparado, pendiente de configurar una clave de YouTube Data API v3 en el servidor.")
        try:
            with httpx.Client(transport=self.transport, timeout=6, follow_redirects=False, trust_env=False) as client:
                data = self._json(client, "playlists", {"part": "snippet,contentDetails,status", "id": identifier, "hl": "es"})
                row = next((item for item in data["items"] if item.get("id") == identifier), None)
                if not row or row.get("status", {}).get("privacyStatus") != "public":
                    raise UseCaseError(status_code=422, detail="Solo se pueden revisar listas públicas. Comprueba el enlace y su visibilidad.")
                snippet = row["snippet"]
                count = row["contentDetails"]["itemCount"]
                if type(count) is not int or count < 1:
                    raise UseCaseError(status_code=422, detail="La lista no contiene vídeos disponibles para revisar.")
                items = self._json(client, "playlistItems", {"part": "snippet", "playlistId": identifier, "maxResults": 12})
            videos = []
            for item in items["items"]:
                part = item.get("snippet", {})
                video = part.get("resourceId", {}).get("videoId", "")
                title = part.get("title", "")
                if re.fullmatch(r"[A-Za-z0-9_-]{11}", video) and isinstance(title, str) and title not in {"Private video", "Deleted video"}:
                    videos.append({"title": title[:200], "url": f"https://www.youtube.com/watch?v={video}&list={identifier}"})
            if not videos:
                raise UseCaseError(status_code=422, detail="No se encontraron vídeos públicos en la muestra. Revisa otra lista.")
            token = secrets.token_urlsafe(24)
            with self._lock:
                self._previews[token] = (time.monotonic() + 900, actor_id, identifier)
                while len(self._previews) > 32:
                    self._previews.popitem(last=False)
            return {"preview_id": token, "playlist_id": identifier, "title": str(snippet["title"])[:200],
                    "channel": str(snippet.get("channelTitle", ""))[:200],
                    "description": str(snippet.get("description", ""))[:2000], "item_count": count,
                    "videos": videos, "sample_only": count > len(videos), "expires_in": 900,
                    "url": f"https://www.youtube.com/playlist?list={identifier}",
                    "fetched_at": datetime.now(timezone.utc).isoformat()}
        except (httpx.HTTPError, ValueError, TypeError, KeyError, AttributeError, RecursionError):
            raise UseCaseError(status_code=503, detail="No pudimos consultar YouTube. No se guardó ningún curso; intenta de nuevo.") from None

    def selected(self, preview_id, *, actor_id):
        with self._lock:
            entry = self._previews.get(preview_id)
            if not entry or entry[0] <= time.monotonic() or entry[1] != actor_id:
                raise UseCaseError(status_code=409, detail="La revisión de YouTube venció; consulta la lista de nuevo.")
            return entry[2]
