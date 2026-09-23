from io import StringIO
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text

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
            "recommendations", "notifications", "company_followers", "alembic_version",
        }
        profile_columns = {column["name"] for column in schema.get_columns("profiles")}
        assert {"department", "photo_filename", "resume_style", "resume_color", "languages"} <= profile_columns
        assert {"languages", "application_questions"} <= {column["name"] for column in schema.get_columns("jobs")}
        company_columns = {column["name"] for column in schema.get_columns("companies")}
        assert {"website", "sector", "size", "location", "mission", "values", "benefits", "logo_filename", "cover_filename"} <= company_columns
        application_columns = {column["name"] for column in schema.get_columns("applications")}
        assert {"pipeline_stage", "resolution_reason", "screening_answers", "screening_adjustment"} <= application_columns
        with engine.connect() as connection:
            assert connection.execute(text("SELECT COUNT(*) FROM users")).scalar_one() == 0
            assert connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == "0018_screening_questions"
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
