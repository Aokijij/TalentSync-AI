"""Preserve editorial decisions independently from external source refreshes."""
import sqlalchemy as sa

from alembic import op

revision = "0058_job_publication_review"
down_revision = "0057_ai_writer_usage"
branch_labels = depends_on = None


def upgrade():
    op.add_column("jobs", sa.Column("moderation_status", sa.String(20), nullable=False, server_default="automatic"))
    op.add_column("jobs", sa.Column("moderation_note", sa.Text(), nullable=False, server_default=""))
    op.add_column("jobs", sa.Column("moderation_revision", sa.Integer(), nullable=False, server_default="0"))


def downgrade():
    op.drop_column("jobs", "moderation_revision")
    op.drop_column("jobs", "moderation_note")
    op.drop_column("jobs", "moderation_status")
