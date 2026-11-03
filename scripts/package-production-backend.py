"""Package source from an explicit allowlist, including authorized working changes."""
import hashlib
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SINGLE_FILES = (
    "alembic.ini", "requirements-lite.txt", "requirements.txt", "requirements-ocr.txt",
    "requirements-model-local-lock.txt", "requirements-cv-local.txt",
)


def main():
    destination = ROOT / ".local/aws-backend-release.tar.gz"
    destination.parent.mkdir(exist_ok=True)
    backend = ROOT / "backend"
    with tarfile.open(destination, "w:gz") as archive:
        for name in ("app", "alembic", "scripts", "legal_documents"):
            for file in sorted((backend / name).rglob("*")):
                if (file.is_file() and "__pycache__" not in file.parts
                        and file.suffix in {".py", ".json", ".csv", ".txt", ".md", ".ini", ".toml"}
                        and not file.is_symlink() and not file.name.startswith(".env")):
                    archive.add(file, arcname=file.relative_to(backend), recursive=False)
        for name in SINGLE_FILES:
            archive.add(backend / name, arcname=name, recursive=False)
        archive.add(ROOT / "infra/production/talentsync.service", arcname="deploy/talentsync.service")
    digest = hashlib.sha256(destination.read_bytes()).hexdigest()
    (ROOT / ".local/aws-backend-release.sha256").write_text(digest, encoding="ascii")
    print(f"Backend source bundle: {destination.stat().st_size} bytes; SHA256: {digest}")


if __name__ == "__main__":
    main()
