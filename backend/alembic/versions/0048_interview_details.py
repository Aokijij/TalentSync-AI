"""Keep the agreed interview format, duration and access details."""
from alembic import op
import sqlalchemy as sa

revision = "0048_interview_details"
down_revision = "0047_schema_alignment"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("applications", sa.Column("interview_details", sa.JSON(), nullable=False, server_default="{}"))


def downgrade():
    with op.batch_alter_table("applications") as batch:
        batch.drop_column("interview_details")
