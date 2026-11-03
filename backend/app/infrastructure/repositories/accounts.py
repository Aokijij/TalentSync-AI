from datetime import datetime

from sqlalchemy import and_, func, or_, update
from sqlalchemy.exc import IntegrityError

from app.domain.services.mail_webhooks import EVENTS
from app.infrastructure.database.models import (
    AccountToken,
    MailDeliveryEvent,
    MailMessage,
    OAuthAttempt,
    SocialIdentity,
    User,
    UserSession,
)


class AccountRepository:
    def __init__(self, session):
        self.session = session

    def integration_history(self):
        from app.infrastructure.database.models import CalendarConnection, CalendarEvent
        result = {}
        def add(key, date, operation):
            if date:
                stamp = date.isoformat() + "Z"
                result[key] = {"last_success_at": stamp, "last_attempt_at": stamp, "last_error": "", "operation": operation}
        add("mail", self.session.query(func.max(MailMessage.sent_at)).filter(MailMessage.transport_status == "accepted").scalar(), "mail_accepted")
        for provider in ("google", "github", "workspace", "entra"):
            date = self.session.query(func.max(UserSession.created_at)).filter(UserSession.authentication_method == provider).scalar()
            identity_date = self.session.query(func.max(SocialIdentity.created_at)).filter(SocialIdentity.provider == provider).scalar()
            add(("sso_" if provider in {"workspace", "entra"} else "social_") + provider, max(filter(None, (date, identity_date)), default=None), "identity_exchange")
        connected = self.session.query(func.max(CalendarConnection.connected_at)).scalar()
        synced = self.session.query(func.max(CalendarEvent.last_synced_at)).scalar()
        add("calendar", max(filter(None, (connected, synced)), default=None), "calendar_sync" if synced and (not connected or synced >= connected) else "calendar_connect")
        return result

    def new_session(self, **values):
        return UserSession(**values)

    def new_identity(self, **values):
        return SocialIdentity(**values)

    def identity(self, provider, subject):
        return self.session.query(SocialIdentity).filter_by(provider=provider, subject=subject).first()

    def identities_for_user(self, user_id):
        return self.session.query(SocialIdentity).filter_by(user_id=user_id).order_by(SocialIdentity.provider).all()

    def cancel_social_access(self, user_id):
        self.session.query(OAuthAttempt).filter_by(link_user_id=user_id, used_at=None).update(
            {OAuthAttempt.used_at: datetime.utcnow(), OAuthAttempt.verifier_cipher: ""}, synchronize_session="fetch")
        self.session.query(AccountToken).filter_by(user_id=user_id, purpose="social_mfa", used_at=None).update(
            {AccountToken.used_at: datetime.utcnow()}, synchronize_session="fetch")

    def new_oauth_attempt(self, **values):
        return OAuthAttempt(**values)

    def oauth_attempt(self, state_hash):
        return self.session.query(OAuthAttempt).filter_by(state_hash=state_hash).first()

    def claim_oauth_attempt(self, attempt_id):
        result = self.session.execute(update(OAuthAttempt).where(
            OAuthAttempt.id == attempt_id, OAuthAttempt.used_at.is_(None),
            OAuthAttempt.expires_at > datetime.utcnow(),
        ).values(used_at=datetime.utcnow(), verifier_cipher="").execution_options(synchronize_session=False))
        return result.rowcount == 1

    def purge_oauth_attempts(self):
        self.session.query(OAuthAttempt).filter(OAuthAttempt.expires_at <= datetime.utcnow()).delete(synchronize_session=False)

    def new_token(self, **values):
        return AccountToken(**values)

    def new_message(self, **values):
        return MailMessage(**values)

    def session_by_hash(self, digest):
        return self.session.query(UserSession).filter_by(token_hash=digest).populate_existing().first()

    def token_by_hash(self, digest, purpose):
        return self.session.query(AccountToken).filter_by(token_hash=digest, purpose=purpose).first()

    def sessions_for_user(self, user_id):
        return self.session.query(UserSession).filter_by(user_id=user_id).order_by(UserSession.created_at.desc()).limit(100).all()

    def claim_token(self, token_id):
        result = self.session.execute(update(AccountToken).where(
            AccountToken.id == token_id, AccountToken.used_at.is_(None),
            AccountToken.expires_at > datetime.utcnow(),
        ).values(used_at=datetime.utcnow()).execution_options(synchronize_session=False))
        return result.rowcount == 1

    def revoke_sessions(self, user_id, except_id=None):
        query = self.session.query(UserSession).filter_by(user_id=user_id, revoked_at=None)
        if except_id is not None:
            query = query.filter(UserSession.id != except_id)
        query.update({UserSession.revoked_at: datetime.utcnow()}, synchronize_session="fetch")

    def claim_mfa(self, user_id, previous, counter, recovery_codes=None):
        values = {"mfa_last_counter": counter}
        if recovery_codes is not None:
            values["recovery_codes"] = recovery_codes
        result = self.session.execute(update(User).where(
            User.id == user_id,
            User.mfa_last_counter.is_(None) if previous is None else User.mfa_last_counter == previous,
        ).values(**values).execution_options(synchronize_session=False))
        return result.rowcount == 1

    def messages(self, limit=50):
        return self.session.query(MailMessage).order_by(MailMessage.created_at.desc(), MailMessage.id.desc()).limit(min(limit, 100)).all()

    def claim_mail(self, now, lease, until):
        eligible = or_(
            and_(MailMessage.delivery_state == "pending", or_(MailMessage.next_attempt_at.is_(None), MailMessage.next_attempt_at <= now)),
            and_(MailMessage.delivery_state == "sending", MailMessage.lease_until <= now),
        )
        ids = self.session.query(MailMessage.id).filter(eligible).order_by(MailMessage.id).limit(20).all()
        for (message_id,) in ids:
            claimed = self.session.execute(update(MailMessage).where(MailMessage.id == message_id, eligible).values(
                delivery_state="sending", lease_token=lease, lease_until=until,
                attempts=MailMessage.attempts + 1).execution_options(synchronize_session=False))
            if claimed.rowcount == 1:
                return self.session.query(MailMessage).filter_by(id=message_id).populate_existing().one()
        return None

    def finish_mail(self, message_id, lease, **values):
        result = self.session.execute(update(MailMessage).where(
            MailMessage.id == message_id, MailMessage.delivery_state == "sending", MailMessage.lease_token == lease,
        ).values(**values, lease_token="", lease_until=None).execution_options(synchronize_session=False))
        return result.rowcount == 1

    def record_mail_event(self, values):
        if self.session.get(MailDeliveryEvent, values["id"]):
            return False
        try:
            with self.session.begin_nested():
                self.session.add(MailDeliveryEvent(**values))
                self.session.flush()
        except IntegrityError:
            return False
        self.reconcile_mail_events(values["provider_message_id"])
        return True

    def reconcile_mail_events(self, provider_message_id):
        message = self.session.query(MailMessage).filter_by(provider_message_id=provider_message_id).populate_existing().first()
        if message is None:
            return
        events = self.session.query(MailDeliveryEvent).filter_by(provider_message_id=provider_message_id).order_by(MailDeliveryEvent.happened_at, MailDeliveryEvent.id).all()
        priority = {None: 0, "accepted": 1, "delayed": 1, "delivered": 2, "failed": 3, "bounced": 4, "complained": 5}
        for event in events:
            state = EVENTS[event.event_type]
            if priority[state] < priority.get(message.transport_status, 0):
                continue
            if message.provider_event_at and event.happened_at < message.provider_event_at:
                continue
            message.transport_status, message.provider_event_at = state, event.happened_at

    def mail_status_page(self, offset=0, limit=20):
        query = self.session.query(MailMessage)
        return query.count(), query.order_by(MailMessage.id.desc()).offset(offset).limit(limit).all()

    def trim_delivery_events(self, before):
        return self.session.query(MailDeliveryEvent).filter(MailDeliveryEvent.received_at < before).delete(synchronize_session=False)
