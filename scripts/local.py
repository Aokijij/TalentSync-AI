"""Isolated local commands. Uses only .local/ and never reads backend/.env."""
import argparse
import json
import os
import secrets
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCAL = ROOT / ".local"
PYTHON = ROOT / "backend/.venv/Scripts/python.exe"
ENV_FILE = LOCAL / "backend.env"


def prepare_environment():
    LOCAL.mkdir(exist_ok=True)
    if not ENV_FILE.exists():
        values = {
            "ENVIRONMENT": "development",
            "DATABASE_URL": f"sqlite:///{(LOCAL / 'talentsync.sqlite3').as_posix()}",
            "SECRET_KEY": secrets.token_urlsafe(48),
            "UPLOAD_DIR": (LOCAL / "uploads").as_posix(),
            "CV_PARSER": "pypdf", "CV_OCR_ENABLED": "false",
            "PERIODIC_MAINTENANCE_ENABLED": "false",
            "AZURE_STORAGE_ACCOUNT_URL": "", "STATIC_DIR": "",
            "JSEARCH_API_KEY": "", "ADZUNA_APP_ID": "", "ADZUNA_APP_KEY": "",
            "JOOBLE_API_KEY": "",
            "ALLOWED_HOSTS": '["127.0.0.1","localhost","testserver"]',
            "CORS_ORIGINS": '["http://127.0.0.1:5173","http://localhost:5173"]',
        }
        ENV_FILE.write_text("\n".join(f"{key}={value}" for key, value in values.items()) + "\n", encoding="utf-8")
    values = dict(line.split("=", 1) for line in ENV_FILE.read_text(encoding="utf-8").splitlines() if line and not line.startswith("#"))
    expected = f"sqlite:///{(LOCAL / 'talentsync.sqlite3').as_posix()}"
    if values.get("DATABASE_URL") != expected or values.get("ENVIRONMENT") != "development":
        raise SystemExit("El entorno aislado requiere su propia base SQLite y ENVIRONMENT=development.")
    # Explicit values also override inherited shell variables and dotenv files.
    values.update({"TALENTSYNC_ENV_FILE": str(ENV_FILE), "PERIODIC_MAINTENANCE_ENABLED": "false",
                   "SESSION_AUTH_ENABLED": "true", "LOCAL_MAIL_ENABLED": "true",
                   "WORKFLOW_MAINTENANCE_ENABLED": "true",
                   "MODEL_MAINTENANCE_ENABLED": "true", "MATCH_MODEL_PATH": values.get("MATCH_MODEL_PATH", ""),
                   "GITHUB_PROJECT_ANALYSIS_ENABLED": values.get("GITHUB_PROJECT_ANALYSIS_ENABLED", "false"),
                   **{key: values.get(key, "") for key in ("OAUTH_GITHUB_CLIENT_ID", "OAUTH_GITHUB_CLIENT_SECRET",
                                                           "OAUTH_GOOGLE_CLIENT_ID", "OAUTH_GOOGLE_CLIENT_SECRET",
                                                           "OAUTH_LINKEDIN_CLIENT_ID", "OAUTH_LINKEDIN_CLIENT_SECRET")},
                   "SESSION_COOKIE_SECURE": "false", "PUBLIC_APP_URL": "http://127.0.0.1:5173",
                   "AZURE_STORAGE_ACCOUNT_URL": "", "JSEARCH_API_KEY": "", "ADZUNA_APP_ID": "",
                   "ADZUNA_APP_KEY": "", "JOOBLE_API_KEY": "", "STATIC_DIR": ""})
    return {**os.environ, **values}


def main():
    parser = argparse.ArgumentParser(description="TalentSync: entorno local aislado")
    parser.add_argument("command", choices=("setup", "backend", "test", "seed", "accounts"))
    args = parser.parse_args()
    env = prepare_environment()
    commands = {
        "setup": ["-m", "alembic", "upgrade", "head"],
        "backend": ["-m", "uvicorn", "app.main:app", "--reload", "--reload-dir", "app",
                    "--reload-exclude", str(ROOT / "backend/tests"),
                    "--reload-exclude", str(ROOT / "backend/scripts"),
                    "--reload-exclude", str(ROOT / "backend/alembic"),
                    "--reload-exclude", str(ROOT / "backend/.venv"),
                    "--host", "127.0.0.1", "--port", "8000"],
        "test": ["-m", "pytest", "-q", "-p", "no:cacheprovider"],
        "seed": ["-m", "scripts.seed_local"],
    }
    if args.command == "accounts":
        account_file = LOCAL / "accounts.json"
        if not account_file.exists():
            raise SystemExit("Ejecuta primero el comando seed.")
        for account in json.loads(account_file.read_text(encoding="utf-8")):
            print(f"{account['role']}: {account['email']} / {account['password']}")
        return
    if not PYTHON.is_file():
        raise SystemExit("Falta backend/.venv. Instala requirements-lite.txt y requirements-dev.txt.")
    raise SystemExit(subprocess.call([str(PYTHON), *commands[args.command]], cwd=ROOT / "backend", env=env))


if __name__ == "__main__":
    main()
