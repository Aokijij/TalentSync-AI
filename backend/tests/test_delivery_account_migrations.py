"""Exercise migration history with existing records, not create_all."""
import os
import sqlite3
import subprocess
import sys
from pathlib import Path


def test_new_delivery_calendar_and_erasure_migrations_preserve_existing_data(tmp_path):
    database = tmp_path / "migration.sqlite3"
    root = Path(__file__).resolve().parents[1]
    env = {**os.environ, "DATABASE_URL": "sqlite:///" + database.as_posix(), "ACCOUNT_CLEANUP_ENABLED": "false", "ACCOUNT_RETENTION_ENABLED": "false", "CALENDAR_SYNC_ENABLED": "false"}

    def migrate(target):
        result = subprocess.run([sys.executable, "-m", "alembic", *target], cwd=root, env=env, capture_output=True, timeout=60)
        assert result.returncode == 0, "Isolated synthetic migration failed"

    migrate(["upgrade", "0043_resume_versions"])
    with sqlite3.connect(database) as db:
        db.execute("INSERT INTO users(id,name,email,password_hash,role,created_at) VALUES (10,'Synthetic','synthetic@example.test','unused','CANDIDATE','2026-10-23')")
        db.commit()
    migrate(["upgrade", "head"])
    with sqlite3.connect(database) as db:
        assert db.execute("SELECT name FROM users WHERE id=10").fetchone() == ("Synthetic",)
        assert db.execute("SELECT registration_pending FROM users WHERE id=10").fetchone() == (0,)
        assert db.execute("SELECT legal_acceptance FROM users WHERE id=10").fetchone() == ("{}",)
        assert "AUTOINCREMENT" in db.execute("SELECT sql FROM sqlite_master WHERE name='users'").fetchone()[0]
        names = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        assert {"calendar_connections", "calendar_events", "mail_delivery_events", "file_erasure_tasks"} <= names
        assert {"provider_message_id", "transport_status", "provider_event_at"} <= {row[1] for row in db.execute("PRAGMA table_info(mail_messages)")}
        db.execute("DELETE FROM users WHERE id=10")
        db.execute("INSERT INTO users(name,email,password_hash,role,created_at) VALUES ('New synthetic','new@example.test','unused','CANDIDATE','2026-10-23')")
        assert db.execute("SELECT id FROM users").fetchone()[0] > 10
        db.commit()
    migrate(["downgrade", "0043_resume_versions"])
    migrate(["upgrade", "head"])
    with sqlite3.connect(database) as db:
        assert db.execute("SELECT name FROM users").fetchone() == ("New synthetic",)
