"""Resend transport for the existing leased outbox. Never logs provider bodies."""
import hashlib
import hmac
import re

import httpx

from app.application.ports.services import MailDeliveryError
from app.infrastructure.security.email_template import render_email


class ResendDelivery:
    def __init__(self, settings, transport=None):
        self.settings = settings
        self.transport = transport

    def send(self, *, recipient, subject, body, message_id):
        if not self.settings.resend_enabled:
            raise MailDeliveryError(retryable=False, kind="configuration")
        # Stable across retries/workers, private and distinct between installations.
        key = hmac.new(self.settings.secret_key.encode(), f"resend-mail:{message_id}".encode(), hashlib.sha256).hexdigest()
        try:
            with httpx.Client(transport=self.transport, timeout=15, follow_redirects=False, trust_env=False) as client:
                with client.stream("POST", "https://api.resend.com/emails", headers={
                    "Authorization": f"Bearer {self.settings.resend_api_key}", "Idempotency-Key": key,
                }, json={"from": f"TalentSync <{self.settings.resend_from}>", "to": [recipient], "subject": subject, "text": body,
                         "html": render_email(subject, body, public_app_url=getattr(self.settings, "public_app_url", ""))}) as response:
                    status = response.status_code
                    if 200 <= status < 300:
                        raw = bytearray()
                        for chunk in response.iter_bytes():
                            raw.extend(chunk)
                            if len(raw) > 4096:
                                raise MailDeliveryError(retryable=False, kind="permanent")
                        import json
                        try:
                            identifier = json.loads(raw).get("id")
                        except (ValueError, AttributeError):
                            identifier = None
                        # Older transports/stubs may not return an id. Never invent one.
                        return identifier if isinstance(identifier, str) and re.fullmatch(r"[A-Za-z0-9_-]{1,100}", identifier) else None
                    # Retry only temporary errors. Do not expose response text or secrets.
                    raise MailDeliveryError(retryable=status == 429 or status >= 500,
                                            kind="configuration" if status in {401, 403} else "temporary" if status == 429 or status >= 500 else "permanent")
        except httpx.HTTPError:
            raise MailDeliveryError(retryable=True, kind="transport") from None
