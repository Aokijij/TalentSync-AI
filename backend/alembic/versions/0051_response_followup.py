"""Separate response delays and pauses from hiring outcomes."""
import sqlalchemy as sa

from alembic import op

revision = "0051_response_followup"
down_revision = "0050_interview_completion"
branch_labels = None
depends_on = None


def upgrade():
    for name in ("response_overdue_at", "response_paused_at", "deadline_missed_at"):
        op.add_column("applications", sa.Column(name, sa.DateTime(), nullable=True))
    op.add_column("applications", sa.Column("deadline_extension_count", sa.Integer(), nullable=False, server_default="0"))
    op.create_index("ix_applications_job_paused", "applications", ["job_id", "response_paused_at"])


def downgrade():
    op.drop_index("ix_applications_job_paused", table_name="applications")
    with op.batch_alter_table("applications") as batch:
        for name in ("response_overdue_at", "response_paused_at", "deadline_missed_at", "deadline_extension_count"):
            batch.drop_column(name)
