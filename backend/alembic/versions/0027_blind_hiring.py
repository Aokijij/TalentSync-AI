"""Gradual blind hiring and identity reveal history."""
import sqlalchemy as sa

from alembic import op

revision = "0027_blind_hiring"
down_revision = "0026_learning"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("jobs", sa.Column("blind_hiring", sa.Boolean(), server_default=sa.false(), nullable=False))
    op.add_column("applications", sa.Column("identity_revealed_at", sa.DateTime(), nullable=True))


def downgrade():
    op.drop_column("applications", "identity_revealed_at")
    op.drop_column("jobs", "blind_hiring")
