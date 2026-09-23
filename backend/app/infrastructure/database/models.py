from datetime import datetime

from sqlalchemy import (
    JSON,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.entities.enums import ApplicationStatus, UserRole
from app.infrastructure.database.session import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole), default=UserRole.CANDIDATE, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    profile: Mapped["Profile | None"] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    applications: Mapped[list["Application"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    recommendations: Mapped[list["Recommendation"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    notifications: Mapped[list["Notification"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    company_follows: Mapped[list["CompanyFollower"]] = relationship(
        back_populates="candidate", cascade="all, delete-orphan"
    )


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), unique=True, nullable=False
    )
    profession: Mapped[str | None] = mapped_column(String(160))
    skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    experience: Mapped[str | None] = mapped_column(Text)
    education: Mapped[str | None] = mapped_column(Text)
    location: Mapped[str | None] = mapped_column(String(120))
    department: Mapped[str | None] = mapped_column(String(120))
    availability: Mapped[str | None] = mapped_column(String(80))
    preferred_modality: Mapped[str | None] = mapped_column(String(40))
    preferred_sector: Mapped[str | None] = mapped_column(String(100))
    desired_salary: Mapped[float | None] = mapped_column(Float)
    phone: Mapped[str | None] = mapped_column(String(40))
    experiences: Mapped[list[dict]] = mapped_column(JSON, default=list)
    educations: Mapped[list[dict]] = mapped_column(JSON, default=list)
    certifications: Mapped[list[dict]] = mapped_column(JSON, default=list)
    languages: Mapped[list[dict]] = mapped_column(JSON, default=list, server_default="[]", nullable=False)
    cv_text: Mapped[str | None] = mapped_column(Text)
    cv_filename: Mapped[str | None] = mapped_column(String(255))
    cv_uploaded_at: Mapped[datetime | None] = mapped_column(DateTime)
    photo_filename: Mapped[str | None] = mapped_column(String(255))
    resume_style: Mapped[str] = mapped_column(
        String(30), default="classic", nullable=False
    )
    resume_color: Mapped[str] = mapped_column(
        String(30), default="default", server_default="default", nullable=False
    )
    embedding: Mapped[list[float] | None] = mapped_column(JSON)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    user: Mapped[User] = relationship(back_populates="profile")

    @property
    def photo_url(self) -> str | None:
        return f"/api/v1/profiles/{self.user_id}/photo" if self.photo_filename else None


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    nit: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    website: Mapped[str | None] = mapped_column(String(255))
    sector: Mapped[str | None] = mapped_column(String(120))
    size: Mapped[str | None] = mapped_column(String(80))
    location: Mapped[str | None] = mapped_column(String(160))
    mission: Mapped[str | None] = mapped_column(Text)
    values: Mapped[list[str]] = mapped_column(JSON, default=list)
    benefits: Mapped[list[str]] = mapped_column(JSON, default=list)
    logo_filename: Mapped[str | None] = mapped_column(String(255))
    cover_filename: Mapped[str | None] = mapped_column(String(255))

    owner: Mapped[User] = relationship()
    jobs: Mapped[list["Job"]] = relationship(
        back_populates="company", cascade="all, delete-orphan"
    )
    followers: Mapped[list["CompanyFollower"]] = relationship(
        back_populates="company", cascade="all, delete-orphan"
    )

    @property
    def logo_url(self) -> str | None:
        return f"/api/v1/companies/{self.id}/logo" if self.logo_filename else None

    @property
    def cover_url(self) -> str | None:
        return f"/api/v1/companies/{self.id}/cover" if self.cover_filename else None


class CompanyFollower(Base):
    __tablename__ = "company_followers"
    __table_args__ = (
        UniqueConstraint(
            "candidate_user_id", "company_id", name="uq_company_follower"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    candidate_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id"), nullable=False, index=True
    )
    min_match: Mapped[float] = mapped_column(Float, default=60.0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    candidate: Mapped[User] = relationship(back_populates="company_follows")
    company: Mapped[Company] = relationship(back_populates="followers")


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    requirements: Mapped[str] = mapped_column(Text, nullable=False)
    salary: Mapped[float | None] = mapped_column(Float)
    location: Mapped[str | None] = mapped_column(String(120))
    department: Mapped[str | None] = mapped_column(String(120))
    modality: Mapped[str] = mapped_column(String(40), default="remote", nullable=False)
    employment_type: Mapped[str] = mapped_column(
        String(50), default="full_time", nullable=False
    )
    sector: Mapped[str | None] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(30), default="active", nullable=False)
    benefits: Mapped[list[str]] = mapped_column(JSON, default=list)
    pipeline_stages: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    languages: Mapped[list[dict]] = mapped_column(JSON, default=list, server_default="[]", nullable=False)
    application_questions: Mapped[list[dict]] = mapped_column(
        JSON, default=list, server_default="[]", nullable=False
    )
    skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    embedding: Mapped[list[float] | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    company: Mapped[Company] = relationship(back_populates="jobs")
    applications: Mapped[list["Application"]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )
    recommendations: Mapped[list["Recommendation"]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )

    @property
    def company_name(self) -> str | None:
        return self.company.name if self.company else None

    @property
    def applications_count(self) -> int:
        return len(self.applications or [])

    @property
    def application_questions_count(self) -> int:
        return len(self.application_questions or [])

    @property
    def company_logo_url(self) -> str | None:
        return self.company.logo_url if self.company else None

    @property
    def company_description(self) -> str | None:
        return self.company.description if self.company else None

    @property
    def company_website(self) -> str | None:
        return self.company.website if self.company else None

    @property
    def company_size(self) -> str | None:
        return self.company.size if self.company else None

    @property
    def company_location(self) -> str | None:
        return self.company.location if self.company else None


class Application(Base):
    __tablename__ = "applications"
    __table_args__ = (
        UniqueConstraint("user_id", "job_id", name="uq_application_user_job"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"), nullable=False)
    status: Mapped[ApplicationStatus] = mapped_column(
        Enum(ApplicationStatus), default=ApplicationStatus.SUBMITTED, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    recruiter_notes: Mapped[str | None] = mapped_column(Text)
    interview_at: Mapped[datetime | None] = mapped_column(DateTime)
    pipeline_stage: Mapped[str | None] = mapped_column(String(80), nullable=True)
    resolution_reason: Mapped[str | None] = mapped_column(String(80), nullable=True)
    screening_answers: Mapped[list[dict]] = mapped_column(
        JSON, default=list, server_default="[]", nullable=False
    )
    screening_adjustment: Mapped[float] = mapped_column(
        Float, default=0.0, server_default="0", nullable=False
    )

    user: Mapped[User] = relationship(back_populates="applications")
    job: Mapped[Job] = relationship(back_populates="applications")

    @property
    def job_title(self) -> str | None:
        return self.job.title if self.job else None

    @property
    def company_name(self) -> str | None:
        return self.job.company.name if self.job and self.job.company else None

    @property
    def candidate_name(self) -> str | None:
        return self.user.name if self.user else None

    @property
    def pipeline_stage_title(self) -> str | None:
        if not self.job:
            return None
        stage_id = self.pipeline_stage
        if stage_id is None:
            value = (
                self.status.value if hasattr(self.status, "value") else str(self.status)
            )
            stage_id = {
                "seen": "submitted",
                "reviewing": "reviewing",
                "shortlisted": "reviewing",
                "technical_interview": "interview",
                "psychometric_test": "interview",
                "accepted": "hired",
            }.get(value, value)
        for stage in self.job.pipeline_stages or []:
            if stage.get("id") == stage_id:
                return stage.get("title")
        return stage_id.replace("_", " ").capitalize()

    @property
    def base_match_percentage(self) -> float | None:
        if not self.job:
            return None
        recommendation = next(
            (
                item
                for item in self.job.recommendations or []
                if item.user_id == self.user_id
            ),
            None,
        )
        return recommendation.match_percentage if recommendation else None

    @property
    def adjusted_match_percentage(self) -> float | None:
        base = self.base_match_percentage
        if base is None:
            return None
        return max(0.0, min(100.0, base + (self.screening_adjustment or 0.0)))


class Recommendation(Base):
    __tablename__ = "recommendations"
    __table_args__ = (
        UniqueConstraint("user_id", "job_id", name="uq_recommendation_user_job"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"), nullable=False)
    match_percentage: Mapped[float] = mapped_column(Float, nullable=False)
    reasons: Mapped[list[str]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    user: Mapped[User] = relationship(back_populates="recommendations")
    job: Mapped[Job] = relationship(back_populates="recommendations")

    def _score_reason(self, name: str) -> float:
        prefix = f"score:{name}:"
        for reason in self.reasons or []:
            if str(reason).startswith(prefix):
                try:
                    return float(str(reason).removeprefix(prefix))
                except ValueError:
                    return 0.0
        return 0.0

    @property
    def skill_match_percentage(self) -> float:
        return self._score_reason("skills")

    @property
    def semantic_match_percentage(self) -> float:
        return self._score_reason("context") or self._score_reason("semantic")

    @property
    def professional_context_percentage(self) -> float:
        return self._score_reason("context") or self._score_reason("semantic")

    @property
    def language_match_percentage(self) -> float | None:
        if any(reason.startswith("score:languages:") for reason in self.reasons or []):
            return self._score_reason("languages")
        return None


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(220), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    action_url: Mapped[str | None] = mapped_column(String(255))
    is_read: Mapped[bool] = mapped_column(default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    user: Mapped[User] = relationship(back_populates="notifications")

    @property
    def category(self) -> str:
        if self.type in {"company_job_match", "candidate_invitation"}:
            return "opportunities"
        if self.type in {
            "application_received",
            "application_updated",
            "application_status",
            "application_interview",
            "application_selected",
            "application_not_selected",
        }:
            return "applications"
        return "system"
