import secrets
from datetime import datetime, timedelta

from app.application.ports.services import MailDeliveryError
from app.application.use_cases.integration_observations import record


def deliver_outbox(db, gateway, *, now=None, limit=20):
    counts = {"sent": 0, "retry": 0, "failed": 0, "expired": 0}
    for _ in range(min(max(limit, 0), 50)):
        current = now or datetime.utcnow()
        lease = secrets.token_urlsafe(32)
        message = db.accounts.claim_mail(current, lease, current + timedelta(minutes=2))
        db.commit()  # Commit the claim before network I/O; never keep DB locks while sending.
        if message is None:
            break
        message_id, attempts = message.id, message.attempts
        if message.expires_at and message.expires_at <= current:
            state, values = "expired", {"body": "", "failure_kind": ""}
        elif attempts > 5:
            state, values = "failed", {"body": "", "failure_kind": "temporary"}
        else:
            try:
                receipt = gateway.send(recipient=message.recipient, subject=message.subject, body=message.body, message_id=message_id)
                state, values = "sent", {"sent_at": now or datetime.utcnow(), "body": "", "failure_kind": "", "provider_message_id": receipt if isinstance(receipt, str) else None, "transport_status": "accepted"}
            except MailDeliveryError as error:
                state = "retry" if error.retryable and attempts < 5 else "failed"
                values = {"failure_kind": error.kind}
                if state == "retry":
                    values["next_attempt_at"] = current + timedelta(seconds=min(60 * 2 ** (attempts - 1), 900))
                else:
                    values["body"] = ""
        if db.accounts.finish_mail(message_id, lease, delivery_state="pending" if state == "retry" else state, **values):
            counts[state] += 1
            if state in {"sent", "retry", "failed"}:
                record(db, "mail", "" if state == "sent" else "provider_error", commit=False, operation="mail_accepted")
            if values.get("provider_message_id"):
                db.accounts.reconcile_mail_events(values["provider_message_id"])
        db.commit()
    return counts
