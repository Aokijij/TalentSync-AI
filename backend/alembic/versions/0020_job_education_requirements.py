"""Add explicit education requirements to jobs.

Revision ID: 0020_job_education_requirements
Revises: 0019_external_job_imports
"""

from alembic import op
import sqlalchemy as sa


revision = "0020_job_education_requirements"
down_revision = "0019_external_job_imports"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("jobs", sa.Column("required_education_level", sa.String(length=40), nullable=True))
    op.add_column("jobs", sa.Column("required_study_fields", sa.JSON(), nullable=False, server_default="[]"))


def downgrade() -> None:
    op.drop_column("jobs", "required_study_fields")
    op.drop_column("jobs", "required_education_level")
