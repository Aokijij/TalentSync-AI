"""Retryable removal of private files after account deletion."""
from alembic import op
import sqlalchemy as sa

revision = "0046_account_erasure"
down_revision = "0045_google_calendar"
branch_labels = None
depends_on = None


def upgrade():
    # Deleted IDs must never be reassigned while their private files await cleanup.
    if op.get_bind().dialect.name == "sqlite":
        with op.batch_alter_table("users", recreate="always", table_kwargs={"sqlite_autoincrement": True}):
            pass
    op.create_table("file_erasure_tasks",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("lease_token", sa.String(48), nullable=False),
        sa.Column("lease_until", sa.DateTime()),
        sa.Column("owner_id", sa.Integer(), nullable=True),
        sa.Column("state", sa.String(20), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("next_attempt_at", sa.DateTime()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime()))


def downgrade():
    op.drop_table("file_erasure_tasks")
