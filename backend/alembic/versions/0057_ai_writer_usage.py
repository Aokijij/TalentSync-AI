"""Persistent free-plan inference reservations shared by every API worker."""
import sqlalchemy as sa

from alembic import op

revision = "0057_ai_writer_usage"
down_revision = "0056_training_record_dedup"
branch_labels = depends_on = None


def upgrade():
    op.create_table("ai_writer_usage",
        sa.Column("id", sa.String(80), primary_key=True),
        sa.Column("requests", sa.Integer(), nullable=False),
        sa.Column("tokens", sa.Integer(), nullable=False),
        sa.Column("minute", sa.String(12), nullable=False),
        sa.Column("minute_requests", sa.Integer(), nullable=False),
        sa.Column("minute_tokens", sa.Integer(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False))


def downgrade():
    op.drop_table("ai_writer_usage")
