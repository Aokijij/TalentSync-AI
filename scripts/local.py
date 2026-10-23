"""Isolated local commands. Uses only .local/ and never reads backend/.env."""
import argparse
import json
import os
import secrets
import subprocess
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
LOCAL = ROOT / ".local"
PYTHON = ROOT / "backend/.venv/Scripts/python.exe"
ENV_FILE = LOCAL / "backend.env"

SOCIAL_PROVIDERS = ("google", "github", "linkedin")
INTEGRATION_KEYS = {
    "INTEGRATIONS_ENABLED", "INTEGRATION_MAIL_TRANSPORT", "PUBLIC_APP_URL",
    "CALENDAR_SYNC_ENABLED", "CALENDAR_GOOGLE_CLIENT_ID", "CALENDAR_GOOGLE_CLIENT_SECRET",
    "RESEND_API_KEY", "RESEND_FROM", "RESEND_WEBHOOK_SECRET",
    "SMTP_HOST", "SMTP_PORT", "SMTP_SECURITY", "SMTP_USERNAME", "SMTP_PASSWORD", "SMTP_FROM",
    *(f"OAUTH_{provider.upper()}_CLIENT_{part}" for provider in SOCIAL_PROVIDERS for part in ("ID", "SECRET")),
}


def integration_overrides(path):
    """Explicit, private opt-in. Never inherit credentials from the parent shell."""
    if not path.exists():
        return {}
    values = {}
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        key, separator, value = line.partition("=")
        key, value = key.strip(), value.strip()
        if not separator or key not in INTEGRATION_KEYS or key in values:
            raise SystemExit("Revisa .local/integrations.env: claves desconocidas, duplicadas o línea inválida.")
        values[key] = value
    if values.pop("INTEGRATIONS_ENABLED", "false") != "true":
        return {}
    transport = values.pop("INTEGRATION_MAIL_TRANSPORT", "local")
    if transport not in {"local", "resend", "smtp"}:
        raise SystemExit("Selecciona correo local, resend o smtp en .local/integrations.env.")
    origin = values.get("PUBLIC_APP_URL", "http://127.0.0.1:5173").rstrip("/")
    try:
        url = urlsplit(origin)
        _ = url.port
        valid = url.scheme in {"http", "https"} and url.hostname in {"localhost", "127.0.0.1"}
        valid = valid and not (url.username or url.password or url.path or url.query or url.fragment)
    except ValueError:
        valid = False
    if not valid:
        raise SystemExit("El arranque local requiere un origen loopback. Configura el dominio público en el entorno de despliegue.")
    if transport == "resend" and (not values.get("RESEND_API_KEY") or not values.get("RESEND_FROM")
                                    or values["RESEND_FROM"].casefold().endswith("@resend.dev")):
        raise SystemExit("El correo de cuentas requiere clave y remitente propio verificado; resend.dev solo sirve para la prueba aislada.")
    if transport == "smtp" and (not values.get("SMTP_HOST") or not values.get("SMTP_FROM")):
        raise SystemExit("El correo SMTP requiere servidor y remitente.")
    return {**values, "PUBLIC_APP_URL": origin, "CORS_ORIGINS": json.dumps([origin]),
            "SESSION_COOKIE_SECURE": str(url.scheme == "https").lower(),
            "LOCAL_MAIL_ENABLED": str(transport == "local").lower(),
            "RESEND_ENABLED": str(transport == "resend").lower(),
            "SMTP_ENABLED": str(transport == "smtp").lower()}


