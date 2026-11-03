"""Learning plans and timed, single-use assessment attempts."""
import sqlalchemy as sa

from alembic import op

revision = "0026_learning"
down_revision = "0025_workflow_deadlines"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("learning_plans", sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("resource_id", sa.String(100), nullable=False), sa.Column("status", sa.String(30), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False), sa.Column("completed_at", sa.DateTime()),
        sa.UniqueConstraint("user_id", "resource_id", name="uq_learning_plan_user_resource"))
    op.create_index("ix_learning_plans_user_id", "learning_plans", ["user_id"])
    op.create_table("assessment_attempts", sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("assessment_id", sa.String(100), nullable=False), sa.Column("skill", sa.String(100), nullable=False),
        sa.Column("version", sa.String(30), nullable=False), sa.Column("snapshot", sa.JSON(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=False), sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("submitted_at", sa.DateTime()), sa.Column("status", sa.String(30), nullable=False),
        sa.Column("score", sa.Float()), sa.Column("passed", sa.Boolean(), nullable=False), sa.Column("feedback", sa.JSON(), nullable=False),
        sa.Column("valid_until", sa.DateTime()))
    op.create_index("ix_assessment_attempts_user_id", "assessment_attempts", ["user_id"])
    op.create_index("ix_assessment_attempts_assessment_id", "assessment_attempts", ["assessment_id"])


def downgrade():
    op.drop_table("assessment_attempts")
    op.drop_table("learning_plans")
