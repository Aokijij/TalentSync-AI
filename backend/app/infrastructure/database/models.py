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
from app.domain.services.blind_hiring import candidate_alias, identity_hidden
from app.domain.services.reputation import company_health
from app.domain.services.external_sources import external_portal
from app.infrastructure.database.session import Base


class EventLog(Base):
    __tablename__ = "event_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    actor_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    event_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    entity_id: Mapped[int | None] = mapped_column(Integer, index=True)
    details: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False, index=True
    )


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
    email_verified: Mapped[bool] = mapped_column(default=False, server_default="false", nullable=False)
    mfa_secret: Mapped[str | None] = mapped_column(Text)
    mfa_enabled: Mapped[bool] = mapped_column(default=False, server_default="false", nullable=False)
    mfa_last_counter: Mapped[int | None] = mapped_column(Integer)
    recovery_codes: Mapped[list[str]] = mapped_column(JSON, default=list, server_default="[]", nullable=False)
    privacy_preferences: Mapped[dict] = mapped_column(JSON, default=dict, server_default="{}", nullable=False)
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


class UserSession(Base):
    __tablename__ = "user_sessions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    csrf_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    user_agent: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime)
    mfa_verified: Mapped[bool] = mapped_column(default=False, nullable=False)


class AccountToken(Base):
    __tablename__ = "account_tokens"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    purpose: Mapped[str] = mapped_column(String(40), nullable=False)
    target_email: Mapped[str | None] = mapped_column(String(255))
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime)


class MailMessage(Base):
    __tablename__ = "mail_messages"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    recipient: Mapped[str] = mapped_column(String(255), nullable=False)
    subject: Mapped[str] = mapped_column(String(180), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), unique=True, nullable=False
    )
    profession: Mapped[str | None] = mapped_column(String(160))
    skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    preferences: Mapped[dict] = mapped_column(JSON, default=dict, server_default="{}", nullable=False)
    evidence: Mapped[list[dict]] = mapped_column(JSON, default=list, server_default="[]", nullable=False)
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
    is_external: Mapped[bool] = mapped_column(default=False, nullable=False)
    source_name: Mapped[str | None] = mapped_column(String(80), index=True)
    verification_required: Mapped[bool] = mapped_column(default=False, server_default="false", nullable=False)
    verification_status: Mapped[str] = mapped_column(String(30), default="pending", server_default="pending", nullable=False)
    verification_submission: Mapped[dict] = mapped_column(JSON, default=dict, server_default="{}", nullable=False)
    verification_feedback: Mapped[str | None] = mapped_column(Text)

    owner: Mapped[User] = relationship()
    jobs: Mapped[list["Job"]] = relationship(
        back_populates="company", cascade="all, delete-orphan"
    )
    incidents: Mapped[list["TrustIncident"]] = relationship(back_populates="company", cascade="all, delete-orphan")
    followers: Mapped[list["CompanyFollower"]] = relationship(
        back_populates="company", cascade="all, delete-orphan"
    )

    @property
    def logo_url(self) -> str | None:
        return f"/api/v1/companies/{self.id}/logo" if self.logo_filename else None

    @property
    def cover_url(self) -> str | None:
        return f"/api/v1/companies/{self.id}/cover" if self.cover_filename else None


class CompanyMember(Base):
    __tablename__ = "company_members"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    role: Mapped[str] = mapped_column(String(30), nullable=False)
    active: Mapped[bool] = mapped_column(default=True, nullable=False)
    assigned_job_ids: Mapped[list[int]] = mapped_column(JSON, default=list, nullable=False)


class CompanyInvitation(Base):
    __tablename__ = "company_invitations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(30), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    assigned_job_ids: Mapped[list[int]] = mapped_column(JSON, default=list, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime)


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
    __table_args__ = (
        UniqueConstraint("source_name", "external_id", name="uq_job_external_source"),
    )

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
    required_education_level: Mapped[str | None] = mapped_column(String(40))
    required_study_fields: Mapped[list[str]] = mapped_column(
        JSON, default=list, server_default="[]", nullable=False
    )
    skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    skill_requirements: Mapped[list[dict]] = mapped_column(JSON, default=list, server_default="[]", nullable=False)
    response_days: Mapped[int] = mapped_column(Integer, default=7, server_default="7", nullable=False)
    blind_hiring: Mapped[bool] = mapped_column(default=False, server_default="false", nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    source_kind: Mapped[str] = mapped_column(
        String(20), default="internal", nullable=False
    )
    source_name: Mapped[str | None] = mapped_column(String(80), index=True)
    external_id: Mapped[str | None] = mapped_column(String(180))
    external_url: Mapped[str | None] = mapped_column(String(1000))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, index=True)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime)

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
    def employer_trust(self) -> dict:
        return company_health(self.company) if self.company else {}

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

    @property
    def source_portal(self) -> str | None:
        if self.source_kind != "external":
            return None
        return external_portal(self.external_url, self.location)


