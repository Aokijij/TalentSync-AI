from datetime import datetime, timedelta

from sqlalchemy import and_, or_, update

from app.infrastructure.database.models import (
    Application,
    CalendarConnection,
    CalendarEvent,
    OAuthAttempt,
)


class CalendarRepository:
    def __init__(self, session):
        self.session = session

    def connection(self, user_id):
        return self.session.get(CalendarConnection, user_id)

    def connect(self, user_id, cipher):
        row = self.connection(user_id)
        if row is None:
            row = CalendarConnection(user_id=user_id, refresh_cipher=cipher)
            self.session.add(row)
        else:
            row.refresh_cipher, row.last_error = cipher, ""
        self.session.query(CalendarEvent).filter_by(user_id=user_id, error_code="authorization").update({CalendarEvent.state: "pending", CalendarEvent.next_attempt_at: None, CalendarEvent.attempts: 0}, synchronize_session=False)
        return row

    def disconnect(self, user_id):
        self.session.query(OAuthAttempt).filter_by(link_user_id=user_id, purpose="calendar", used_at=None).update({OAuthAttempt.used_at: datetime.utcnow(), OAuthAttempt.verifier_cipher: ""}, synchronize_session=False)
        self.session.query(CalendarEvent).filter_by(user_id=user_id).delete(synchronize_session=False)
        self.session.query(CalendarConnection).filter_by(user_id=user_id).delete(synchronize_session=False)

    def event(self, user_id, application_id):
        return self.session.query(CalendarEvent).filter_by(user_id=user_id, application_id=application_id).first()

    def new_event(self, **values):
        return CalendarEvent(**values)

    def due(self, now, limit=20):
        return self.session.query(CalendarEvent).join(CalendarConnection, CalendarConnection.user_id == CalendarEvent.user_id).join(Application, Application.id == CalendarEvent.application_id).filter(
            CalendarConnection.last_error != "authorization",
            or_(CalendarEvent.lease_until.is_(None), CalendarEvent.lease_until < now),
            or_(and_(CalendarEvent.state.in_(["synced", "cancelled"]), CalendarEvent.application_version != Application.version),
                and_(CalendarEvent.state.in_(["pending", "retry"]), or_(CalendarEvent.next_attempt_at.is_(None), CalendarEvent.next_attempt_at <= now)))
        ).order_by(CalendarEvent.next_attempt_at, CalendarEvent.id).limit(limit).all()

    def claim(self, event_id, lease, now):
        return self.session.execute(update(CalendarEvent).where(CalendarEvent.id == event_id, or_(CalendarEvent.lease_until.is_(None), CalendarEvent.lease_until < now)).values(lease_token=lease, lease_until=now + timedelta(minutes=2)).execution_options(synchronize_session=False)).rowcount == 1
