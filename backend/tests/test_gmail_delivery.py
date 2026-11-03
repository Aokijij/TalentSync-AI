import base64
import json
from email import policy
from email.parser import BytesParser
from types import SimpleNamespace

import httpx
import pytest
from pydantic import SecretStr, ValidationError

from app.application.ports.services import MailDeliveryError
from app.core.config import Settings
from app.infrastructure.security.gmail import SEND_SCOPE, GmailDelivery


def configuration(**changes):
    return SimpleNamespace(gmail_mail_enabled=True, gmail_mail_client_id="synthetic.apps.googleusercontent.com",
                           gmail_mail_client_secret=SecretStr("PRIVATE-CLIENT"),
                           gmail_mail_refresh_token=SecretStr("PRIVATE-REFRESH"), gmail_mail_sender="sender@example.com",
                           secret_key="synthetic-key", public_app_url="https://app.example.com", **changes)


def deliver(gateway):
    return gateway.send(recipient="recipient@example.com", subject="Confirmación", body="Confirma tu correo:\n\nhttps://app.example.com/cuenta/confirmar?purpose=verify&token=synthetic", message_id=123)


def test_gmail_uses_refresh_token_and_sends_branded_multipart_without_reading_mail():
    calls = []
    def handler(request):
        calls.append(request)
        if request.url.host == "oauth2.googleapis.com":
            assert b"refresh_token=PRIVATE-REFRESH" in request.content
            return httpx.Response(200, json={"access_token": "PRIVATE-ACCESS", "expires_in": 3600, "scope": SEND_SCOPE})
        assert request.url == "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"
        assert request.headers["Authorization"] == "Bearer PRIVATE-ACCESS"
        raw = base64.urlsafe_b64decode(json.loads(request.content)["raw"])
        message = BytesParser(policy=policy.default).parsebytes(raw)
        assert message["From"] == "TalentSync <sender@example.com>"
        assert message["To"] == "recipient@example.com"
        assert message["Subject"] == "Confirmación"
        assert "Confirma tu correo" in message.get_body(preferencelist=("plain",)).get_content()
        assert "Confirmar mi correo" in message.get_body(preferencelist=("html",)).get_content()
        assert b"PRIVATE" not in raw
        return httpx.Response(200, json={"id": "synthetic-message"})
    gateway = GmailDelivery(configuration(), httpx.MockTransport(handler))
    assert deliver(gateway) == "synthetic-message"
    assert deliver(gateway) == "synthetic-message"
    assert len(calls) == 3  # One refresh for two sends; no profile, inbox or read scope.


@pytest.mark.parametrize("stage,status,retry,kind", [
    ("refresh", 400, False, "configuration"), ("refresh", 401, False, "configuration"),
    ("refresh", 503, True, "temporary"), ("send", 401, False, "configuration"),
    ("send", 403, False, "configuration"), ("send", 429, True, "temporary"),
    ("send", 503, False, "permanent"),
])
def test_gmail_classifies_errors_without_provider_details(stage, status, retry, kind):
    def handler(request):
        if stage == "refresh" or request.url.host != "oauth2.googleapis.com":
            return httpx.Response(status, json={"error": "PRIVATE-PROVIDER-DETAILS"})
        return httpx.Response(200, json={"access_token": "PRIVATE-ACCESS", "expires_in": 3600})
    with pytest.raises(MailDeliveryError) as failure:
        deliver(GmailDelivery(configuration(), httpx.MockTransport(handler)))
    assert (failure.value.retryable, failure.value.kind) == (retry, kind)
    assert "PRIVATE" not in str(failure.value)


@pytest.mark.parametrize("stage,retry", [("refresh", True), ("send", False)])
def test_send_timeout_is_not_automatically_retried(stage, retry):
    def handler(request):
        if stage == "refresh" or request.url.host != "oauth2.googleapis.com":
            raise httpx.ReadTimeout("PRIVATE-TOKEN")
        return httpx.Response(200, json={"access_token": "PRIVATE-ACCESS", "expires_in": 3600})
    with pytest.raises(MailDeliveryError) as failure:
        deliver(GmailDelivery(configuration(), httpx.MockTransport(handler)))
    assert failure.value.retryable is retry
    assert failure.value.kind == "transport"


@pytest.mark.parametrize("payload", [{}, {"access_token": "token", "expires_in": 3600, "scope": "openid"},
                                     {"access_token": "token", "expires_in": -1}, {"access_token": "token", "expires_in": 3600, "token_type": "basic"}])
def test_invalid_or_insufficient_tokens_never_send(payload):
    calls = []
    def handler(request):
        calls.append(request.url.host)
        return httpx.Response(200, json=payload)
    with pytest.raises(MailDeliveryError):
        deliver(GmailDelivery(configuration(), httpx.MockTransport(handler)))
    assert calls == ["oauth2.googleapis.com"]


@pytest.mark.parametrize("changes", [{"gmail_mail_client_id": ""}, {"gmail_mail_client_secret": ""},
                                      {"gmail_mail_refresh_token": ""}, {"gmail_mail_sender": "invalid"},
                                      {"smtp_enabled": True}, {"local_mail_enabled": True}, {"resend_enabled": True}])
def test_gmail_requires_complete_configuration_and_exclusive_transport(changes):
    values = dict(secret_key="s" * 48, gmail_mail_enabled=True, gmail_mail_client_id="synthetic.apps.googleusercontent.com",
                  gmail_mail_client_secret="PRIVATE-CLIENT", gmail_mail_refresh_token="PRIVATE-REFRESH", gmail_mail_sender="sender@example.com")
    with pytest.raises(ValidationError) as failure:
        Settings(_env_file=None, **(values | changes))
    assert "PRIVATE" not in str(failure.value)


def test_gmail_secrets_are_masked_and_new_actions_use_the_outbox():
    settings = Settings(_env_file=None, secret_key="s" * 48, gmail_mail_enabled=True,
                        gmail_mail_client_id="synthetic.apps.googleusercontent.com", gmail_mail_client_secret="PRIVATE-CLIENT",
                        gmail_mail_refresh_token="PRIVATE-REFRESH", gmail_mail_sender="sender@example.com")
    assert settings.mail_delivery_enabled and settings.mail_delivery_mode == "pending"
    assert "PRIVATE-REFRESH" not in repr(settings)
    assert "PRIVATE-CLIENT" not in repr(settings)
