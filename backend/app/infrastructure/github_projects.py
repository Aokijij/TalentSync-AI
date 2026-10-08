"""Opt-in public GitHub metadata and manifest reader. No clone, source execution or credentials."""
import base64
import hashlib
import json
import re
import time
from pathlib import PurePosixPath
from urllib.parse import urlsplit

import httpx

from app.application.errors import UseCaseError
from app.domain.services.project_analysis import analyze, manifest_kind
from app.infrastructure.project_inspector import IGNORED, MAX_MANIFEST


class GitHubProjectInspector:
    def __init__(self, settings, transport=None):
        self.settings = settings
        self.transport = transport

    @staticmethod
    def repository(url):
        try:
            parsed = urlsplit(url)
            parts = parsed.path.strip("/").split("/")
            if (parsed.scheme != "https" or parsed.netloc != "github.com" or parsed.query or parsed.fragment
                    or len(parts) != 2 or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9-]{0,38}", parts[0])
                    or not re.fullmatch(r"[A-Za-z0-9_.-]{1,100}", parts[1]) or parts[1] in {".", ".."}):
                raise ValueError()
            owner, repo = parts
            if repo.endswith(".git"):
                repo = repo[:-4]
            if not repo or repo in {".", ".."}:
                raise ValueError()
            return owner, repo
        except ValueError:
            raise UseCaseError(status_code=422, detail="Usa la URL raíz HTTPS de un repositorio público: https://github.com/propietario/repositorio") from None

    @staticmethod
    def _json(client, path, limit=1_000_000):
        with client.stream("GET", f"https://api.github.com{path}", headers={"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}) as response:
            if response.status_code in {403, 429}:
                raise UseCaseError(status_code=503, detail="GitHub limitó temporalmente las consultas públicas. Prueba más tarde o usa un ZIP local.")
            if response.status_code == 404:
                raise UseCaseError(status_code=422, detail="No encontramos un repositorio público accesible con contenido")
            response.raise_for_status()
            body = bytearray()
            for chunk in response.iter_bytes(chunk_size=16384):
                body.extend(chunk)
                if len(body) > limit:
                    raise ValueError("Response limit")
            return json.loads(body)

    def inspect(self, url):
        if not self.settings.github_project_analysis_enabled:
            raise UseCaseError(status_code=503, detail="La lectura de GitHub está desactivada; puedes analizar un ZIP local")
        owner, repo = self.repository(url)
        root = f"/repos/{owner}/{repo}"
        deadline = time.monotonic() + 30
        def fetch(client, path, limit=1_000_000):
            if time.monotonic() >= deadline:
                raise UseCaseError(status_code=503, detail="La consulta de GitHub tardó demasiado. Prueba más tarde o usa un ZIP local.")
            return self._json(client, path, limit)
        try:
            with httpx.Client(timeout=httpx.Timeout(8, connect=3), follow_redirects=False, trust_env=False, transport=self.transport) as client:
                commit = fetch(client, f"{root}/commits/HEAD")
                revision, tree_sha = commit["sha"], commit["commit"]["tree"]["sha"]
                if not all(isinstance(sha, str) and re.fullmatch(r"[a-f0-9]{40}", sha) for sha in (revision, tree_sha)):
                    raise ValueError("Invalid object identity")
                tree = fetch(client, f"{root}/git/trees/{tree_sha}?recursive=1")
                if tree.get("truncated") is not False or len(tree["tree"]) > 2000:
                    raise ValueError("Incomplete or oversized tree")
                files, manifests, seen, ignored = [], {}, set(), 0
                for row in tree["tree"]:
                    if row["type"] != "blob" or row.get("mode") not in {"100644", "100755"}:
                        continue
                    name = row["path"]
                    path = PurePosixPath(name)
                    if (len(name) > 300 or "\x00" in name or "\\" in name or ":" in name or path.is_absolute()
                            or ".." in path.parts or len(path.parts) > 20 or str(path).casefold() in seen):
                        raise ValueError("Unsafe path")
                    seen.add(str(path).casefold())
                    if any(part.casefold() in IGNORED for part in path.parts) or path.name.startswith("."):
                        ignored += 1
                        continue
                    files.append(str(path))
                    if manifest_kind(str(path)):
                        if not isinstance(row.get("size"), int) or not 0 <= row["size"] <= MAX_MANIFEST or len(manifests) >= 32:
                            raise ValueError("Manifest limits")
                        sha = row["sha"]
                        if not isinstance(sha, str) or not re.fullmatch(r"[a-f0-9]{40}", sha):
                            raise ValueError("Invalid blob identity")
                        blob = fetch(client, f"{root}/git/blobs/{sha}", limit=400_000)
                        if blob.get("encoding") != "base64" or blob.get("sha") != sha:
                            raise ValueError("Unexpected blob")
                        raw = base64.b64decode("".join(blob["content"].split()), validate=True)
                        if len(raw) > MAX_MANIFEST or len(raw) != row["size"]:
                            raise ValueError("Manifest size mismatch")
                        manifests[str(path)] = raw
                report = analyze(files, manifests)
                report.update(fingerprint=hashlib.sha256(f"github-public:{owner.casefold()}/{repo.casefold()}:{revision}".encode()).hexdigest(),
                    origin="github_public", repository_url=f"https://github.com/{owner}/{repo}", revision=revision,
                    files_considered=len(files), files_ignored=ignored, manifests_read=len(manifests))
                return report
        except (httpx.HTTPError, ValueError, TypeError, KeyError, AttributeError, RecursionError):
            raise UseCaseError(status_code=422, detail="No pudimos analizar el repositorio completo dentro de los límites: 2.000 entradas y 32 manifiestos de 256 KiB. No seguimos redirecciones. Puedes usar un ZIP local.") from None
