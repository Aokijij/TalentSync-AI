"""Atomic reservations across workers; no prompts or generated text are stored."""
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm.exc import StaleDataError

from app.application.errors import UseCaseError
from app.infrastructure.database.models import AIWriterUsage
from app.infrastructure.database.session import SessionLocal


@dataclass(frozen=True)
class Reservation:
    keys: tuple[str, ...]
    minute: str
    tokens: int


class WritingBudget:
    def __init__(self, config, session_factory=SessionLocal, clock=None):
        self.config, self.sessions = config, session_factory
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    def reserve(self, tokens, owner_id=None):
        now = self.clock()
        day, minute = now.strftime("%Y%m%d"), now.strftime("%Y%m%d%H%M")
        keys = (f"groq-{day}",) + ((f"groq-{day}-user-{owner_id}",) if owner_id is not None else ())
        if tokens > self.config.groq_minute_tokens:
            raise UseCaseError(422, "El texto es demasiado extenso para el cupo disponible. Acorta la descripción y conserva lo esencial")
        for _ in range(5):
            try:
                with self.sessions() as db:
                    for index, key in enumerate(keys):
                        row = db.query(AIWriterUsage).filter_by(id=key).with_for_update().one_or_none()
                        if row is None:
                            row = AIWriterUsage(id=key, requests=0, tokens=0, minute=minute, minute_requests=0, minute_tokens=0)
                            db.add(row)
                        if row.minute != minute:
                            row.minute, row.minute_requests, row.minute_tokens = minute, 0, 0
                        daily = self.config.groq_daily_requests if index == 0 else self.config.groq_user_daily_requests
                        per_minute = self.config.groq_minute_requests if index == 0 else 5
                        if row.requests >= daily or row.tokens + tokens > self.config.groq_daily_tokens:
                            raise UseCaseError(429, "Se agotó el cupo gratuito de redacción por hoy. Tu texto se conserva y puedes editarlo directamente")
                        if row.minute_requests >= per_minute or row.minute_tokens + tokens > self.config.groq_minute_tokens:
                            raise UseCaseError(429, "Hay varias propuestas en preparación. Espera un minuto y vuelve a intentarlo; tu texto se conserva")
                        row.requests += 1
                        row.tokens += tokens
                        row.minute_requests += 1
                        row.minute_tokens += tokens
                    db.commit()
                return Reservation(keys, minute, tokens)
            except (IntegrityError, StaleDataError, OperationalError):
                continue
        raise UseCaseError(503, "No pudimos reservar el cupo de redacción. Inténtalo de nuevo en un momento")

    def settle(self, reservation, used_tokens):
        if type(used_tokens) is not int or not 0 <= used_tokens <= reservation.tokens:
            return
        refund = reservation.tokens - used_tokens
        if not refund:
            return
        for _ in range(5):
            try:
                with self.sessions() as db:
                    for key in reservation.keys:
                        row = db.query(AIWriterUsage).filter_by(id=key).with_for_update().one_or_none()
                        if row is None:
                            continue
                        row.tokens = max(0, row.tokens - refund)
                        if row.minute == reservation.minute:
                            row.minute_tokens = max(0, row.minute_tokens - refund)
                    db.commit()
                return
            except (IntegrityError, StaleDataError, OperationalError):
                continue
        # Keeping a reservation is safer than allowing unaccounted requests.
