"""Track actual individual reviews without changing recruitment stages."""
from alembic import op
import sqlalchemy as sa

revision = "0049_application_review"
down_revision = "0048_interview_details"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("applications", sa.Column("reviewed_at", sa.DateTime(), nullable=True))
    op.create_index("ix_applications_job_reviewed", "applications", ["job_id", "reviewed_at"])


def downgrade():
    op.drop_index("ix_applications_job_reviewed", table_name="applications")
    with op.batch_alter_table("applications") as batch:
        batch.drop_column("reviewed_at")
