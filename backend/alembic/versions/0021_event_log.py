"""Append-only application event stream (no credentials or CV contents)."""
from alembic import op
import sqlalchemy as sa

revision = "0021_event_log"
down_revision = "0020_job_education_requirements"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "event_log",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("actor_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("event_type", sa.String(80), nullable=False),
        sa.Column("entity_type", sa.String(40), nullable=False),
        sa.Column("entity_id", sa.Integer()),
        sa.Column("details", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    for field in ("actor_user_id", "event_type", "entity_type", "entity_id", "created_at"):
        op.create_index(f"ix_event_log_{field}", "event_log", [field])


def downgrade():
    op.drop_table("event_log")
