"""Add configurable recruitment stages per job.

Revision ID: 0009_job_pipeline_stages
Revises: 0008_notification_actions
"""

from alembic import op
import sqlalchemy as sa


revision = "0009_job_pipeline_stages"
down_revision = "0008_notification_actions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("jobs", sa.Column("pipeline_stages", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("jobs", "pipeline_stages")
