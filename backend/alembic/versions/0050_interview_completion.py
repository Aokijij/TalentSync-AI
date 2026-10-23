"""Record confirmed interview completion separately from the scheduled time."""
import sqlalchemy as sa

from alembic import op

revision = "0050_interview_completion"
down_revision = "0049_application_review"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("applications", sa.Column("interview_completed_at", sa.DateTime(), nullable=True))


def downgrade():
    with op.batch_alter_table("applications") as batch:
        batch.drop_column("interview_completed_at")
