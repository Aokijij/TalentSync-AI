from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import StaleDataError

from app.application.errors import UseCaseError

from app.infrastructure.database.models import (
    Application,
    Company,
    EventLog,
    Job,
    Notification,
    Profile,
    Recommendation,
    User,
)
from app.infrastructure.repositories.accounts import AccountRepository
from app.infrastructure.repositories.applications import ApplicationRepository
from app.infrastructure.repositories.companies import CompanyRepository
from app.infrastructure.repositories.events import EventRepository
from app.infrastructure.repositories.jobs import JobRepository
from app.infrastructure.repositories.notifications import NotificationRepository
from app.infrastructure.repositories.organizations import OrganizationRepository
from app.infrastructure.repositories.profiles import ProfileRepository
from app.infrastructure.repositories.recommendations import RecommendationRepository
from app.infrastructure.repositories.users import UserRepository


class SqlAlchemyUnitOfWork:
    def __init__(self, session: Session):
        self.session = session
        self.organizations = OrganizationRepository(session)
        self.accounts = AccountRepository(session)
        self.events = EventRepository(session, EventLog)
        self.users = UserRepository(session, User)
        self.profiles = ProfileRepository(session, Profile)
        self.companies = CompanyRepository(session, Company)
        self.jobs = JobRepository(session, Job)
        self.applications = ApplicationRepository(session, Application)
        self.recommendations = RecommendationRepository(session, Recommendation)
        self.notifications = NotificationRepository(session, Notification)

    def add(self, entity: object) -> None:
        self.session.add(entity)

    def delete(self, entity: object) -> None:
        self.session.delete(entity)

    def flush(self) -> None:
        self.session.flush()

    def commit(self) -> None:
        try:
            self.session.commit()
        except StaleDataError:
            self.session.rollback()
            raise UseCaseError(status_code=409, detail="El proceso cambió mientras lo editabas; actualiza y vuelve a intentar") from None

    def refresh(self, entity: object) -> None:
        self.session.refresh(entity)

    def ping(self) -> None:
        self.session.execute(text("SELECT 1"))
