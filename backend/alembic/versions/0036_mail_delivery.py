"""Durable SMTP outbox; existing local messages are never sent externally."""
import sqlalchemy as sa
from alembic import op

revision = "0036_mail_delivery"
down_revision = "0035_corporate_authority"
branch_labels = None
depends_on = None


def upgrade():
    for column in [
        sa.Column("delivery_state", sa.String(16), server_default="local", nullable=False),
        sa.Column("attempts", sa.Integer(), server_default="0", nullable=False),
        sa.Column("next_attempt_at", sa.DateTime()),
        sa.Column("lease_token", sa.String(64), server_default="", nullable=False),
        sa.Column("lease_until", sa.DateTime()),
        sa.Column("expires_at", sa.DateTime()),
        sa.Column("sent_at", sa.DateTime()),
        sa.Column("failure_kind", sa.String(32), server_default="", nullable=False),
    ]:
        op.add_column("mail_messages", column)
    op.create_index("ix_mail_messages_delivery_state", "mail_messages", ["delivery_state"])


def downgrade():
    op.drop_index("ix_mail_messages_delivery_state", table_name="mail_messages")
    with op.batch_alter_table("mail_messages") as batch:
        for name in ["failure_kind", "sent_at", "expires_at", "lease_until", "lease_token", "next_attempt_at", "attempts", "delivery_state"]:
            batch.drop_column(name)
