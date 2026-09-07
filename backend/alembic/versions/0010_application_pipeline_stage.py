"""Track an application's configurable pipeline stage.

Revision ID: 0010_application_pipeline_stage
Revises: 0009_job_pipeline_stages
"""

from alembic import op
import sqlalchemy as sa


revision = "0010_application_pipeline_stage"
down_revision = "0009_job_pipeline_stages"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("applications", sa.Column("pipeline_stage", sa.String(length=80), nullable=True))
    op.execute(
        """
        UPDATE applications
        SET pipeline_stage = CASE lower(CAST(status AS TEXT))
            WHEN 'seen' THEN 'submitted'
            WHEN 'reviewing' THEN 'shortlisted'
            WHEN 'accepted' THEN 'hired'
            ELSE lower(CAST(status AS TEXT))
        END
        """
    )


def downgrade() -> None:
    op.drop_column("applications", "pipeline_stage")
