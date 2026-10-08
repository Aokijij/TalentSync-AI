# ruff: noqa: F811
import smtplib
import ssl
from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest
from pydantic import ValidationError
from test_api_flows import client, register  # noqa: F401

from app.application.ports.services import MailDeliveryError
from app.application.use_cases.mail_delivery import deliver_outbox
from app.core.config import Settings, settings
from app.infrastructure.database.models import MailMessage
from app.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork
from app.infrastructure.security.smtp import SmtpDelivery


def queue(client, **values):
    with client.session_factory() as session:
        message = MailMessage(recipient="synthetic@example.com", subject="Prueba", body="PRIVATE TOKEN",
                              **({"delivery_state": "pending"} | values))
        session.add(message)
        session.commit()
        return message.id


def cycle(client, gateway, **options):
    with client.session_factory() as session:
        return deliver_outbox(SqlAlchemyUnitOfWork(session), gateway, **options)


def inspect_message(client, message_id):
    with client.session_factory() as session:
        message = session.get(MailMessage, message_id)
        session.expunge(message)
        return message


def test_only_pending_messages_are_delivered_and_sensitive_body_is_removed(client):
    queue(client, delivery_state="local")
    selected = queue(client)
    sent = []
    gateway = SimpleNamespace(send=lambda **values: sent.append(values))
    assert cycle(client, gateway)["sent"] == 1
    assert len(sent) == 1 and sent[0]["message_id"] == selected
    assert cycle(client, gateway)["sent"] == 0
    result = inspect_message(client, selected)
    assert result.delivery_state == "sent" and result.sent_at and result.body == ""
    assert result.lease_token == "" and result.attempts == 1


def test_expired_links_are_never_sent(client):
    message = queue(client, expires_at=datetime.utcnow() - timedelta(seconds=1))
    assert cycle(client, SimpleNamespace(send=lambda **values: pytest.fail("expired mail must not send")))["expired"] == 1
    assert inspect_message(client, message).body == ""


def test_temporary_failure_retries_after_backoff_then_sends(client):
    message = queue(client)
    now = datetime.utcnow()
    def fail(**values): raise MailDeliveryError(retryable=True, kind="temporary")
    assert cycle(client, SimpleNamespace(send=fail), now=now)["retry"] == 1
    result = inspect_message(client, message)
    assert result.body == "PRIVATE TOKEN" and result.next_attempt_at == now + timedelta(seconds=60)
    gateway = SimpleNamespace(send=lambda **values: None)
    assert cycle(client, gateway, now=now + timedelta(seconds=59))["sent"] == 0
    assert cycle(client, gateway, now=now + timedelta(seconds=60))["sent"] == 1
    assert inspect_message(client, message).attempts == 2


@pytest.mark.parametrize("retryable,attempts", [(False, 0), (True, 4), (True, 5)])
def test_permanent_or_exhausted_failures_clear_body_and_stop(client, retryable, attempts):
    selected = queue(client, attempts=attempts)
    calls = []
    def fail(**values):
        calls.append(True)
        raise MailDeliveryError(retryable=retryable, kind="permanent" if not retryable else "temporary")
    assert cycle(client, SimpleNamespace(send=fail))["failed"] == 1
    row = inspect_message(client, selected)
    assert row.delivery_state == "failed" and row.body == ""
    assert bool(calls) == (attempts < 5)
    assert cycle(client, SimpleNamespace(send=fail))["failed"] == 0


def test_two_workers_cannot_claim_same_lease_and_stale_worker_cannot_finish(client):
    selected = queue(client)
    now = datetime.utcnow()
    with client.session_factory() as first, client.session_factory() as second:
        a, b = SqlAlchemyUnitOfWork(first), SqlAlchemyUnitOfWork(second)
        assert a.accounts.claim_mail(now, "first", now + timedelta(minutes=2)).id == selected
        a.commit()
        assert b.accounts.claim_mail(now, "second", now + timedelta(minutes=2)) is None
        b.commit()
        later = now + timedelta(minutes=3)
        assert b.accounts.claim_mail(later, "second", later + timedelta(minutes=2)).id == selected
        b.commit()
        assert not a.accounts.finish_mail(selected, "first", delivery_state="sent")
        a.commit()
        assert b.accounts.finish_mail(selected, "second", delivery_state="sent", body="")
        b.commit()


def test_crashed_worker_is_reclaimed_after_lease_expiry(client):
    message = queue(client)
    now = datetime.utcnow()
    def crash(**values): raise RuntimeError("unexpected private provider error")
    with pytest.raises(RuntimeError):
        cycle(client, SimpleNamespace(send=crash), now=now)
    assert inspect_message(client, message).delivery_state == "sending"
    gateway = SimpleNamespace(send=lambda **values: None)
    assert cycle(client, gateway, now=now + timedelta(seconds=119))["sent"] == 0
    assert cycle(client, gateway, now=now + timedelta(seconds=120))["sent"] == 1


