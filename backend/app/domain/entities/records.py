from __future__ import annotations

from datetime import datetime
from typing import Protocol

from app.domain.entities.enums import ApplicationStatus, UserRole


class User(Protocol):
    id: int
    name: str
    email: str
    password_hash: str
    role: UserRole
    created_at: datetime
    profile: Profile | None
    applications: list["Application"]
    recommendations: list["Recommendation"]
    notifications: list["Notification"]


class Profile(Protocol):
    id: int
    user_id: int
    profession: str | None
    skills: list[str]
    experience: str | None
    education: str | None
    location: str | None
    department: str | None
    availability: str | None
    preferred_modality: str | None
    preferred_sector: str | None
    desired_salary: float | None
    phone: str | None
    experiences: list[dict]
    educations: list[dict]
    certifications: list[dict]
    cv_text: str | None
    cv_filename: str | None
    cv_uploaded_at: datetime | None
    embedding: list[float] | None
    updated_at: datetime
    user: User


class Company(Protocol):
    id: int
    owner_user_id: int
    name: str
    nit: str
    description: str | None
    owner: User
    jobs: list["Job"]


class Job(Protocol):
    id: int
    company_id: int
    title: str
    description: str
    requirements: str
    salary: float | None
    location: str | None
    department: str | None
    modality: str
    employment_type: str
    sector: str | None
    status: str
    benefits: list[str]
    pipeline_stages: list[dict] | None
    skills: list[str]
    embedding: list[float] | None
    created_at: datetime
    company: Company
    applications: list["Application"]
    recommendations: list["Recommendation"]

    @property
    def company_name(self) -> str | None: ...
    @property
    def applications_count(self) -> int: ...


class Application(Protocol):
    id: int
    user_id: int
    job_id: int
    status: ApplicationStatus
    created_at: datetime
    recruiter_notes: str | None
    interview_at: datetime | None
    pipeline_stage: str | None
    user: User
    job: Job

    @property
    def job_title(self) -> str | None: ...
    @property
    def company_name(self) -> str | None: ...
    @property
    def candidate_name(self) -> str | None: ...
    @property
    def pipeline_stage_title(self) -> str | None: ...


class Recommendation(Protocol):
    id: int
    user_id: int
    job_id: int
    match_percentage: float
    reasons: list[str]
    created_at: datetime
    user: User
    job: Job

    @property
    def skill_match_percentage(self) -> float: ...
    @property
    def semantic_match_percentage(self) -> float: ...


class Notification(Protocol):
    id: int
    user_id: int
    type: str
    title: str
    body: str
    action_url: str | None
    is_read: bool
    created_at: datetime
    user: User
