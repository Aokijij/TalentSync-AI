"""Explicit personal calendar connections and idempotent interview events."""
from alembic import op
import sqlalchemy as sa

revision = "0045_google_calendar"
down_revision = "0044_mail_events"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("calendar_connections", sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("refresh_cipher", sa.Text(), nullable=False), sa.Column("connected_at", sa.DateTime(), nullable=False), sa.Column("last_error", sa.String(32), nullable=False))
    op.create_table("calendar_events", sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("application_id", sa.Integer(), sa.ForeignKey("applications.id", ondelete="CASCADE"), nullable=False),
        sa.Column("remote_id", sa.String(64), nullable=False), sa.Column("minutes", sa.Integer(), nullable=False),
        sa.Column("application_version", sa.Integer(), nullable=False), sa.Column("state", sa.String(24), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False), sa.Column("next_attempt_at", sa.DateTime()), sa.Column("last_synced_at", sa.DateTime()),
        sa.Column("error_code", sa.String(32), nullable=False), sa.Column("lease_token", sa.String(48), nullable=False), sa.Column("lease_until", sa.DateTime()),
        sa.UniqueConstraint("user_id", "application_id", name="uq_calendar_event_owner_application"))
    op.create_index("ix_calendar_events_user_id", "calendar_events", ["user_id"])
    op.create_index("ix_calendar_events_application_id", "calendar_events", ["application_id"])


def downgrade():
    op.drop_table("calendar_events")
    op.drop_table("calendar_connections")
