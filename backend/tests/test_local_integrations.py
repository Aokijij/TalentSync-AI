"""Private configuration must opt in explicitly and stay isolated from tests."""
import json

import pytest
from test_local_environment import local_commands


def write_config(tmp_path, content):
    target = tmp_path / "integrations.env"
    target.write_text(content, encoding="utf-8-sig")
    return target


def test_private_social_configuration_and_sanitized_callbacks(monkeypatch, tmp_path):
    commands = local_commands(monkeypatch, tmp_path)
    write_config(tmp_path, "INTEGRATIONS_ENABLED=true\nOAUTH_GOOGLE_CLIENT_ID=private-id\nOAUTH_GOOGLE_CLIENT_SECRET=private-secret\nOAUTH_LINKEDIN_CLIENT_ID=linkedin-id\nOAUTH_LINKEDIN_CLIENT_SECRET=private-linkedin\n")
    env = commands.prepare_environment()
    assert env["OAUTH_GOOGLE_CLIENT_SECRET"] == "private-secret"
    report = commands.integration_status(env)
    assert report["providers"]["google"]["state"] == "configured"
    assert report["providers"]["linkedin"]["state"] == "requires_https"
    assert report["providers"]["github"]["state"] == "missing_credentials"
    assert report["providers"]["google"]["callback"] == "http://127.0.0.1:5173/api/v1/auth/social/google/callback"
    assert "private" not in json.dumps(report)
    assert commands.prepare_environment(testing=True)["OAUTH_GOOGLE_CLIENT_SECRET"] == ""


def test_explicit_resend_only_future_outbox_and_webhook_configuration(monkeypatch, tmp_path):
    commands = local_commands(monkeypatch, tmp_path)
    write_config(tmp_path, "INTEGRATIONS_ENABLED=true\nINTEGRATION_MAIL_TRANSPORT=resend\nRESEND_API_KEY=re_private\nRESEND_FROM=accounts@example.com\nRESEND_WEBHOOK_SECRET=whsec_private\n")
    env = commands.prepare_environment()
    assert env["RESEND_ENABLED"] == "true"
    assert env["LOCAL_MAIL_ENABLED"] == env["SMTP_ENABLED"] == "false"
    assert env["RESEND_WEBHOOK_SECRET"] == "whsec_private"
    report = commands.integration_status(env)
    assert report["mail"] == "resend" and report["delivery_webhook"]["configured"]
    testing = commands.prepare_environment(testing=True)
    assert testing["RESEND_ENABLED"] == "false" and testing["RESEND_API_KEY"] == ""
    assert testing["RESEND_WEBHOOK_SECRET"] == ""


def test_gmail_requires_explicit_opt_in_and_never_leaks_into_tests(monkeypatch, tmp_path):
    commands = local_commands(monkeypatch, tmp_path)
    write_config(tmp_path, "INTEGRATIONS_ENABLED=true\nINTEGRATION_MAIL_TRANSPORT=gmail\nGMAIL_MAIL_CLIENT_ID=synthetic.apps.googleusercontent.com\nGMAIL_MAIL_CLIENT_SECRET=PRIVATE-CLIENT\nGMAIL_MAIL_REFRESH_TOKEN=PRIVATE-REFRESH\nGMAIL_MAIL_SENDER=sender@example.com\n")
    env = commands.prepare_environment()
    assert env["GMAIL_MAIL_ENABLED"] == "true"
    assert env["LOCAL_MAIL_ENABLED"] == env["SMTP_ENABLED"] == env["RESEND_ENABLED"] == "false"
    assert commands.integration_status(env)["mail"] == "gmail"
    assert "PRIVATE" not in json.dumps(commands.integration_status(env))
    testing = commands.prepare_environment(testing=True)
    assert testing["GMAIL_MAIL_ENABLED"] == "false" and testing["GMAIL_MAIL_REFRESH_TOKEN"] == ""
    assert testing["GMAIL_MAIL_CLIENT_SECRET"] == ""


def test_https_origin_and_calendar_opt_in(monkeypatch, tmp_path):
    commands = local_commands(monkeypatch, tmp_path)
    write_config(tmp_path, "INTEGRATIONS_ENABLED=true\nPUBLIC_APP_URL=https://localhost:5173\nCALENDAR_SYNC_ENABLED=true\nCALENDAR_GOOGLE_CLIENT_ID=calendar-id\nCALENDAR_GOOGLE_CLIENT_SECRET=calendar-secret\nINTEGRATION_MAIL_TRANSPORT=smtp\nSMTP_HOST=smtp.example.com\nSMTP_FROM=accounts@example.com\n")
    env = commands.prepare_environment()
    assert env["SESSION_COOKIE_SECURE"] == "true"
    assert json.loads(env["CORS_ORIGINS"]) == ["https://localhost:5173"]
    assert env["SMTP_ENABLED"] == "true" and env["LOCAL_MAIL_ENABLED"] == "false"
    assert commands.integration_status(env)["calendar"]["state"] == "configured"
    assert commands.prepare_environment(testing=True)["PUBLIC_APP_URL"] == "http://127.0.0.1:5173"


@pytest.mark.parametrize("content", [
    "INTEGRATIONS_ENABLED=true\nDATABASE_URL=sqlite:///other",
    "INTEGRATIONS_ENABLED=true\nRESEND_API_KEY=private\nRESEND_API_KEY=duplicate",
    "INTEGRATIONS_ENABLED=true\nINTEGRATION_MAIL_TRANSPORT=invalid",
    "INTEGRATIONS_ENABLED=true\nPUBLIC_APP_URL=https://external.example.com",
    "INTEGRATIONS_ENABLED=true\nPUBLIC_APP_URL=http://localhost:bad",
    "INTEGRATIONS_ENABLED=true\nPUBLIC_APP_URL=https://user:password@localhost",
    "INTEGRATIONS_ENABLED=true\nINTEGRATION_MAIL_TRANSPORT=resend\nRESEND_API_KEY=re_private\nRESEND_FROM=onboarding@resend.dev",
    "INTEGRATIONS_ENABLED=true\nINTEGRATION_MAIL_TRANSPORT=smtp",
    "INTEGRATIONS_ENABLED=true\nINTEGRATION_MAIL_TRANSPORT=gmail",
])
def test_invalid_private_configuration_never_leaks_secrets(monkeypatch, tmp_path, content):
    commands = local_commands(monkeypatch, tmp_path)
    write_config(tmp_path, content)
    with pytest.raises(SystemExit) as failure:
        commands.prepare_environment()
    assert "re_private" not in str(failure.value) and "user:password" not in str(failure.value)
    # Broken real integration settings must not interfere with isolated test runs.
    assert commands.prepare_environment(testing=True)["DATABASE_URL"] == "sqlite://"


def test_no_opt_in_never_uses_credentials_or_inherited_mail(monkeypatch, tmp_path):
    commands = local_commands(monkeypatch, tmp_path)
    write_config(tmp_path, "INTEGRATIONS_ENABLED=false\nINTEGRATION_MAIL_TRANSPORT=resend\nRESEND_API_KEY=re_private\nOAUTH_GOOGLE_CLIENT_ID=ignored\n")
    monkeypatch.setenv("RESEND_ENABLED", "true")
    monkeypatch.setenv("RESEND_API_KEY", "inherited-private")
    env = commands.prepare_environment()
    assert env["RESEND_ENABLED"] == "false" and env["RESEND_API_KEY"] == ""
    assert env["OAUTH_GOOGLE_CLIENT_ID"] == ""
