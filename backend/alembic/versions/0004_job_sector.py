"""job sector

Revision ID: 0004_job_sector
Revises: 0003_recruiting_details
Create Date: 2026-07-30
"""

from alembic import op
import sqlalchemy as sa


revision = "0004_job_sector"
down_revision = "0003_recruiting_details"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("jobs", sa.Column("sector", sa.String(length=100), nullable=True))


def downgrade() -> None:
    op.drop_column("jobs", "sector")
