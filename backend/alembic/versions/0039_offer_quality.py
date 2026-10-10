"""Structured offer review and explicit, private candidate feedback."""
import sqlalchemy as sa
from alembic import op

revision = "0039_offer_quality"
down_revision = "0038_interview_evaluations"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("jobs", sa.Column("quality_details", sa.JSON(), nullable=True))
    op.add_column("jobs", sa.Column("quality_revision", sa.Integer(), server_default="0", nullable=False))
    op.create_table(
        "offer_feedback",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("job_id", sa.Integer(), sa.ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("reason", sa.String(30), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("user_id", "job_id", name="uq_offer_feedback_pair"),
    )
    op.create_index("ix_offer_feedback_job_revision", "offer_feedback", ["job_id", "revision"])


def downgrade():
    op.drop_table("offer_feedback")
    with op.batch_alter_table("jobs") as batch:
        batch.drop_column("quality_revision")
        batch.drop_column("quality_details")
