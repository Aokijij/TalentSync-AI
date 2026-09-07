"""profile and job enrichment

Revision ID: 0002_profile_and_job_enrichment
Revises: 0001_initial_schema
Create Date: 2026-07-30
"""

from alembic import op
import sqlalchemy as sa


revision = "0002_profile_and_job_enrichment"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("profiles", sa.Column("location", sa.String(length=120), nullable=True))
    op.add_column("profiles", sa.Column("availability", sa.String(length=80), nullable=True))
    op.add_column("profiles", sa.Column("preferred_modality", sa.String(length=40), nullable=True))
    op.add_column("profiles", sa.Column("desired_salary", sa.Float(), nullable=True))
    op.add_column("profiles", sa.Column("cv_filename", sa.String(length=255), nullable=True))
    op.add_column("profiles", sa.Column("cv_uploaded_at", sa.DateTime(), nullable=True))
    op.add_column("jobs", sa.Column("location", sa.String(length=120), nullable=True))
    op.add_column("jobs", sa.Column("modality", sa.String(length=40), nullable=False, server_default="remote"))
    op.add_column("jobs", sa.Column("employment_type", sa.String(length=50), nullable=False, server_default="full_time"))
    op.add_column("jobs", sa.Column("status", sa.String(length=30), nullable=False, server_default="active"))
    op.add_column("jobs", sa.Column("benefits", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("jobs", "benefits")
    op.drop_column("jobs", "status")
    op.drop_column("jobs", "employment_type")
    op.drop_column("jobs", "modality")
    op.drop_column("jobs", "location")
    op.drop_column("profiles", "cv_uploaded_at")
    op.drop_column("profiles", "cv_filename")
    op.drop_column("profiles", "desired_salary")
    op.drop_column("profiles", "preferred_modality")
    op.drop_column("profiles", "availability")
    op.drop_column("profiles", "location")
