"""Consented preference signals and offline model experiments."""
from alembic import op
import sqlalchemy as sa

revision = "0030_recommendation_feedback"
down_revision = "0029_interview_rooms"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("recommendation_feedback", sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("job_id", sa.Integer(), sa.ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("interested", sa.Boolean(), nullable=False), sa.Column("features", sa.JSON(), nullable=False),
        sa.Column("feature_version", sa.String(180), nullable=False), sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("user_id", "job_id", name="uq_recommendation_feedback_pair"))
    op.create_index("ix_recommendation_feedback_user_id", "recommendation_feedback", ["user_id"])
    op.create_table("model_experiments", sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("version", sa.String(180), nullable=False), sa.Column("status", sa.String(50), nullable=False),
        sa.Column("metrics", sa.JSON(), nullable=False), sa.Column("artifact", sa.JSON(), nullable=False), sa.Column("created_at", sa.DateTime(), nullable=False))


def downgrade():
    op.drop_table("model_experiments")
    op.drop_table("recommendation_feedback")
