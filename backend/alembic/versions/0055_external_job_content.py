"""Source publication date and evidence of extracted external job content."""
import sqlalchemy as sa

from alembic import op

revision = "0055_external_job_content"
down_revision = "0054_external_job_freshness"
branch_labels = depends_on = None


def upgrade():
    op.add_column("jobs", sa.Column("external_published_at", sa.DateTime(), nullable=True))
    op.add_column("jobs", sa.Column("external_content", sa.JSON(), nullable=True))
    op.create_index("ix_jobs_external_published_at", "jobs", ["external_published_at"])


def downgrade():
    op.drop_index("ix_jobs_external_published_at", table_name="jobs")
    op.drop_column("jobs", "external_content")
    op.drop_column("jobs", "external_published_at")
