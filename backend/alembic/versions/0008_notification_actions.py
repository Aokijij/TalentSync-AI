"""add notification action links

Revision ID: 0008_notification_actions
Revises: 0007_recruitment_pipeline
Create Date: 2026-09-03
"""

from alembic import op
import sqlalchemy as sa

revision = "0008_notification_actions"
down_revision = "0007_recruitment_pipeline"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("notifications", sa.Column("action_url", sa.String(length=255), nullable=True))
    op.execute(
        "UPDATE notifications SET is_read = true "
        "WHERE is_read = false AND id NOT IN "
        "(SELECT MAX(id) FROM notifications GROUP BY user_id, title, body)"
    )


def downgrade() -> None:
    op.drop_column("notifications", "action_url")
