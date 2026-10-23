"""Explicit owner boundaries for portability and removal; never export employer notes."""
from datetime import timedelta
from uuid import uuid4

from sqlalchemy import func, or_, update

from app.domain.entities.enums import UserRole
from app.domain.services.learning_activities import public_activity
from app.infrastructure.database import models as m


def columns(row, excluded=()):
    return {column.name: getattr(row, column.name) for column in row.__table__.columns if column.name not in excluded}


class AccountDataRepository:
    def __init__(self, session):
        self.session = session

    def export(self, user):
        pdf_size = self.session.query(func.coalesce(func.sum(func.length(m.ResumeVersion.pdf)), 0)).filter(m.ResumeVersion.user_id == user.id).scalar()
        if pdf_size > 50 * 1024 * 1024:
            raise ValueError("Export size limit")
        result = {"account": columns(user, {"password_hash", "mfa_secret", "mfa_last_counter", "recovery_codes"}),
                  "profile": columns(user.profile, {"embedding"}) if user.profile else None}
        owned = {"recommendations": m.Recommendation, "learning_plan": m.LearningPlan,
                 "assessments": m.AssessmentAttempt, "feedback": m.RecommendationFeedback,
                 "offer_feedback": m.OfferFeedback, "notifications": m.Notification,
                 "drafts": m.CareerCoachState, "cv_versions": m.ResumeVersion, "memberships": m.CompanyMember}
        for key, model in owned.items():
            query = self.session.query(model).filter(model.user_id == user.id)
            if query.count() > 10000:
                raise ValueError("Export row limit")
            excluded = {"pdf", "embedding"} | ({"snapshot"} if model is m.AssessmentAttempt else set())
            result[key] = []
            for row in query.all():
                entry = columns(row, excluded)
                if model is m.AssessmentAttempt:
                    entry["questions"] = [public_activity(item) for item in row.snapshot]
                result[key].append(entry)
        result["followed_companies"] = [columns(row) for row in self.session.query(m.CompanyFollower).filter_by(candidate_user_id=user.id).all()]
        result["linked_accounts"] = [{"provider": row.provider, "connected_at": row.created_at} for row in self.session.query(m.SocialIdentity).filter_by(user_id=user.id).all()]
        result["applications"] = []
        for row in self.session.query(m.Application).filter_by(user_id=user.id).all():
            entry = columns(row, {"recruiter_notes", "interview_evaluations", "screening_adjustment", "screening_answers"})
            entry["screening_answers"] = [{key: answer[key] for key in ("question_id", "question", "answer", "option_id", "text", "question_text") if key in answer} for answer in row.screening_answers or []]
            result["applications"].append(entry)
        result["reports"] = [columns(row, {"appeal"}) for row in self.session.query(m.TrustIncident).filter_by(reporter_user_id=user.id).all()]
        result["calendar"] = [{key: getattr(row, key) for key in ("application_id", "minutes", "state", "last_synced_at")} for row in self.session.query(m.CalendarEvent).filter_by(user_id=user.id).all()]
        pdfs = [(row.id, row.pdf) for row in self.session.query(m.ResumeVersion).filter_by(user_id=user.id).all()]
        return result, pdfs

    def deletion_block(self, user):
        if self.session.query(m.Company.id).filter_by(owner_user_id=user.id).first():
            return "Tu cuenta es propietaria de una organización. Transfiere la propiedad con administración antes de eliminarla; los procesos del equipo deben conservarse."
        if user.role == UserRole.ADMIN and self.session.query(m.User.id).filter(m.User.role == UserRole.ADMIN, m.User.id != user.id).count() == 0:
            return "Debe quedar al menos otra cuenta administradora antes de eliminar esta cuenta."
        return ""

    def lock_deletion(self, user):
        # Lock all administrators before checking the last-admin invariant. SQLite's
        # no-op write provides the equivalent writer serialization.
        if user.role == UserRole.ADMIN:
            self.session.execute(update(m.User).where(m.User.role == UserRole.ADMIN).values(created_at=m.User.created_at))
        else:
            self.session.execute(update(m.User).where(m.User.id == user.id).values(created_at=m.User.created_at))

    def claim_erasure(self, identifier, lease, now):
        return self.session.execute(update(m.FileErasureTask).where(m.FileErasureTask.id == identifier,
            m.FileErasureTask.state != "completed", or_(m.FileErasureTask.lease_until.is_(None), m.FileErasureTask.lease_until < now),
            or_(m.FileErasureTask.next_attempt_at.is_(None), m.FileErasureTask.next_attempt_at <= now)).values(lease_token=lease, lease_until=now + timedelta(minutes=10)).execution_options(synchronize_session=False)).rowcount == 1

    def erasure_task(self, user_id):
        task = m.FileErasureTask(id=uuid4().hex, owner_id=user_id)
        self.session.add(task)
        return task

    def finish_erasure(self, identifier, lease, values):
        return self.session.execute(update(m.FileErasureTask).where(m.FileErasureTask.id == identifier,
            m.FileErasureTask.lease_token == lease).values(**values, lease_token="", lease_until=None).execution_options(synchronize_session=False)).rowcount == 1

    def erase(self, user):
        # Explicit cleanup also works in old SQLite deployments without FK enforcement.
        app_ids = [row[0] for row in self.session.query(m.Application.id).filter_by(user_id=user.id).all()]
        self.session.query(m.CalendarEvent).filter(or_(m.CalendarEvent.user_id == user.id, m.CalendarEvent.application_id.in_(app_ids))).delete(synchronize_session=False)
        for model in (m.CalendarConnection, m.CareerCoachState):
            self.session.query(model).filter_by(user_id=user.id).delete(synchronize_session=False)
        self.session.query(m.InterviewRoom).filter_by(creator_user_id=user.id).update({"creator_user_id": None}, synchronize_session=False)
        self.session.query(m.ModelAuditRun).filter_by(actor_user_id=user.id).update({"actor_user_id": None}, synchronize_session=False)
        self.session.query(m.EventLog).filter(or_(m.EventLog.actor_user_id == user.id,
            (m.EventLog.entity_type == "user") & (m.EventLog.entity_id == user.id),
            (m.EventLog.entity_type == "application") & m.EventLog.entity_id.in_(app_ids))).delete(synchronize_session=False)
        # Remove report text attached to the withdrawn personal application.
        self.session.query(m.TrustIncident).filter(m.TrustIncident.application_id.in_(app_ids)).delete(synchronize_session=False)
        # Historical notifications addressed to the employer can contain a candidate
        # name. Scrub only this candidate's exact submission notification/process.
        own_jobs = {row[0] for row in self.session.query(m.Application.job_id).filter_by(user_id=user.id).all()}
        process_urls = {f"/procesos/{identifier}" for identifier in app_ids}
        submission_bodies = {f"/empresa/postulaciones?job={job.id}": f"{user.name} se postuló a {job.title}."
                             for job in self.session.query(m.Job).filter(m.Job.id.in_(own_jobs)).all()}
        for notice in self.session.query(m.Notification).filter(m.Notification.action_url.in_(process_urls | set(submission_bodies))).all():
            if notice.action_url in process_urls or notice.type == "application_received" and notice.body == submission_bodies.get(notice.action_url):
                notice.body, notice.action_url = "Este proceso personal fue retirado.", None
        if user.role != UserRole.CANDIDATE:
            for application in self.session.query(m.Application).all():
                entries = application.interview_evaluations or []
                if any(entry.get("author_id") == user.id for entry in entries):
                    application.interview_evaluations = [{**entry, "author_id": None, "author": "Cuenta eliminada"} if entry.get("author_id") == user.id else entry for entry in entries]
            for notice in self.session.query(m.Notification).filter_by(type="interview_evaluation").all():
                prefix = f"{user.name} añadió una evaluación interna al proceso de "
                if notice.body.startswith(prefix):
                    notice.body = "Una persona del equipo añadió una evaluación interna al proceso de " + notice.body[len(prefix):]
        self.session.query(m.MailMessage).filter_by(recipient=user.email).delete(synchronize_session=False)
        self.session.query(m.CompanyInvitation).filter_by(email=user.email).delete(synchronize_session=False)
        self.session.expire(user, ["reported_incidents"])
        self.session.delete(user)

    def pending_erasures(self, now):
        return self.session.query(m.FileErasureTask).filter(m.FileErasureTask.state != "completed",
            or_(m.FileErasureTask.next_attempt_at.is_(None), m.FileErasureTask.next_attempt_at <= now),
            or_(m.FileErasureTask.lease_until.is_(None), m.FileErasureTask.lease_until < now)).limit(20).all()

    def retain(self, before):
        counts = {}
        for name, model, predicate in (
            ("tokens", m.AccountToken, m.AccountToken.expires_at < before),
            ("oauth", m.OAuthAttempt, m.OAuthAttempt.expires_at < before),
            ("sessions", m.UserSession, m.UserSession.expires_at < before),
            ("mail", m.MailMessage, m.MailMessage.expires_at < before),
            ("mail_events", m.MailDeliveryEvent, m.MailDeliveryEvent.received_at < before),
            ("receipts", m.FileErasureTask, (m.FileErasureTask.state == "completed") & (m.FileErasureTask.completed_at < before)),
        ):
            counts[name] = self.session.query(model).filter(predicate).delete(synchronize_session=False)
        return counts

    def queue_counts(self):
        return {"mail_pending": self.session.query(m.MailMessage).filter(m.MailMessage.delivery_state.in_(["pending", "retry"])).count(),
                "mail_failed": self.session.query(m.MailMessage).filter_by(delivery_state="failed").count(),
                "calendar_failed": self.session.query(m.CalendarEvent).filter_by(state="failed").count(),
                "file_erasure_pending": self.session.query(m.FileErasureTask).filter(m.FileErasureTask.state != "completed").count()}
