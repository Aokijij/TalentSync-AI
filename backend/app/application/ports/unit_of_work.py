from typing import Protocol

from app.domain.repositories.applications import ApplicationRepository
from app.domain.repositories.companies import CompanyRepository
from app.domain.repositories.jobs import JobRepository
from app.domain.repositories.notifications import NotificationRepository
from app.domain.repositories.profiles import ProfileRepository
from app.domain.repositories.recommendations import RecommendationRepository
from app.domain.repositories.users import UserRepository


class UnitOfWork(Protocol):
    users: UserRepository
    profiles: ProfileRepository
    companies: CompanyRepository
    jobs: JobRepository
    applications: ApplicationRepository
    recommendations: RecommendationRepository
    notifications: NotificationRepository

    def add(self, entity: object) -> None: ...
    def delete(self, entity: object) -> None: ...
    def flush(self) -> None: ...
    def commit(self) -> None: ...
    def refresh(self, entity: object) -> None: ...
    def ping(self) -> None: ...
