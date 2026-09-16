"""Add visual identity images to company profiles.

Revision ID: 0015_company_images
Revises: 0014_simplified_flow
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0015_company_images"
down_revision: str | None = "0014_simplified_flow"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("companies", sa.Column("logo_filename", sa.String(255)))
    op.add_column("companies", sa.Column("cover_filename", sa.String(255)))


def downgrade() -> None:
    op.drop_column("companies", "cover_filename")
    op.drop_column("companies", "logo_filename")
