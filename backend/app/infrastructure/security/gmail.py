"""Send-only Gmail OAuth transport. Never reads messages or falls back to a password."""
import base64
import hashlib
import json
import time
from email.message import EmailMessage
from email.utils import formataddr, formatdate

import httpx

from app.application.ports.services import MailDeliveryError
from app.infrastructure.security.email_template import render_email

SEND_SCOPE = "https://www.googleapis.com/auth/gmail.send"


def _private(value):
    return value.get_secret_value() if hasattr(value, "get_secret_value") else value


def _json(response, *, limit=16384):
    body = bytearray()
    for chunk in response.iter_bytes():
        body.extend(chunk)
        if len(body) > limit:
            raise MailDeliveryError(retryable=False, kind="permanent")
    try:
        value = json.loads(body)
    except (ValueError, UnicodeError):
        raise MailDeliveryError(retryable=False, kind="permanent") from None
    if not isinstance(value, dict):
        raise MailDeliveryError(retryable=False, kind="permanent")
    return value


class GmailDelivery:
    def __init__(self, settings, transport=None):
        self.settings = settings
        self.transport = transport
        self._token = ""
        self._expires = 0

    def _access(self, client):
        if self._token and time.monotonic() < self._expires:
            return self._token
        with client.stream("POST", "https://oauth2.googleapis.com/token", data={
            "grant_type": "refresh_token", "client_id": self.settings.gmail_mail_client_id,
            "client_secret": _private(self.settings.gmail_mail_client_secret),
            "refresh_token": _private(self.settings.gmail_mail_refresh_token),
        }) as response:
            if response.status_code != 200:
                raise MailDeliveryError(retryable=response.status_code == 429 or response.status_code >= 500,
                                        kind="temporary" if response.status_code == 429 or response.status_code >= 500 else "configuration")
            payload = _json(response)
        token, lifetime = payload.get("access_token"), payload.get("expires_in")
        if (not isinstance(token, str) or not token or len(token) > 8192
                or not isinstance(lifetime, (int, float)) or lifetime <= 0
                or payload.get("token_type", "Bearer").casefold() != "bearer"):
            raise MailDeliveryError(retryable=False, kind="configuration")
        if "scope" in payload and SEND_SCOPE not in payload["scope"].split():
            raise MailDeliveryError(retryable=False, kind="configuration")
        self._token = token
        self._expires = time.monotonic() + max(0, min(lifetime, 3600) - 60)
        return token

    def send(self, *, recipient, subject, body, message_id):
        config = self.settings
        if not config.gmail_mail_enabled:
            raise MailDeliveryError(retryable=False, kind="configuration")
        try:
            message = EmailMessage()
            message["From"] = formataddr(("TalentSync", config.gmail_mail_sender))
            message["To"], message["Subject"] = recipient, subject
            message["Date"] = formatdate(localtime=False)
            namespace = hashlib.sha256(("mail:" + config.secret_key).encode()).hexdigest()[:16]
            message["Message-ID"] = f"<talentsync-{namespace}-{message_id}@{config.gmail_mail_sender.rsplit('@', 1)[1]}>"
            message.set_content(body)
            message.add_alternative(render_email(subject, body, public_app_url=config.public_app_url), subtype="html")
            encoded = base64.urlsafe_b64encode(message.as_bytes()).decode("ascii")
            with httpx.Client(transport=self.transport, timeout=15, follow_redirects=False, trust_env=False) as client:
                token = self._access(client)
                # A send timeout is ambiguous: do not retry automatically and risk duplicate mail.
                try:
                    with client.stream("POST", "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
                                       headers={"Authorization": f"Bearer {token}"}, json={"raw": encoded}) as response:
                        if response.status_code == 200:
                            identifier = _json(response).get("id")
                            if isinstance(identifier, str) and identifier and len(identifier) <= 100:
                                return identifier
                            raise MailDeliveryError(retryable=False, kind="permanent")
                        if response.status_code == 401:
                            self._token = ""
                        raise MailDeliveryError(retryable=response.status_code == 429,
                                                kind="temporary" if response.status_code == 429 else "configuration" if response.status_code in {401, 403} else "permanent")
                except httpx.HTTPError:
                    raise MailDeliveryError(retryable=False, kind="transport") from None
        except httpx.HTTPError:
            # Refresh-token network errors are safe to retry: no message was submitted.
            raise MailDeliveryError(retryable=True, kind="transport") from None
        except (ValueError, TypeError, AttributeError, IndexError):
            raise MailDeliveryError(retryable=False, kind="configuration") from None
