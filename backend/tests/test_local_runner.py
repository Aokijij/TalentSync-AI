import runpy
from pathlib import Path


def test_test_runner_ignores_active_models_integrations_and_demo_database(tmp_path, monkeypatch):
    module = runpy.run_path(str(Path(__file__).resolve().parents[2] / "scripts/local.py"))
    prepare = module["prepare_environment"]
    local = tmp_path / ".local"
    local.mkdir()
    env_file = local / "backend.env"
    source = (
        f"ENVIRONMENT=development\nDATABASE_URL=sqlite:///{(local / 'talentsync.sqlite3').as_posix()}\n"
        'MATCH_MODEL_PATH=C:/configured-model\nADMIN_SSO_REQUIRED=true\nWORKSPACE_DOMAIN=example.com\n'
        'GITHUB_PROJECT_ANALYSIS_ENABLED=true\nOAUTH_GOOGLE_CLIENT_ID=local-config\n'
        'WEBRTC_TURN_URLS=["turn:localhost:3478"]\nWEBRTC_TURN_SECRET=local-secret\n'
        'WEBRTC_RELAY_ONLY=true\n'
    )
    env_file.write_text(source, encoding="utf-8")
    prepare.__globals__.update(ROOT=tmp_path, LOCAL=local, ENV_FILE=env_file)
    monkeypatch.setenv("MATCH_MODEL_PATH", "C:/inherited-model")
    testing = prepare(testing=True)
    assert testing["DATABASE_URL"] == "sqlite://"
    assert testing["MATCH_MODEL_PATH"] == ""
    assert testing["OAUTH_GOOGLE_CLIENT_ID"] == ""
    assert testing["WORKSPACE_DOMAIN"] == ""
    assert testing["WEBRTC_TURN_SECRET"] == ""
    assert testing["WEBRTC_TURN_URLS"] == "[]"
    for name in ["SESSION_AUTH_ENABLED", "LOCAL_MAIL_ENABLED", "ADMIN_SSO_REQUIRED", "WEBRTC_RELAY_ONLY",
                 "GITHUB_PROJECT_ANALYSIS_ENABLED", "WORKFLOW_MAINTENANCE_ENABLED", "MODEL_MAINTENANCE_ENABLED"]:
        assert testing[name] == "false"
    assert env_file.read_text(encoding="utf-8") == source
    development = prepare()
    assert development["MATCH_MODEL_PATH"] == "C:/configured-model"
    assert development["OAUTH_GOOGLE_CLIENT_ID"] == "local-config"
    assert development["DATABASE_URL"].endswith("talentsync.sqlite3")
