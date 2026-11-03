"""Track administrative SSO sessions and subject-bound second-factor challenges."""
from alembic import op
import sqlalchemy as sa

revision = "0034_admin_sso"
down_revision = "0033_learning_resources"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("user_sessions", sa.Column("authentication_method", sa.String(20), server_default="password", nullable=False))
    op.add_column("account_tokens", sa.Column("context", sa.JSON(), server_default="{}", nullable=False))


def downgrade():
    with op.batch_alter_table("account_tokens") as batch:
        batch.drop_column("context")
    with op.batch_alter_table("user_sessions") as batch:
        batch.drop_column("authentication_method")
