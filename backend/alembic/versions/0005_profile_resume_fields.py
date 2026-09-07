"""structured profile resume fields

Revision ID: 0005_resume_fields
Revises: 0004_job_sector
Create Date: 2026-08-19
"""
from alembic import op
import sqlalchemy as sa

revision = "0005_resume_fields"
down_revision = "0004_job_sector"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column("profiles", sa.Column("phone", sa.String(length=40), nullable=True))
    op.add_column("profiles", sa.Column("experiences", sa.JSON(), nullable=True))
    op.add_column("profiles", sa.Column("educations", sa.JSON(), nullable=True))
    op.add_column("profiles", sa.Column("certifications", sa.JSON(), nullable=True))

def downgrade() -> None:
    op.drop_column("profiles", "certifications")
    op.drop_column("profiles", "educations")
    op.drop_column("profiles", "experiences")
    op.drop_column("profiles", "phone")
