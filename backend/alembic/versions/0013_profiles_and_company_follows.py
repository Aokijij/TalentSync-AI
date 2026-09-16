"""Add resume presentation and public company follow settings.

Revision ID: 0013_profiles_company
Revises: 0012_colombian_departments
"""

from alembic import op
import sqlalchemy as sa


revision = "0013_profiles_company"
down_revision = "0012_colombian_departments"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "applications", sa.Column("resolution_reason", sa.String(length=80))
    )
    op.add_column("profiles", sa.Column("photo_filename", sa.String(length=255)))
    op.add_column(
        "profiles",
        sa.Column(
            "resume_style",
            sa.String(length=30),
            nullable=False,
            server_default="classic",
        ),
    )
    op.add_column("companies", sa.Column("website", sa.String(length=255)))
    op.add_column("companies", sa.Column("sector", sa.String(length=120)))
    op.add_column("companies", sa.Column("size", sa.String(length=80)))
    op.add_column("companies", sa.Column("location", sa.String(length=160)))
    op.add_column("companies", sa.Column("mission", sa.Text()))
    op.add_column(
        "companies",
        sa.Column("values", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
    )
    op.add_column(
        "companies",
        sa.Column("benefits", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
    )
    op.create_table(
        "company_followers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "candidate_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False
        ),
        sa.Column(
            "company_id", sa.Integer(), sa.ForeignKey("companies.id"), nullable=False
        ),
        sa.Column("min_match", sa.Float(), nullable=False, server_default="60"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint(
            "candidate_user_id", "company_id", name="uq_company_follower"
        ),
    )
    op.create_index(
        op.f("ix_company_followers_candidate_user_id"),
        "company_followers",
        ["candidate_user_id"],
    )
    op.create_index(
        op.f("ix_company_followers_company_id"),
        "company_followers",
        ["company_id"],
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_company_followers_company_id"), table_name="company_followers"
    )
    op.drop_index(
        op.f("ix_company_followers_candidate_user_id"),
        table_name="company_followers",
    )
    op.drop_table("company_followers")
    for column in ("benefits", "values", "mission", "location", "size", "sector", "website"):
        op.drop_column("companies", column)
    op.drop_column("profiles", "resume_style")
    op.drop_column("profiles", "photo_filename")
    op.drop_column("applications", "resolution_reason")
