"""Reproducible local checks. Never reads backend/.env, prints credentials or deploys."""
import argparse
import ast
import hashlib
import http.client
import json
import shutil
import sqlite3
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

import local


def node_executable():
    installed = shutil.which("node")
    bundled = Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe"
    return installed or (str(bundled) if bundled.is_file() else None)


def migration_head(root):
    revisions, parents = set(), set()
    for path in (root / "backend/alembic/versions").glob("*.py"):
        for node in ast.parse(path.read_text(encoding="utf-8")).body:
            if isinstance(node, (ast.Assign, ast.AnnAssign)):
                for target in node.targets if isinstance(node, ast.Assign) else [node.target]:
                    if isinstance(target, ast.Name) and target.id in {"revision", "down_revision"}:
                        value = ast.literal_eval(node.value)
                        if target.id == "revision":
                            revisions.add(value)
                        elif value:
                            parents.update(value if isinstance(value, tuple) else [value])
    heads = revisions - parents
    if len(heads) != 1:
        raise ValueError("Se requiere una única cabecera de migraciones")
    return heads.pop()


def http_probe(port, path, *, expected_json=None):
    # Fixed IPv4 loopback, no proxy inheritance and no redirects.
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=3)
    try:
        connection.request("GET", path)
        response = connection.getresponse()
        data = response.read(65536)
        if response.status != 200:
            return False
        if expected_json:
            payload = json.loads(data)
            return all(payload.get(key) == value for key, value in expected_json.items())
        return True
    except (OSError, ValueError, http.client.HTTPException):
        return False
    finally:
        connection.close()


def diagnose():
    checks = []

    def add(name, passed, detail, *, required=True):
        checks.append({"name": name, "passed": bool(passed), "required": required, "detail": detail})

    add("python", local.PYTHON.is_file(), "Entorno Python del proyecto")
    add("node", node_executable() is not None, "Node en PATH o runtime local conocido")
    frontend = local.ROOT / "frontend"
    add("frontend_dependencies", all((frontend / "node_modules" / item).is_file() for item in ["eslint/bin/eslint.js", "vite/bin/vite.js"]), "Dependencias frontend instaladas")
    env = None
    if local.ENV_FILE.is_file():
        try:
            env = local.prepare_environment()
        except (SystemExit, OSError, ValueError):
            pass
    add("isolated_environment", env is not None, "Configuración development con SQLite aislada; no se muestran claves")
    database = local.LOCAL / "talentsync.sqlite3"
    database_ok = False
    if database.is_file():
        try:
            with sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True, timeout=1) as connection:
                revision = connection.execute("SELECT version_num FROM alembic_version").fetchone()
                database_ok = revision == (migration_head(local.ROOT),) and connection.execute("PRAGMA quick_check").fetchone() == ("ok",)
        except (sqlite3.Error, OSError, ValueError):
            pass
    add("database", database_ok, "Base existente, íntegra y en la última migración; lectura sin escritura")
    add("demo_accounts", (local.LOCAL / "accounts.json").is_file(), "Semilla local disponible; credenciales excluidas del informe", required=False)
    if env and env.get("MATCH_MODEL_PATH"):
        folder = Path(env["MATCH_MODEL_PATH"])
        add("model_files", all((folder / name).is_file() for name in ["modules.json", "model.safetensors"]), "Pesos configurados presentes; verify comprueba la inferencia real")
    else:
        add("model_files", False, "Modelo neuronal sin configurar; el matching usa el método léxico", required=False)
    add("backend_http", http_probe(8000, "/health", expected_json={"status": "ok"}), "Servidor local en 127.0.0.1:8000", required=False)
    add("session_auth", http_probe(8000, "/api/v1/auth/options", expected_json={"mode": "session"}), "Backend local con sesiones opacas", required=False)
    add("frontend_http", http_probe(5173, "/"), "Frontend local en 127.0.0.1:5173", required=False)
    return {"ready": all(row["passed"] for row in checks if row["required"]), "checks": checks}


def source_fingerprint():
    digest = hashlib.sha256()
    result = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"], cwd=local.ROOT, capture_output=True, check=True)
    for filename in sorted(result.stdout.split(b"\0")):
        if filename:
            path = local.ROOT / filename.decode("utf-8")
            digest.update(filename + b"\0")
            digest.update(path.read_bytes() if path.is_file() else b"<deleted>")
            digest.update(b"\0")
    return digest.hexdigest()


def validation_steps(env, node):
    python = str(local.PYTHON)
    frontend = local.ROOT / "frontend"
    steps = [
        ("python_dependencies", [python, "-m", "pip", "check"], local.ROOT),
        ("python_lint", [python, "-m", "ruff", "check", "backend", "scripts"], local.ROOT),
        ("backend_tests", [python, "scripts/local.py", "test"], local.ROOT),
        ("frontend_tests", [node, "--test"], frontend),
        ("frontend_lint", [node, "node_modules/eslint/bin/eslint.js", "."], frontend),
        ("frontend_build", [node, "node_modules/vite/bin/vite.js", "build"], frontend),
    ]
    if env.get("MATCH_MODEL_PATH"):
        steps.append(("local_model", [python, "-m", "scripts.local_model", "check"], local.ROOT / "backend"))
    return steps


def verify():
    env = local.prepare_environment()
    # Build the same loopback-relative API as the development frontend.
    env.update(VITE_API_URL="/api/v1", HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1")
    node = node_executable()
    report = {"passed": False, "steps": [], "scope": "local; temporary test databases; no deployment or external login"}
    try:
        report["source_sha256"] = source_fingerprint()
        if not node:
            raise ValueError("Falta Node; instala las dependencias locales antes de verificar")
        for name, command, directory in validation_steps(env, node):
            print(f"\nComprobando {name}...", flush=True)
            started = time.perf_counter()
            result = subprocess.run(command, cwd=directory, env=env, check=False)
            report["steps"].append({"name": name, "passed": result.returncode == 0, "seconds": round(time.perf_counter() - started, 2)})
            if result.returncode:
                break
        else:
            report["passed"] = source_fingerprint() == report["source_sha256"]
            if not report["passed"]:
                report["error_type"] = "source_changed_during_validation"
                print("El código cambió durante las comprobaciones; vuelve a ejecutar verify.", flush=True)
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        report["error_type"] = type(error).__name__
        print("No se pudo completar la verificación. Revisa los runtimes y dependencias locales.", flush=True)
    save_report("validation", report)
    return 0 if report["passed"] else 1


def save_report(name, report):
    destination = local.LOCAL / "verification"
    destination.mkdir(parents=True, exist_ok=True)
    payload = {"created_at_utc": datetime.now(timezone.utc).isoformat(), **report}
    (destination / f"{name}.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Informe local: .local/verification/{name}.json", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("doctor", "verify"))
    args = parser.parse_args()
    if args.command == "verify":
        raise SystemExit(verify())
    report = diagnose()
    for row in report["checks"]:
        print(f"{'OK' if row['passed'] else 'FALTA' if row['required'] else 'AVISO'} {row['name']}: {row['detail']}")
    save_report("doctor", report)
    raise SystemExit(0 if report["ready"] else 1)


if __name__ == "__main__":
    main()
