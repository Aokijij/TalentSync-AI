"""Real PostgreSQL rehearsal on an owned loopback cluster; never uses backend/.env."""
import argparse
import json
import os
import secrets
import socket
import subprocess
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

import local
from local_checks import migration_head, source_fingerprint

ROOT = local.ROOT
FOLDER = ROOT / ".local/staging"
DATA = FOLDER / "pgdata"
PORT = 55432
ADMIN = "talentsync_rehearsal_admin"
ROLE = "talentsync_rehearsal_app"


def run(command, *, env=None, cwd=None):
    # pg_ctl's daemon inherits pipe handles on Windows, preventing communicate()
    # from seeing EOF even after pg_ctl exits. A file does not wait for that EOF.
    with tempfile.TemporaryFile(mode="w+", encoding="utf-8") as output:
        result = subprocess.run(command, env=env, cwd=cwd, stdout=output, stderr=output, check=False, timeout=300,
                                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
        output.seek(0)
        content = output.read()
    if result.returncode:
        # Driver errors can include connection strings or SQL values. Do not echo them.
        raise RuntimeError(f"Falló {Path(command[0]).name}; no se muestran datos de conexión")
    return content


def pg_tools():
    folder = Path(os.environ.get("TALENTSYNC_PG_BIN", r"C:\Program Files\PostgreSQL\18\bin"))
    tools = {name: folder / (name + (".exe" if os.name == "nt" else ""))
             for name in ("initdb", "pg_ctl", "pg_dump", "pg_restore")}
    if not all(path.is_file() for path in tools.values()):
        raise RuntimeError("Instala PostgreSQL 18 o configura TALENTSYNC_PG_BIN")
    return tools


def credentials():
    FOLDER.mkdir(parents=True, exist_ok=True)
    path = FOLDER / "credentials.json"
    if path.exists():
        values = json.loads(path.read_text(encoding="utf-8"))
        if set(values) != {"admin", "app", "session"} or any(len(value) < 32 for value in values.values()):
            raise RuntimeError("Credenciales del ensayo inválidas; no se sobrescriben")
        return values
    if DATA.exists():
        raise RuntimeError("Existe un clúster sin credenciales del ensayo; no se modifica")
    values = {name: secrets.token_urlsafe(48) for name in ("admin", "app", "session")}
    with path.open("x", encoding="utf-8") as stream:
        json.dump(values, stream)
    return values


def connect(values, *, database="postgres", app=False):
    import psycopg
    return psycopg.connect(host="127.0.0.1", port=PORT, dbname=database,
                           user=ROLE if app else ADMIN, password=values["app" if app else "admin"],
                           connect_timeout=5, autocommit=True)


def assert_owned(connection):
    actual = connection.execute("SHOW data_directory").fetchone()[0]
    if Path(actual).resolve() != DATA.resolve():
        raise RuntimeError("El servidor no pertenece al ensayo; no se modifica")
    if connection.execute("SHOW listen_addresses").fetchone()[0] != "127.0.0.1":
        raise RuntimeError("El clúster debe escuchar exclusivamente en loopback")


def port_open():
    with socket.socket() as probe:
        probe.settimeout(1)
        return probe.connect_ex(("127.0.0.1", PORT)) == 0


def initialize(tools, values):
    if (DATA / "PG_VERSION").exists():
        return
    if DATA.exists():
        raise RuntimeError("Directorio PostgreSQL incompleto; no se sobrescribe")
    password_file = FOLDER / "init-password"
    password_file.write_text(values["admin"], encoding="utf-8")
    try:
        run([str(tools["initdb"]), "-D", str(DATA), "--username", ADMIN, "--pwfile", str(password_file),
             "--auth-host=scram-sha-256", "--auth-local=scram-sha-256", "--encoding=UTF8", "--locale=C"])
    finally:
        password_file.unlink(missing_ok=True)


def create_database(values, name):
    from psycopg import sql
    if not name.startswith("talentsync_rehearsal_"):
        raise RuntimeError("Nombre de base fuera del ensayo")
    with connect(values) as connection:
        assert_owned(connection)
        if not connection.execute("SELECT 1 FROM pg_roles WHERE rolname=%s", (ROLE,)).fetchone():
            connection.execute(sql.SQL("CREATE ROLE {} LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE PASSWORD {}").format(
                sql.Identifier(ROLE), sql.Literal(values["app"])))
        attributes = connection.execute("SELECT rolsuper, rolcreatedb, rolcreaterole FROM pg_roles WHERE rolname=%s", (ROLE,)).fetchone()
        if any(attributes):
            raise RuntimeError("El rol de la aplicación tiene privilegios administrativos")
        connection.execute(sql.SQL("CREATE DATABASE {} OWNER {} TEMPLATE template0 ENCODING 'UTF8'").format(
            sql.Identifier(name), sql.Identifier(ROLE)))


def application_env(values, database):
    env = local.prepare_environment(testing=True)
    # An empty, dedicated dotenv prevents fallback to the original backend/.env.
    env_file = FOLDER / "empty.env"
    env_file.touch(exist_ok=True)
    env.update({"TALENTSYNC_ENV_FILE": str(env_file), "SECRET_KEY": values["session"],
                "DATABASE_URL": f"postgresql+psycopg://{ROLE}:{values['app']}@127.0.0.1:{PORT}/{database}",
                "TALENTSYNC_REHEARSAL_DATA": str(DATA.resolve()),
                "TALENTSYNC_REHEARSAL_DATABASE": database})
    return env


def check():
    tools, values = pg_tools(), credentials()
    started = False
    report = {"passed": False, "checked_at": datetime.now(timezone.utc).isoformat(), "steps": []}
    fingerprint = source_fingerprint()
    try:
        if port_open():
            with connect(values) as connection:
                assert_owned(connection)
        else:
            initialize(tools, values)
            run([str(tools["pg_ctl"]), "-D", str(DATA), "-l", str(FOLDER / "postgres.log"),
                 "-o", f"-h 127.0.0.1 -p {PORT}", "-w", "start"])
            started = True
        with connect(values) as connection:
            assert_owned(connection)
            report["postgres_version"] = connection.execute("SHOW server_version").fetchone()[0]
        database = "talentsync_rehearsal_" + uuid.uuid4().hex
        create_database(values, database)
        env = application_env(values, database)

        def step(name, command):
            print(f"Comprobando: {name}", flush=True)
            entry = {"name": name, "passed": False}
            report["steps"].append(entry)
            run(command, env=env, cwd=ROOT / "backend")
            entry["passed"] = True

        alembic = [str(local.PYTHON), "-m", "alembic"]
        step("migrations_upgrade", [*alembic, "upgrade", "head"])
        step("cross_role_acceptance", [str(local.PYTHON), "-m", "pytest", "-q", "tests/test_postgres_acceptance.py",
                                      "--disable-warnings", "-W", "error::sqlalchemy.exc.SAWarning"])
        step("migration_downgrade", [*alembic, "downgrade", "-1"])
        step("migration_reupgrade", [*alembic, "upgrade", "head"])
        backup = FOLDER / (database + ".dump")
        pg_env = {**os.environ, "PGHOST": "127.0.0.1", "PGPORT": str(PORT), "PGUSER": ROLE,
                  "PGPASSWORD": values["app"], "PGDATABASE": database, "PGCONNECT_TIMEOUT": "5"}
        run([str(tools["pg_dump"]), "--format=custom", "--no-owner", "--no-acl", "--file", str(backup)], env=pg_env)
        restored = "talentsync_rehearsal_" + uuid.uuid4().hex
        create_database(values, restored)
        run([str(tools["pg_restore"]), "--exit-on-error", "--no-owner", "--no-acl", "--dbname", restored, str(backup)], env=pg_env)
        with connect(values, database=database, app=True) as before, connect(values, database=restored, app=True) as after:
            head = migration_head(ROOT)
            for connection in (before, after):
                assert connection.execute("SELECT version_num FROM alembic_version").fetchone() == (head,)
            # Compare every table, including sessions, portfolio and audit records.
            from psycopg import sql
            tables = before.execute("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename").fetchall()
            for (table,) in tables:
                query = sql.SQL("SELECT row_to_json(t)::text FROM {} t ORDER BY row_to_json(t)::text").format(sql.Identifier(table))
                assert before.execute(query).fetchall() == after.execute(query).fetchall(), "Restore mismatch"
            report["restored_tables"] = len(tables)
        report["steps"].append({"name": "backup_restore_all_rows", "passed": True})
        if fingerprint != source_fingerprint():
            raise RuntimeError("El código cambió durante la verificación; repite el ensayo")
        report.update({"passed": True, "source_fingerprint": fingerprint, "migration_head": head})
    finally:
        try:
            if started:
                with connect(values) as connection:
                    assert_owned(connection)
                run([str(tools["pg_ctl"]), "-D", str(DATA), "-w", "stop", "-m", "fast"])
        except Exception:
            report["passed"] = False
            raise
        finally:
            FOLDER.mkdir(parents=True, exist_ok=True)
            (FOLDER / "verification.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("PostgreSQL: migraciones, aceptación y restauración verificadas. Informe sin credenciales en .local/staging/verification.json")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ensayo aislado de PostgreSQL; no despliega")
    parser.add_argument("command", choices=["check"])
    parser.parse_args()
    try:
        check()
    except Exception as exc:  # noqa: BLE001 -- do not disclose driver connection strings or SQL values
        print(f"El ensayo no pasó ({type(exc).__name__}). Revisa la etapa indicada; se omiten datos de conexión y SQL.", file=sys.stderr)
        raise SystemExit(1) from None
