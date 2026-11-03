"""Private coach history and immutable application-specific profile snapshots."""
import sqlalchemy as sa

from alembic import op

revision = "0041_career_coach"
down_revision = "0040_learning_sources"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("career_coach_states",
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("content", sa.JSON(), nullable=False, server_default="{}"))
    op.add_column("applications", sa.Column("coach_snapshot", sa.JSON(), nullable=False, server_default="{}"))


def downgrade():
    op.drop_column("applications", "coach_snapshot")
    op.drop_table("career_coach_states")
