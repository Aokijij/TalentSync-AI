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


def prepare_environment(*, testing=False):
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
                   "MATCH_MODEL_CPU_THREADS": values.get("MATCH_MODEL_CPU_THREADS", "2"),
                   "GITHUB_PROJECT_ANALYSIS_ENABLED": values.get("GITHUB_PROJECT_ANALYSIS_ENABLED", "false"),
                   "WORKSPACE_DOMAIN": values.get("WORKSPACE_DOMAIN", ""),
                   "ADMIN_SSO_REQUIRED": values.get("ADMIN_SSO_REQUIRED", "false"),
                   "WEBRTC_STUN_URLS": values.get("WEBRTC_STUN_URLS", "[]"),
                   "WEBRTC_TURN_URLS": values.get("WEBRTC_TURN_URLS", "[]"),
                   "WEBRTC_TURN_SECRET": values.get("WEBRTC_TURN_SECRET", ""),
                   "WEBRTC_RELAY_ONLY": values.get("WEBRTC_RELAY_ONLY", "false"),
                   **{key: values.get(key, "") for key in ("OAUTH_GITHUB_CLIENT_ID", "OAUTH_GITHUB_CLIENT_SECRET",
                                                           "OAUTH_GOOGLE_CLIENT_ID", "OAUTH_GOOGLE_CLIENT_SECRET",
                                                           "OAUTH_LINKEDIN_CLIENT_ID", "OAUTH_LINKEDIN_CLIENT_SECRET",
                                                           "OAUTH_WORKSPACE_CLIENT_ID", "OAUTH_WORKSPACE_CLIENT_SECRET")},
                   "SESSION_COOKIE_SECURE": "false", "PUBLIC_APP_URL": "http://127.0.0.1:5173",
                   "AZURE_STORAGE_ACCOUNT_URL": "", "JSEARCH_API_KEY": "", "ADZUNA_APP_ID": "",
                   "ADZUNA_APP_KEY": "", "JOOBLE_API_KEY": "", "STATIC_DIR": ""})
    if testing:
        # Tests must not depend on user integrations, weights or the demo database.
        values.update({"DATABASE_URL": "sqlite://", "MATCH_MODEL_PATH": "",
                       "SESSION_AUTH_ENABLED": "false", "LOCAL_MAIL_ENABLED": "false",
                       "WORKFLOW_MAINTENANCE_ENABLED": "false", "MODEL_MAINTENANCE_ENABLED": "false",
                       "GITHUB_PROJECT_ANALYSIS_ENABLED": "false", "WORKSPACE_DOMAIN": "",
                       "ADMIN_SSO_REQUIRED": "false", "WEBRTC_STUN_URLS": "[]", "WEBRTC_TURN_URLS": "[]",
                       "WEBRTC_TURN_SECRET": "", "WEBRTC_RELAY_ONLY": "false",
                       **{key: "" for key in values if key.startswith("OAUTH_")}})
    return {**os.environ, **values}


def main():
    parser = argparse.ArgumentParser(description="TalentSync: entorno local aislado")
    parser.add_argument("command", choices=("setup", "backend", "test", "seed", "accounts", "admin-sso", "model-prepare", "model-check"))
    parser.add_argument("options", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if args.options and args.command != "admin-sso":
        parser.error("Solo admin-sso admite argumentos adicionales")
    env = prepare_environment(testing=args.command == "test")
    commands = {
        "setup": ["-m", "alembic", "upgrade", "head"],
        "backend": ["-m", "uvicorn", "app.main:app", "--no-access-log", "--reload", "--reload-dir", "app",
                    "--reload-exclude", str(ROOT / "backend/tests"),
                    "--reload-exclude", str(ROOT / "backend/scripts"),
                    "--reload-exclude", str(ROOT / "backend/alembic"),
                    "--reload-exclude", str(ROOT / "backend/.venv"),
                    "--host", "127.0.0.1", "--port", "8000"],
        "test": ["-m", "pytest", "-q", "-p", "no:cacheprovider", "--disable-warnings", "-W", "error::sqlalchemy.exc.SAWarning"],
        "seed": ["-m", "scripts.seed_local"],
        "admin-sso": ["-m", "scripts.admin_sso", *args.options],
        "model-prepare": ["-m", "scripts.local_model", "prepare"],
        "model-check": ["-m", "scripts.local_model", "check"],
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
