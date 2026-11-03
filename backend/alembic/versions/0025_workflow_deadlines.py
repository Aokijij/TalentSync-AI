"""Response deadlines, feedback and optimistic process updates."""
import sqlalchemy as sa

from alembic import op

revision = "0025_workflow_deadlines"
down_revision = "0024_match_explanations"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("jobs", sa.Column("response_days", sa.Integer(), server_default="7", nullable=False))
    op.add_column("applications", sa.Column("version", sa.Integer(), server_default="1", nullable=False))
    for name in ["response_due_at", "reminder_sent_at", "released_at"]:
        op.add_column("applications", sa.Column(name, sa.DateTime(), nullable=True))
    op.create_index("ix_applications_response_due_at", "applications", ["response_due_at"])
    op.add_column("applications", sa.Column("candidate_feedback", sa.JSON(), server_default="{}", nullable=False))


def downgrade():
    op.drop_index("ix_applications_response_due_at", table_name="applications")
    for name in ["candidate_feedback", "released_at", "reminder_sent_at", "response_due_at", "version"]:
        op.drop_column("applications", name)
    op.drop_column("jobs", "response_days")
