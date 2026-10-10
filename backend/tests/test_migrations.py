from io import StringIO
from pathlib import Path

from alembic.config import Config
from sqlalchemy import create_engine, inspect, text

from alembic import command
from app.core.config import settings


def migration_config(output_buffer=None):
    backend = Path(__file__).parents[1]
    config = Config(str(backend / "alembic.ini"), output_buffer=output_buffer)
    config.set_main_option("script_location", str(backend / "alembic"))
    return config


def test_fresh_database_migrates_without_preloaded_accounts(monkeypatch, tmp_path):
    database_url = f"sqlite:///{(tmp_path / 'installation.sqlite3').as_posix()}"
    monkeypatch.setattr(settings, "database_url", database_url)
    command.upgrade(migration_config(), "head")
    engine = create_engine(database_url)
    try:
        schema = inspect(engine)
        assert set(schema.get_table_names()) == {
            "users", "profiles", "companies", "jobs", "applications",
            "recommendations", "notifications", "company_followers", "alembic_version", "event_log",
            "user_sessions", "account_tokens", "mail_messages",
            "company_members", "company_invitations",
            "learning_plans", "assessment_attempts", "learning_resources",
            "trust_incidents", "model_audit_runs",
            "interview_rooms", "interview_participants", "interview_signals",
            "recommendation_feedback", "model_experiments", "offer_feedback",
            "social_identities", "oauth_attempts",
        }
        profile_columns = {column["name"] for column in schema.get_columns("profiles")}
        assert "authentication_authority" in {column["name"] for column in schema.get_columns("user_sessions")}
        assert {"department", "photo_filename", "resume_style", "resume_color", "languages"} <= profile_columns
        assert {
            "languages",
            "application_questions",
            "source_kind",
            "source_name",
            "external_id",
            "external_url",
            "expires_at",
            "last_seen_at",
            "required_education_level",
            "required_study_fields",
        } <= {column["name"] for column in schema.get_columns("jobs")}
        assert {"is_external", "source_name"} <= {
            column["name"] for column in schema.get_columns("companies")
        }
        company_columns = {column["name"] for column in schema.get_columns("companies")}
        assert {"website", "sector", "size", "location", "mission", "values", "benefits", "logo_filename", "cover_filename"} <= company_columns
        application_columns = {column["name"] for column in schema.get_columns("applications")}
        assert {"purpose", "link_user_id", "link_session_id"} <= {column["name"] for column in schema.get_columns("oauth_attempts")}
        assert {"pipeline_stage", "resolution_reason", "screening_answers", "screening_adjustment", "interview_evaluations"} <= application_columns
        with engine.connect() as connection:
            assert connection.execute(text("SELECT COUNT(*) FROM users")).scalar_one() == 0
            assert connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == "0039_offer_quality"
    finally:
        engine.dispose()


def test_postgresql_migration_sql_creates_enum_types_once(monkeypatch):
    monkeypatch.setattr(settings, "database_url", "postgresql+psycopg://migration:check%40only@localhost/unused")
    output = StringIO()
    command.upgrade(migration_config(output), "head", sql=True)
    sql = output.getvalue()
    assert sql.count("CREATE TYPE userrole AS ENUM") == 1
    assert sql.count("CREATE TYPE applicationstatus AS ENUM") == 1
    assert "CAST(status AS TEXT)" in sql
    assert "0017_languages" in sql
    assert "fk_oauth_link_session" in sql


def test_existing_language_requirements_are_preserved_on_upgrade(monkeypatch, tmp_path):
    database_url = f"sqlite:///{(tmp_path / 'existing.sqlite3').as_posix()}"
    monkeypatch.setattr(settings, "database_url", database_url)
    command.upgrade(migration_config(), "0016_resume_colors")
    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            connection.execute(text("INSERT INTO jobs (company_id, title, description, requirements, modality, employment_type, status, skills, created_at) VALUES (1, 'Desarrollador', 'Desarrollo de aplicaciones', 'Nivel de inglés B1 intermedio.', 'hybrid', 'full_time', 'active', '[]', CURRENT_TIMESTAMP)"))
        command.upgrade(migration_config(), "head")
        with engine.connect() as connection:
            import json
            languages = connection.execute(text("SELECT languages FROM jobs")).scalar_one()
            assert json.loads(languages) == [{"name": "inglés", "level": "B1"}]
    finally:
        engine.dispose()


