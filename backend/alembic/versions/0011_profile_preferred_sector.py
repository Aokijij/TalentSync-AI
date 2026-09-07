"""Add the candidate's preferred professional sector.

Revision ID: 0011_profile_preferred_sector
Revises: 0010_application_pipeline_stage
"""

from alembic import op
import sqlalchemy as sa


revision = "0011_profile_preferred_sector"
down_revision = "0010_application_pipeline_stage"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("profiles", sa.Column("preferred_sector", sa.String(length=100), nullable=True))


def downgrade() -> None:
    op.drop_column("profiles", "preferred_sector")