def integration_status(env):
    """Configuration report only. No secrets, network calls, messages or DB writes."""
    origin = env["PUBLIC_APP_URL"].rstrip("/")
    providers = {}
    for provider in SOCIAL_PROVIDERS:
        prefix = f"OAUTH_{provider.upper()}_CLIENT_"
        complete = all(env.get(prefix + part) for part in ("ID", "SECRET"))
        state = "configured" if complete else "missing_credentials"
        if complete and provider == "linkedin" and not origin.startswith("https://"):
            state = "requires_https"
        providers[provider] = {"state": state, "callback": f"{origin}/api/v1/auth/social/{provider}/callback"}
    calendar = bool(env.get("CALENDAR_GOOGLE_CLIENT_ID") and env.get("CALENDAR_GOOGLE_CLIENT_SECRET"))
    return {"origin": origin, "providers": providers,
            "calendar": {"state": "configured" if calendar and env.get("CALENDAR_SYNC_ENABLED") == "true" else "disabled" if calendar else "missing_credentials",
                         "callback": f"{origin}/api/v1/account/calendar/google/callback"},
            "mail": "resend" if env.get("RESEND_ENABLED") == "true" else "smtp" if env.get("SMTP_ENABLED") == "true" else "local",
            "delivery_webhook": {"configured": bool(env.get("RESEND_WEBHOOK_SECRET")),
                                 "path": "/api/v1/webhooks/resend"},
            "verification": "configuration_only; complete real consent and delivery checks after setup"}


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
                   "PUBLIC_LEARNING_REFRESH_ENABLED": values.get("PUBLIC_LEARNING_REFRESH_ENABLED", "false"),
                   "YOUTUBE_LEARNING_ENABLED": values.get("YOUTUBE_LEARNING_ENABLED", "false"),
                   "YOUTUBE_API_KEY": values.get("YOUTUBE_API_KEY", ""),
                   "YOUTUBE_LEARNING_DAILY_REQUESTS": values.get("YOUTUBE_LEARNING_DAILY_REQUESTS", "100"),
                   "CALENDAR_SYNC_ENABLED": values.get("CALENDAR_SYNC_ENABLED", "false"),
                   "CALENDAR_GOOGLE_CLIENT_ID": values.get("CALENDAR_GOOGLE_CLIENT_ID", ""),
                   "CALENDAR_GOOGLE_CLIENT_SECRET": values.get("CALENDAR_GOOGLE_CLIENT_SECRET", ""),
                   "ACCOUNT_CLEANUP_ENABLED": values.get("ACCOUNT_CLEANUP_ENABLED", "true"),
                   "ACCOUNT_RETENTION_ENABLED": values.get("ACCOUNT_RETENTION_ENABLED", "false"),
                   "RESEND_WEBHOOK_SECRET": "",
                   "RESEND_ENABLED": "false", "RESEND_API_KEY": "", "RESEND_FROM": "",
                   **{key: values.get(key, "false" if key == "LEARN_ENABLED" else "") for key in (
                       "LEARN_ENABLED", "LEARN_TENANT_ID", "LEARN_CLIENT_ID", "LEARN_CLIENT_SECRET")},
                   "SMTP_ENABLED": "false", "SMTP_HOST": "", "SMTP_USERNAME": "", "SMTP_PASSWORD": "", "SMTP_FROM": "",
                   "SMTP_PORT": "587", "SMTP_SECURITY": "starttls",
                   "SESSION_AUTH_ENABLED": "true", "LOCAL_MAIL_ENABLED": "true",
                   "LOCAL_MFA_REVIEW_ENABLED": "true", "COMPANY_MFA_REQUIRED": "false",
                   "WORKFLOW_MAINTENANCE_ENABLED": "true",
                   "MODEL_MAINTENANCE_ENABLED": "true", "MATCH_MODEL_PATH": values.get("MATCH_MODEL_PATH", ""),
                   "CAREER_WRITER_MODEL": values.get("CAREER_WRITER_MODEL", ""),
                   "CAREER_WRITER_EXECUTABLE": values.get("CAREER_WRITER_EXECUTABLE", ""),
                   "MATCH_MODEL_CPU_THREADS": values.get("MATCH_MODEL_CPU_THREADS", "2"),
                   "CV_ENTITY_MODEL_PATH": values.get("CV_ENTITY_MODEL_PATH", ""),
                   "CV_ENTITY_PYTHON": values.get("CV_ENTITY_PYTHON", ""),
                   "GITHUB_PROJECT_ANALYSIS_ENABLED": values.get("GITHUB_PROJECT_ANALYSIS_ENABLED", "false"),
                   "CODEWARS_ENABLED": values.get("CODEWARS_ENABLED", "false"),
                   "WORKSPACE_DOMAIN": values.get("WORKSPACE_DOMAIN", ""),
                   "ADMIN_SSO_REQUIRED": values.get("ADMIN_SSO_REQUIRED", "false"),
                   "ADMIN_SSO_PROVIDER": values.get("ADMIN_SSO_PROVIDER", "workspace"),
                   "ENTRA_TENANT_ID": values.get("ENTRA_TENANT_ID", ""),
                   "WEBRTC_STUN_URLS": values.get("WEBRTC_STUN_URLS", "[]"),
                   "WEBRTC_TURN_URLS": values.get("WEBRTC_TURN_URLS", "[]"),
                   "WEBRTC_TURN_SECRET": values.get("WEBRTC_TURN_SECRET", ""),
                   "WEBRTC_RELAY_ONLY": values.get("WEBRTC_RELAY_ONLY", "false"),
                   **{key: values.get(key, "") for key in ("OAUTH_GITHUB_CLIENT_ID", "OAUTH_GITHUB_CLIENT_SECRET",
                                                           "OAUTH_GOOGLE_CLIENT_ID", "OAUTH_GOOGLE_CLIENT_SECRET",
                                                           "OAUTH_LINKEDIN_CLIENT_ID", "OAUTH_LINKEDIN_CLIENT_SECRET",
                                                           "OAUTH_WORKSPACE_CLIENT_ID", "OAUTH_WORKSPACE_CLIENT_SECRET",
                                                           "OAUTH_ENTRA_CLIENT_ID", "OAUTH_ENTRA_CLIENT_SECRET")},
                   "SESSION_COOKIE_SECURE": "false", "PUBLIC_APP_URL": "http://127.0.0.1:5173",
                   "AZURE_STORAGE_ACCOUNT_URL": "", "JSEARCH_API_KEY": "", "ADZUNA_APP_ID": "",
                   "ADZUNA_APP_KEY": "", "JOOBLE_API_KEY": "", "STATIC_DIR": ""})
    if not testing:
        values.update(integration_overrides(LOCAL / "integrations.env"))
    if testing:
        # Tests must not depend on user integrations, weights or the demo database.
        values.update({"CALENDAR_SYNC_ENABLED": "false", "CALENDAR_GOOGLE_CLIENT_ID": "", "CALENDAR_GOOGLE_CLIENT_SECRET": "", "ACCOUNT_RETENTION_ENABLED": "false", "ACCOUNT_CLEANUP_ENABLED": "false"})
        values.update({"DATABASE_URL": "sqlite://", "MATCH_MODEL_PATH": "", "CV_ENTITY_MODEL_PATH": "", "CV_ENTITY_PYTHON": "",
                       "CAREER_WRITER_MODEL": "", "CAREER_WRITER_EXECUTABLE": "",
                       "PUBLIC_LEARNING_REFRESH_ENABLED": "false",
                       "YOUTUBE_LEARNING_ENABLED": "false", "YOUTUBE_API_KEY": "", "YOUTUBE_LEARNING_DAILY_REQUESTS": "100",
                       "LEARN_ENABLED": "false", "LEARN_TENANT_ID": "", "LEARN_CLIENT_ID": "", "LEARN_CLIENT_SECRET": "",
                       "SESSION_AUTH_ENABLED": "false", "LOCAL_MAIL_ENABLED": "false", "LOCAL_ADMIN_REVIEW_ENABLED": "false", "LOCAL_MFA_REVIEW_ENABLED": "false", "COMPANY_MFA_REQUIRED": "true",
                       "WORKFLOW_MAINTENANCE_ENABLED": "false", "MODEL_MAINTENANCE_ENABLED": "false",
                       "GITHUB_PROJECT_ANALYSIS_ENABLED": "false", "WORKSPACE_DOMAIN": "",
                       "CODEWARS_ENABLED": "false",
                       "ADMIN_SSO_REQUIRED": "false", "ADMIN_SSO_PROVIDER": "workspace", "ENTRA_TENANT_ID": "",
                       "WEBRTC_STUN_URLS": "[]", "WEBRTC_TURN_URLS": "[]",
                       "WEBRTC_TURN_SECRET": "", "WEBRTC_RELAY_ONLY": "false",
                       **{key: "" for key in values if key.startswith("OAUTH_")}})
    return {**os.environ, **values}


