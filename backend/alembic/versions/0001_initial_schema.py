"""initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-06-03
"""

from alembic import op
import sqlalchemy as sa

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    user_role = sa.Enum("CANDIDATE", "COMPANY", "ADMIN", name="userrole")
    app_status = sa.Enum("SUBMITTED", "REVIEWING", "ACCEPTED", "REJECTED", name="applicationstatus")

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", user_role, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)

    op.create_table(
        "profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, unique=True),
        sa.Column("profession", sa.String(length=160)),
        sa.Column("skills", sa.JSON()),
        sa.Column("experience", sa.Text()),
        sa.Column("education", sa.Text()),
        sa.Column("cv_text", sa.Text()),
        sa.Column("embedding", sa.JSON()),
        sa.Column("updated_at", sa.DateTime()),
    )
    op.create_table(
        "companies",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("owner_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name", sa.String(length=180), nullable=False),
        sa.Column("nit", sa.String(length=80), nullable=False, unique=True),
        sa.Column("description", sa.Text()),
    )
    op.create_table(
        "jobs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("title", sa.String(length=180), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("requirements", sa.Text(), nullable=False),
        sa.Column("salary", sa.Float()),
        sa.Column("skills", sa.JSON()),
        sa.Column("embedding", sa.JSON()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "applications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("job_id", sa.Integer(), sa.ForeignKey("jobs.id"), nullable=False),
        sa.Column("status", app_status, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("user_id", "job_id", name="uq_application_user_job"),
    )
    op.create_table(
        "recommendations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("job_id", sa.Integer(), sa.ForeignKey("jobs.id"), nullable=False),
        sa.Column("match_percentage", sa.Float(), nullable=False),
        sa.Column("reasons", sa.JSON()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("user_id", "job_id", name="uq_recommendation_user_job"),
    )


def downgrade() -> None:
    op.drop_table("recommendations")
    op.drop_table("applications")
    op.drop_table("jobs")
    op.drop_table("companies")
    op.drop_table("profiles")
    op.drop_index(op.f("ix_users_id"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
    sa.Enum(name="applicationstatus").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="userrole").drop(op.get_bind(), checkfirst=True)
