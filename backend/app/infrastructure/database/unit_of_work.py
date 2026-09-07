from sqlalchemy import text
from sqlalchemy.orm import Session

from app.infrastructure.database.models import (
    Application,
    Company,
    Job,
    Notification,
    Profile,
    Recommendation,
    User,
)
from app.infrastructure.repositories.applications import ApplicationRepository
from app.infrastructure.repositories.companies import CompanyRepository
from app.infrastructure.repositories.jobs import JobRepository
from app.infrastructure.repositories.notifications import NotificationRepository
from app.infrastructure.repositories.profiles import ProfileRepository
from app.infrastructure.repositories.recommendations import RecommendationRepository
from app.infrastructure.repositories.users import UserRepository


class SqlAlchemyUnitOfWork:
    def __init__(self, session: Session):
        self.session = session
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
        self.session.commit()

    def refresh(self, entity: object) -> None:
        self.session.refresh(entity)

    def ping(self) -> None:
        self.session.execute(text("SELECT 1"))
