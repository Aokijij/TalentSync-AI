from datetime import datetime, timedelta


def record(db, event, retention_days):
    db.accounts.record_mail_event(event)
    db.accounts.trim_delivery_events(datetime.utcnow() - timedelta(days=retention_days))
    db.commit()
