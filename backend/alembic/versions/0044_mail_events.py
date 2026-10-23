"""Track provider acceptance separately from delivered mail, without payload bodies."""
from alembic import op
import sqlalchemy as sa

revision = "0044_mail_events"
down_revision = "0043_resume_versions"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("mail_messages") as batch:
        batch.add_column(sa.Column("provider_message_id", sa.String(100), nullable=True))
        batch.add_column(sa.Column("transport_status", sa.String(24), nullable=True))
        batch.add_column(sa.Column("provider_event_at", sa.DateTime(), nullable=True))
        batch.create_index("ix_mail_messages_provider_message_id", ["provider_message_id"], unique=True)
    op.create_table("mail_delivery_events", sa.Column("id", sa.String(100), primary_key=True),
        sa.Column("provider_message_id", sa.String(100), nullable=False), sa.Column("event_type", sa.String(40), nullable=False),
        sa.Column("happened_at", sa.DateTime(), nullable=False), sa.Column("received_at", sa.DateTime(), nullable=False))
    op.create_index("ix_mail_delivery_events_provider_message_id", "mail_delivery_events", ["provider_message_id"])


def downgrade():
    op.drop_table("mail_delivery_events")
    with op.batch_alter_table("mail_messages") as batch:
        batch.drop_index("ix_mail_messages_provider_message_id")
        batch.drop_column("provider_event_at")
        batch.drop_column("transport_status")
        batch.drop_column("provider_message_id")
