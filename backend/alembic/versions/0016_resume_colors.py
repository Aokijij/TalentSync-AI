"""Persist the selected resume color without changing existing designs."""

import sqlalchemy as sa
from alembic import op

revision = "0016_resume_colors"
down_revision = "0015_company_images"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("profiles", sa.Column("resume_color", sa.String(30), nullable=False, server_default="default"))


def downgrade() -> None:
    op.drop_column("profiles", "resume_color")
