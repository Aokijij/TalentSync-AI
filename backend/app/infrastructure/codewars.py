"""Bounded public Codewars reader. No credentials, private data or code execution."""
import copy
import hashlib
import json
import re
import threading
import time
from collections import OrderedDict, deque
from datetime import datetime, timezone
from urllib.parse import quote

import httpx

from app.application.errors import UseCaseError
from app.domain.services.skills import skill_key

USERNAME = r"[A-Za-z0-9][A-Za-z0-9_. -]{0,79}"
NOTICE = "Codewars informa actividad y rangos en retos de programación. No verifica la titularidad de esta cuenta ni certifica dominio profesional."
ALIASES = {"csharp": "c#", "cpp": "c++", "shell": "bash"}


def _count(value):
    if type(value) is not int or not 0 <= value <= 100_000_000:
        raise ValueError("Invalid count")
    return value


def _rank(value):
    if value is None:
        return {"rank": "Sin rango", "score": 0}
    if not isinstance(value, dict):
        raise ValueError("Invalid rank")
    rank, score = value.get("rank"), _count(value.get("score", 0))
    if rank is None:
        return {"rank": "Sin rango", "score": score}
    if type(rank) is not int or rank == 0 or not -8 <= rank <= 8:
        raise ValueError("Invalid rank")
    return {"rank": f"{-rank} kyu" if rank < 0 else f"{rank} dan", "score": score}


class CodewarsReader:
    def __init__(self, settings, transport=None):
        self.settings, self.transport = settings, transport
        self._lock, self._cache, self._calls = threading.Lock(), OrderedDict(), deque()

    def inspect(self, username):
        if not self.settings.codewars_enabled:
            raise UseCaseError(status_code=503, detail="La consulta de Codewars está desactivada en este entorno.")
        username = username.strip()
        if not re.fullmatch(USERNAME, username):
            raise UseCaseError(status_code=422, detail="Indica solo el nombre de usuario de Codewars, no su URL.")
        key = username.casefold()
        with self._lock:
            now = time.monotonic()
            cached = self._cache.get(key)
            if cached and cached[0] > now:
                return copy.deepcopy(cached[1])
            while self._calls and self._calls[0] < now - 3600:
                self._calls.popleft()
            if len(self._calls) >= 50:
                raise UseCaseError(status_code=503, detail="Se alcanzó el presupuesto local de consultas a Codewars. Intenta más tarde.")
            self._calls.append(now)
        try:
            with httpx.Client(timeout=httpx.Timeout(8, connect=3), follow_redirects=False,
                              trust_env=False, transport=self.transport) as client:
                with client.stream("GET", f"https://www.codewars.com/api/v1/users/{quote(username, safe='')}", headers={"Accept": "application/json"}) as response:
                    if response.status_code == 404:
                        raise UseCaseError(status_code=422, detail="No encontramos ese usuario público de Codewars. Revisa el nombre.")
                    if response.status_code != 200:
                        raise UseCaseError(status_code=503, detail="Codewars no está disponible o limitó las consultas. Intenta más tarde.")
                    raw = bytearray()
                    for chunk in response.iter_bytes(chunk_size=16384):
                        raw.extend(chunk)
                        if len(raw) > 131072:
                            raise ValueError("Response limit")
                    report = self._report(json.loads(raw))
        except (httpx.HTTPError, ValueError, TypeError, KeyError, AttributeError):
            raise UseCaseError(status_code=503, detail="No pudimos interpretar la respuesta de Codewars. Prueba más tarde o registra una referencia manual.") from None
        with self._lock:
            self._cache[key] = (time.monotonic() + 600, copy.deepcopy(report))
            while len(self._cache) > 32:
                self._cache.popitem(last=False)
        return report

    @staticmethod
    def _report(value):
        username = value["username"]
        if not isinstance(username, str) or not re.fullmatch(USERNAME, username):
            raise ValueError("Invalid username")
        ranks = value.get("ranks") or {}
        languages = ranks.get("languages") or {}
        if not isinstance(languages, dict) or len(languages) > 100:
            raise ValueError("Invalid languages")
        signals = []
        for language, rank in sorted(languages.items()):
            if not re.fullmatch(r"[a-z][a-z0-9-]{0,29}", language):
                continue
            try:
                details = _rank(rank)
            except (ValueError, TypeError):
                continue
            if details["score"] > 0 and details["rank"] != "Sin rango":
                signals.append({"skill": skill_key(ALIASES.get(language, language)), **details})
        report = {"origin": "codewars_public", "version": "codewars-v1", "username": username,
                  "profile_url": f"https://www.codewars.com/users/{quote(username, safe='')}",
                  "overall": _rank(ranks.get("overall")),
                  "completed_challenges": _count(value["codeChallenges"]["totalCompleted"]),
                  "signals": signals[:20], "truncated": len(signals) > 20}
        report["fingerprint"] = hashlib.sha256(json.dumps(report, sort_keys=True).encode()).hexdigest()
        report.update(fetched_at=datetime.now(timezone.utc).isoformat(), notice=NOTICE)
        return report
