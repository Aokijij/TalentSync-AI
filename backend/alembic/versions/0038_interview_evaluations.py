"""Private interview evaluations, outside the audit stream."""
import sqlalchemy as sa
from alembic import op

revision = "0038_interview_evaluations"
down_revision = "0037_learning_journeys"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("applications", sa.Column("interview_evaluations", sa.JSON(), server_default="[]", nullable=False))


def downgrade():
    with op.batch_alter_table("applications") as batch:
        batch.drop_column("interview_evaluations")
