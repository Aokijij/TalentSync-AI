"""Bind corporate sessions to their configured tenant/domain and application."""
import sqlalchemy as sa
from alembic import op

revision = "0035_corporate_authority"
down_revision = "0034_admin_sso"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("user_sessions", sa.Column("authentication_authority", sa.String(64), server_default="", nullable=False))


def downgrade():
    with op.batch_alter_table("user_sessions") as batch:
        batch.drop_column("authentication_authority")