def test_smtp_registration_queues_without_sending_or_exposing_local_mailbox(client, monkeypatch):
    monkeypatch.setattr(settings, "smtp_enabled", True)
    monkeypatch.setattr(settings, "local_mail_enabled", False)
    register(client, "smtp-synthetic")
    with client.session_factory() as session:
        row = session.query(MailMessage).one()
        assert row.delivery_state == "pending" and row.expires_at and row.attempts == 0
    assert client.get("/api/v1/dev/mailbox").status_code == 404


@pytest.fixture
def smtp(monkeypatch):
    calls, messages = [], []
    class Transport:
        error = None
        refusal = {}
        def __init__(self, host, port, **kwargs):
            calls.append(("connect", kwargs))
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def ehlo(self): calls.append(("ehlo", None))
        def starttls(self, *, context):
            calls.append(("tls", context))
            if self.error: raise self.error
        def login(self, user, password): calls.append(("login", None))
        def send_message(self, message, **kwargs):
            calls.append(("send", kwargs))
            messages.append(message)
            if self.error: raise self.error
            return self.refusal
    monkeypatch.setattr(smtplib, "SMTP", Transport)
    monkeypatch.setattr(smtplib, "SMTP_SSL", Transport)
    config = SimpleNamespace(smtp_enabled=True, smtp_host="smtp.invalid", smtp_port=587, smtp_security="starttls",
                             smtp_from="test@example.com", smtp_username="synthetic", smtp_password="PRIVATE", secret_key="s" * 48)
    return SmtpDelivery(config), Transport, calls, messages


@pytest.mark.parametrize("mode", ["starttls", "ssl"])
def test_smtp_encrypts_and_validates_certificate_before_authentication(smtp, mode):
    gateway, _, calls, messages = smtp
    gateway.settings.smtp_security = mode
    for _ in range(2):
        gateway.send(recipient="synthetic@example.com", subject="Confirmación", body="Synthetic", message_id=42)
    names = [name for name, _ in calls]
    if mode == "starttls":
        assert names[:5] == ["connect", "ehlo", "tls", "ehlo", "login"]
        context = calls[2][1]
    else:
        assert "tls" not in names
        context = calls[0][1]["context"]
    assert context.check_hostname and context.verify_mode == ssl.CERT_REQUIRED
    assert messages[0]["Message-ID"] == messages[1]["Message-ID"]
    assert "PRIVATE" not in str(messages[0])


@pytest.mark.parametrize("error,retryable,kind", [
    (smtplib.SMTPNotSupportedError("PRIVATE"), False, "configuration"),
    (smtplib.SMTPAuthenticationError(535, b"PRIVATE"), False, "configuration"),
    (ssl.SSLCertVerificationError("PRIVATE"), False, "configuration"),
    (smtplib.SMTPDataError(451, b"PRIVATE"), True, "temporary"),
    (smtplib.SMTPDataError(550, b"PRIVATE"), False, "permanent"),
    (smtplib.SMTPRecipientsRefused({"synthetic@example.com": (450, b"PRIVATE")}), True, "temporary"),
    (smtplib.SMTPRecipientsRefused({"synthetic@example.com": (550, b"PRIVATE")}), False, "permanent"),
    (TimeoutError("PRIVATE"), True, "transport"),
])
def test_smtp_errors_are_classified_without_exposing_provider_text(smtp, error, retryable, kind):
    gateway, transport, _, _ = smtp
    transport.error = error
    with pytest.raises(MailDeliveryError) as result:
        gateway.send(recipient="synthetic@example.com", subject="Synthetic", body="Synthetic", message_id=1)
    assert result.value.retryable == retryable and result.value.kind == kind
    assert "PRIVATE" not in str(result.value) and result.value.__cause__ is None


def test_starttls_failure_never_authenticates_or_sends(smtp):
    gateway, transport, calls, _ = smtp
    transport.error = smtplib.SMTPNotSupportedError("TLS unavailable")
    with pytest.raises(MailDeliveryError):
        gateway.send(recipient="synthetic@example.com", subject="Synthetic", body="Synthetic", message_id=1)
    assert not any(name in {"login", "send"} for name, _ in calls)


@pytest.mark.parametrize("overrides", [
    {"smtp_host": ""}, {"smtp_host": "https://smtp.invalid"}, {"smtp_from": "invalid"},
    {"smtp_username": "user", "smtp_password": ""}, {"smtp_security": "plain"}, {"local_mail_enabled": True},
])
def test_smtp_configuration_rejects_incomplete_or_unencrypted_delivery(overrides):
    values = dict(secret_key="s" * 48, smtp_enabled=True, smtp_host="smtp.invalid", smtp_from="test@example.com",
                  smtp_username="user", smtp_password="PRIVATE") | overrides
    with pytest.raises(ValidationError) as result:
        Settings(_env_file=None, **values)
    assert "PRIVATE" not in str(result.value)
