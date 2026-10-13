"""Install the optional CV runtime without changing backend matching packages."""
import subprocess
import venv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    folder = ROOT / ".local/cv-runtime"
    backend_packages = ROOT / "backend/.venv/Lib/site-packages"
    if not backend_packages.is_dir():
        raise SystemExit("Prepara primero backend/.venv")
    if not (folder / "Scripts/python.exe").exists():
        venv.EnvBuilder(with_pip=True).create(folder)
    packages = folder / "Lib/site-packages"
    (packages / "backend_shared.pth").write_text(str(backend_packages) + "\n", encoding="utf-8")
    raise SystemExit(subprocess.call([str(folder / "Scripts/python.exe"), "-m", "pip", "install", "-r", str(ROOT / "backend/requirements-cv-local.txt")]))


if __name__ == "__main__":
    main()
