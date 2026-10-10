"""Public educational metadata cache; no students, purchases or credentials."""
import sqlalchemy as sa

from alembic import op

revision = "0040_learning_sources"
down_revision = "0039_offer_quality"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("learning_source_snapshots",
        sa.Column("id", sa.String(100), primary_key=True),
        sa.Column("content", sa.JSON(), nullable=False),
        sa.Column("fetched_at", sa.DateTime(), nullable=False),
        sa.Column("attempted_at", sa.DateTime(), nullable=False),
        sa.Column("error", sa.String(250), nullable=False))


def downgrade():
    op.drop_table("learning_source_snapshots")
