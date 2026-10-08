from datetime import datetime

from sqlalchemy import update

from app.infrastructure.database.models import (
    AccountToken,
    MailMessage,
    User,
    UserSession,
)


class AccountRepository:
    def __init__(self, session):
        self.session = session

    def new_session(self, **values):
        return UserSession(**values)

    def new_token(self, **values):
        return AccountToken(**values)

    def new_message(self, **values):
        return MailMessage(**values)

    def session_by_hash(self, digest):
        return self.session.query(UserSession).filter_by(token_hash=digest).first()

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
