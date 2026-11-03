"""Require identity confirmation for new social registrations only."""
import sqlalchemy as sa

from alembic import op

revision = "0052_social_registration"
down_revision = "0051_response_followup"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("registration_pending", sa.Boolean(), server_default=sa.false(), nullable=False))


def downgrade():
    with op.batch_alter_table("users") as batch:
        batch.drop_column("registration_pending")
