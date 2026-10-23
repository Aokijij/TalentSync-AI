"""Svix v1 verification over exact bytes, bounded timestamp and signed identifiers."""
import base64
import hashlib
import hmac
import json
import re
import time
from datetime import datetime, timezone

EVENTS = {"email.sent": "accepted", "email.delivered": "delivered", "email.delivery_delayed": "delayed", "email.bounced": "bounced", "email.complained": "complained", "email.failed": "failed"}


def verify_event(body, headers, secret, *, now=None):
    identifier, stamp, signatures = (headers.get(key, "") for key in ("svix-id", "svix-timestamp", "svix-signature"))
    try:
        if len(body) > 65536 or not re.fullmatch(r"[A-Za-z0-9_-]{1,100}", identifier) or len(signatures) > 2000 or abs((time.time() if now is None else now) - int(stamp)) > 300:
            raise ValueError()
        key = base64.b64decode(secret.removeprefix("whsec_"), validate=True)
        if len(key) < 16:
            raise ValueError()
        signed = identifier.encode() + b"." + stamp.encode() + b"." + body
        expected = base64.b64encode(hmac.new(key, signed, hashlib.sha256).digest()).decode()
        if not any(part.startswith("v1,") and hmac.compare_digest(part[3:], expected) for part in signatures.split()):
            raise ValueError()
        payload = json.loads(body)
        event_type = payload.get("type")
        if event_type not in EVENTS:
            return None  # Authentic but not a delivery event used by this application.
        provider_id = payload["data"]["email_id"]
        if not isinstance(provider_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,100}", provider_id):
            raise ValueError()
        at = datetime.fromisoformat(payload["created_at"].replace("Z", "+00:00"))
        if at.tzinfo is None:
            raise ValueError()
        return {"id": identifier, "provider_message_id": provider_id, "event_type": event_type, "happened_at": at.astimezone(timezone.utc).replace(tzinfo=None)}
    except (ValueError, TypeError, KeyError, AttributeError):
        raise ValueError("Firma o evento de correo inválido") from None
