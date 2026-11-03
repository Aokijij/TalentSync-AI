"""Structured requirements, candidate preferences and match explanations."""
import sqlalchemy as sa

from alembic import op

revision = "0024_match_explanations"
down_revision = "0023_organization_access"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("profiles", sa.Column("preferences", sa.JSON(), server_default="{}", nullable=False))
    op.add_column("profiles", sa.Column("evidence", sa.JSON(), server_default="[]", nullable=False))
    op.add_column("jobs", sa.Column("skill_requirements", sa.JSON(), server_default="[]", nullable=False))
    op.add_column("recommendations", sa.Column("match_details", sa.JSON(), server_default="{}", nullable=False))


def downgrade():
    op.drop_column("recommendations", "match_details")
    op.drop_column("jobs", "skill_requirements")
    op.drop_column("profiles", "evidence")
    op.drop_column("profiles", "preferences")