class Application(Base):
    __tablename__ = "applications"
    __table_args__ = (
        UniqueConstraint("user_id", "job_id", name="uq_application_user_job"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    version: Mapped[int] = mapped_column(Integer, default=1, server_default="1", nullable=False)
    identity_revealed_at: Mapped[datetime | None] = mapped_column(DateTime)
    first_response_at: Mapped[datetime | None] = mapped_column(DateTime)
    response_due_at: Mapped[datetime | None] = mapped_column(DateTime, index=True)
    reminder_sent_at: Mapped[datetime | None] = mapped_column(DateTime)
    released_at: Mapped[datetime | None] = mapped_column(DateTime)
    candidate_feedback: Mapped[dict] = mapped_column(JSON, default=dict, server_default="{}", nullable=False)
    __mapper_args__ = {"version_id_col": version}
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
        return candidate_alias(self.job_id, self.user_id) if identity_hidden(self.job, self) else self.user.name if self.user else None

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
    match_details: Mapped[dict] = mapped_column(JSON, default=dict, server_default="{}", nullable=False)
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

    @property
    def data_confidence_percentage(self) -> float:
        prefix = "confidence:data:"
        for reason in self.reasons or []:
            if str(reason).startswith(prefix):
                try:
                    return float(str(reason).removeprefix(prefix))
                except ValueError:
                    break
        return 100.0

    @property
    def is_estimated(self) -> bool:
        return "source:external" in (self.reasons or [])


class InterviewRoom(Base):
    __tablename__ = "interview_rooms"
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("applications.id", ondelete="CASCADE"), unique=True, nullable=False)
    creator_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    code: Mapped[str] = mapped_column(Text, default="", nullable=False)
    whiteboard: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    closed: Mapped[bool] = mapped_column(default=False, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    application: Mapped[Application] = relationship()
    __mapper_args__ = {"version_id_col": version}


class InterviewParticipant(Base):
    __tablename__ = "interview_participants"
    __table_args__ = (UniqueConstraint("room_id", "slot", name="uq_interview_participant_slot"),)
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    room_id: Mapped[str] = mapped_column(ForeignKey("interview_rooms.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    slot: Mapped[int] = mapped_column(Integer, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class InterviewSignal(Base):
    __tablename__ = "interview_signals"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    room_id: Mapped[str] = mapped_column(ForeignKey("interview_rooms.id", ondelete="CASCADE"), nullable=False, index=True)
    sender_id: Mapped[str] = mapped_column(String(32), nullable=False)
    recipient_id: Mapped[str] = mapped_column(String(32), nullable=False)
    kind: Mapped[str] = mapped_column(String(10), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class TrustIncident(Base):
    __tablename__ = "trust_incidents"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    reporter_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), index=True, nullable=False)
    application_id: Mapped[int | None] = mapped_column(ForeignKey("applications.id", ondelete="SET NULL"))
    category: Mapped[str] = mapped_column(String(40), nullable=False)
    details: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="open", nullable=False)
    shared_summary: Mapped[str | None] = mapped_column(Text)
    appeal: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    company: Mapped[Company] = relationship(back_populates="incidents")


class ModelAuditRun(Base):
    __tablename__ = "model_audit_runs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    actor_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    version: Mapped[str] = mapped_column(String(80), nullable=False)
    metrics: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class LearningPlan(Base):
    __tablename__ = "learning_plans"
    __table_args__ = (UniqueConstraint("user_id", "resource_id", name="uq_learning_plan_user_resource"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    resource_id: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="in_progress", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)


class AssessmentAttempt(Base):
    __tablename__ = "assessment_attempts"
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    assessment_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    skill: Mapped[str] = mapped_column(String(100), nullable=False)
    version: Mapped[str] = mapped_column(String(30), nullable=False)
    snapshot: Mapped[list[dict]] = mapped_column(JSON, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(String(30), default="active", nullable=False)
    score: Mapped[float | None] = mapped_column(Float)
    passed: Mapped[bool] = mapped_column(default=False, nullable=False)
    feedback: Mapped[list[dict]] = mapped_column(JSON, default=list, nullable=False)
    valid_until: Mapped[datetime | None] = mapped_column(DateTime)


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