def main():
    parser = argparse.ArgumentParser(description="TalentSync: entorno local aislado")
    parser.add_argument("command", choices=("setup", "backend", "test", "seed", "seed-review", "seed-demo", "seed-scenarios", "seed-quality", "seed-radar", "reset-realistic", "enrich-realistic", "seed-skill-levels", "seed-education", "sync-education", "accounts", "admin-sso", "model-prepare", "model-check", "cv-runtime", "cv-model-prepare", "cv-model-check", "cv-evaluate", "doctor", "verify", "rehearse", "integrations"))
    parser.add_argument("options", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if args.options and args.command not in {"admin-sso", "integrations"}:
        parser.error("Solo admin-sso e integrations admiten argumentos adicionales")
    if args.command == "integrations":
        if args.options not in ([], ["--init"]):
            parser.error("Usa integrations o integrations --init")
        if args.options:
            LOCAL.mkdir(exist_ok=True)
            target = LOCAL / "integrations.env"
            try:
                with target.open("x", encoding="utf-8") as destination:
                    destination.write((ROOT / "backend/local-integrations.env.example").read_text(encoding="utf-8"))
            except FileExistsError:
                print("Se conserva .local/integrations.env existente.")
        print(json.dumps(integration_status(prepare_environment()), indent=2, ensure_ascii=False))
        return
    if args.command in {"doctor", "verify", "rehearse"}:
        if not PYTHON.is_file():
            raise SystemExit("Falta backend/.venv. Instala requirements-lite.txt y requirements-dev.txt.")
        command = [str(ROOT / "scripts/local_rehearsal.py")] if args.command == "rehearse" else [str(ROOT / "scripts/local_checks.py"), args.command]
        raise SystemExit(subprocess.call([str(PYTHON), *command], cwd=ROOT))
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
        "seed-review": ["-m", "scripts.seed_review"],
        "seed-demo": ["-m", "scripts.seed_rich_demo"],
        "seed-scenarios": ["-m", "scripts.seed_scenarios"],
        "seed-quality": ["-m", "scripts.seed_offer_quality"],
        "seed-radar": ["-m", "scripts.seed_market_radar"],
        "reset-realistic": ["-m", "scripts.seed_realistic"],
        "enrich-realistic": ["-m", "scripts.enrich_realistic"],
        "seed-skill-levels": ["-m", "scripts.seed_skill_levels"],
        "seed-education": ["-m", "scripts.seed_education_catalog"],
        "sync-education": ["-m", "scripts.sync_education_sources"],
        "admin-sso": ["-m", "scripts.admin_sso", *args.options],
        "model-prepare": ["-m", "scripts.local_model", "prepare"],
        "model-check": ["-m", "scripts.local_model", "check"],
        "cv-runtime": [str(ROOT / "scripts/cv_runtime.py")],
        "cv-model-prepare": ["-m", "scripts.cv_model", "prepare"],
        "cv-model-check": ["-m", "scripts.cv_model", "check"],
        "cv-evaluate": ["-m", "scripts.evaluate_cv_entities"],
    }
    if args.command == "accounts":
        realistic_file = LOCAL / "realistic-accounts.json"
        if realistic_file.exists():
            realistic = json.loads(realistic_file.read_text(encoding="utf-8"))
            for account in realistic["accounts"]:
                print(f"{account['type']}: {account['email']} / {realistic['password']}")
            return
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
