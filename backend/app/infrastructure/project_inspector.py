import hashlib
import io
import stat
import zipfile
import zlib
from pathlib import PurePosixPath

from app.application.errors import UseCaseError
from app.domain.services.project_analysis import analyze, manifest_kind

MAX_UPLOAD = 8 * 1024 * 1024
MAX_UNPACKED = 32 * 1024 * 1024
MAX_MANIFEST = 256 * 1024
IGNORED = {".git", "node_modules", "venv", ".venv", "vendor", "dist", "build", "coverage", "__pycache__", "__macosx"}


class ProjectInspector:
    def inspect(self, file):
        if not (file.filename or "").casefold().endswith(".zip"):
            raise UseCaseError(status_code=422, detail="Selecciona un archivo ZIP de proyecto")
        blob = file.file.read(MAX_UPLOAD + 1)
        if len(blob) > MAX_UPLOAD:
            raise UseCaseError(status_code=413, detail="El ZIP puede ocupar como máximo 8 MiB")
        try:
            with zipfile.ZipFile(io.BytesIO(blob)) as archive:
                items = archive.infolist()
                if len(items) > 2000 or sum(row.file_size for row in items) > MAX_UNPACKED:
                    raise ValueError("Archive limits")
                files, manifests, seen, ignored = [], {}, set(), 0
                for row in items:
                    name = row.orig_filename
                    path = PurePosixPath(name)
                    if (not name or len(name) > 300 or "\x00" in name or "\\" in name or ":" in name
                            or path.is_absolute() or ".." in path.parts or len(path.parts) > 20
                            or stat.S_ISLNK(row.external_attr >> 16) or row.flag_bits & 1
                            or row.compress_type not in {zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED}
                            or (row.file_size > 0 and row.file_size / max(1, row.compress_size) > 200)):
                        raise ValueError("Unsafe archive entry")
                    if row.is_dir():
                        continue
                    normalized = str(path).casefold()
                    if normalized in seen:
                        raise ValueError("Ambiguous archive entries")
                    seen.add(normalized)
                    if any(part.casefold() in IGNORED for part in path.parts) or path.name.startswith("."):
                        ignored += 1
                        continue
                    files.append(str(path))
                    if manifest_kind(str(path)):
                        if row.file_size > MAX_MANIFEST or len(manifests) >= 32:
                            raise ValueError("Manifest limits")
                        with archive.open(row) as stream:
                            raw = stream.read(MAX_MANIFEST + 1)
                        if len(raw) > MAX_MANIFEST:
                            raise ValueError("Manifest limits")
                        manifests[str(path)] = raw
                report = analyze(files, manifests)
                report.update(fingerprint=hashlib.sha256(blob).hexdigest(), files_considered=len(files),
                              files_ignored=ignored, manifests_read=len(manifests))
                return report
        except (zipfile.BadZipFile, zipfile.LargeZipFile, ValueError, RuntimeError, OSError, EOFError, zlib.error, NotImplementedError):
            raise UseCaseError(status_code=422, detail="ZIP inválido o fuera de los límites: 2.000 entradas, 32 MiB descomprimidos, 32 manifiestos de hasta 256 KiB y relación de compresión máxima 200:1. No admite rutas inseguras, enlaces ni cifrado.") from None
