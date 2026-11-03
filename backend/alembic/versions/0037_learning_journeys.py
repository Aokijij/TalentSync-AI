"""Persistent guided learning drafts and optimistic concurrency."""
import sqlalchemy as sa
from alembic import op

revision = "0037_learning_journeys"
down_revision = "0036_mail_delivery"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("learning_plans", sa.Column("progress", sa.JSON(), server_default="{}", nullable=False))
    op.add_column("learning_plans", sa.Column("version", sa.Integer(), server_default="1", nullable=False))


def downgrade():
    with op.batch_alter_table("learning_plans") as batch:
        batch.drop_column("version")
        batch.drop_column("progress")
