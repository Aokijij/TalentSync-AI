"""application recruiting details

Revision ID: 0003_recruiting_details
Revises: 0002_profile_and_job_enrichment
Create Date: 2026-07-30
"""

from alembic import op
import sqlalchemy as sa


revision = "0003_recruiting_details"
down_revision = "0002_profile_and_job_enrichment"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("applications", sa.Column("recruiter_notes", sa.Text(), nullable=True))
    op.add_column("applications", sa.Column("interview_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("applications", "interview_at")
    op.drop_column("applications", "recruiter_notes")
