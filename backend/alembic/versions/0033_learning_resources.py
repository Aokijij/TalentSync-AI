"""Locally curated educational resources; no external purchases or certifications."""
from alembic import op
import sqlalchemy as sa

revision = "0033_learning_resources"
down_revision = "0032_social_linking"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("learning_resources",
        sa.Column("id", sa.String(100), primary_key=True),
        sa.Column("content", sa.JSON(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False))


def downgrade():
    op.drop_table("learning_resources")