def test_oauth_linking_migration_preserves_pending_logins(monkeypatch, tmp_path):
    database_url = f"sqlite:///{(tmp_path / 'oauth-upgrade.sqlite3').as_posix()}"
    monkeypatch.setattr(settings, "database_url", database_url)
    command.upgrade(migration_config(), "0031_social_identity")
    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            connection.execute(text("INSERT INTO oauth_attempts (provider,state_hash,browser_hash,verifier_cipher,expires_at) VALUES ('github','state-hash','browser-hash','encrypted-verifier','2030-01-01')"))
        command.upgrade(migration_config(), "head")
        with engine.connect() as connection:
            row = connection.execute(text("SELECT purpose,link_user_id,link_session_id,verifier_cipher FROM oauth_attempts")).one()
            assert tuple(row) == ("login", None, None, "encrypted-verifier")
        command.downgrade(migration_config(), "0031_social_identity")
        with engine.connect() as connection:
            assert connection.execute(text("SELECT state_hash FROM oauth_attempts")).scalar_one() == "state-hash"
        command.upgrade(migration_config(), "head")
        engine.dispose()  # Inspect through a fresh SQLite connection after external DDL.
        assert len(inspect(engine).get_foreign_keys("oauth_attempts")) == 2
    finally:
        engine.dispose()


def test_corporate_authority_migration_preserves_existing_sessions(monkeypatch, tmp_path):
    database_url = f"sqlite:///{(tmp_path / 'corporate-upgrade.sqlite3').as_posix()}"
    monkeypatch.setattr(settings, "database_url", database_url)
    command.upgrade(migration_config(), "0034_admin_sso")
    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            connection.execute(text("INSERT INTO users (name,email,password_hash,role,created_at) VALUES ('Staff','staff@example.com','unchanged-hash','ADMIN',CURRENT_TIMESTAMP)"))
            for token, method in [("password-token", "password"), ("workspace-token", "workspace")]:
                connection.execute(text("INSERT INTO user_sessions (user_id,token_hash,csrf_hash,user_agent,created_at,last_seen_at,expires_at,mfa_verified,authentication_method) VALUES (1,:token,:token,'test',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP,'2030-01-01',false,:method)"), {"token": token, "method": method})
        command.upgrade(migration_config(), "head")
        with engine.connect() as connection:
            rows = connection.execute(text("SELECT authentication_method,authentication_authority FROM user_sessions ORDER BY id")).all()
            assert [tuple(row) for row in rows] == [("password", ""), ("workspace", "")]
            assert connection.execute(text("SELECT password_hash FROM users")).scalar_one() == "unchanged-hash"
        command.downgrade(migration_config(), "0034_admin_sso")
        with engine.connect() as connection:
            assert connection.execute(text("SELECT COUNT(*) FROM user_sessions")).scalar_one() == 2
    finally:
        engine.dispose()


def test_mail_migration_preserves_local_messages_without_sending_them(monkeypatch, tmp_path):
    url = f"sqlite:///{(tmp_path / 'mail-upgrade.sqlite3').as_posix()}"
    monkeypatch.setattr(settings, "database_url", url)
    command.upgrade(migration_config(), "0035_corporate_authority")
    engine = create_engine(url)
    try:
        with engine.begin() as connection:
            connection.execute(text("INSERT INTO mail_messages (recipient,subject,body,created_at) VALUES ('synthetic@example.com','Local','unchanged',CURRENT_TIMESTAMP)"))
        command.upgrade(migration_config(), "head")
        with engine.connect() as connection:
            assert tuple(connection.execute(text("SELECT body,delivery_state,attempts,lease_token FROM mail_messages")).one()) == ("unchanged", "local", 0, "")
        command.downgrade(migration_config(), "0035_corporate_authority")
        with engine.connect() as connection:
            assert connection.execute(text("SELECT body FROM mail_messages")).scalar_one() == "unchanged"
        command.upgrade(migration_config(), "head")
    finally:
        engine.dispose()
