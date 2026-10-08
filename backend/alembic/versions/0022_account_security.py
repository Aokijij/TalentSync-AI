"""Revocable browser sessions, one-use account actions and local mail."""
from alembic import op
import sqlalchemy as sa

revision = "0022_account_security"
down_revision = "0021_event_log"
branch_labels = None
depends_on = None


def upgrade():
    for column in [
        sa.Column("email_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("mfa_secret", sa.Text()),
        sa.Column("mfa_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("mfa_last_counter", sa.Integer()),
        sa.Column("recovery_codes", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("privacy_preferences", sa.JSON(), nullable=False, server_default="{}"),
    ]:
        op.add_column("users", column)
    op.create_table("user_sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("token_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("csrf_hash", sa.String(64), nullable=False),
        sa.Column("user_agent", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("revoked_at", sa.DateTime()),
        sa.Column("mfa_verified", sa.Boolean(), nullable=False),
    )
    op.create_table("account_tokens",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("token_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("purpose", sa.String(40), nullable=False),
        sa.Column("target_email", sa.String(255)),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("used_at", sa.DateTime()),
    )
    op.create_table("mail_messages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("recipient", sa.String(255), nullable=False),
        sa.Column("subject", sa.String(180), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )


def downgrade():
    for table in ("mail_messages", "account_tokens", "user_sessions"):
        op.drop_table(table)
    for column in ("privacy_preferences", "recovery_codes", "mfa_last_counter", "mfa_enabled", "mfa_secret", "email_verified"):
        op.drop_column("users", column)
