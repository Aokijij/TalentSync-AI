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
    languages: list[dict]
    cv_text: str | None
    cv_filename: str | None
    cv_uploaded_at: datetime | None
    photo_filename: str | None
    photo_url: str | None
    resume_style: str
    resume_color: str
    embedding: list[float] | None
    updated_at: datetime
    user: User


class Company(Protocol):
    id: int
    owner_user_id: int
    name: str
    nit: str
    description: str | None
    website: str | None
    sector: str | None
    size: str | None
    location: str | None
    mission: str | None
    values: list[str]
    benefits: list[str]
    logo_filename: str | None
    cover_filename: str | None
    is_external: bool
    source_name: str | None
    logo_url: str | None
    cover_url: str | None
    owner: User
    jobs: list["Job"]


class CompanyFollower(Protocol):
    id: int
    candidate_user_id: int
    company_id: int
    min_match: float
    created_at: datetime
    candidate: User
    company: Company


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
    languages: list[dict]
    application_questions: list[dict]
    skills: list[str]
    embedding: list[float] | None
    created_at: datetime
    source_kind: str
    source_name: str | None
    external_id: str | None
    external_url: str | None
    expires_at: datetime | None
    last_seen_at: datetime | None
    company: Company
    applications: list["Application"]
    recommendations: list["Recommendation"]

    @property
    def company_name(self) -> str | None: ...
    @property
    def applications_count(self) -> int: ...
    @property
    def application_questions_count(self) -> int: ...


class Application(Protocol):
    id: int
    user_id: int
    job_id: int
    status: ApplicationStatus
    created_at: datetime
    recruiter_notes: str | None
    interview_at: datetime | None
    pipeline_stage: str | None
    resolution_reason: str | None
    screening_answers: list[dict]
    screening_adjustment: float
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
    @property
    def base_match_percentage(self) -> float | None: ...
    @property
    def adjusted_match_percentage(self) -> float | None: ...


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
    @property
    def professional_context_percentage(self) -> float: ...


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
    category: str
