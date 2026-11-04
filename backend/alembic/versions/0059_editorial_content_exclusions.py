"""Preserve reviewed source additions and discarded source identities."""
import sqlalchemy as sa

from alembic import op

revision = "0059_editorial_jobs"
down_revision = "0058_job_publication_review"
branch_labels = depends_on = None


def upgrade():
    op.add_column("jobs", sa.Column("editorial_overrides", sa.JSON(), nullable=False, server_default="{}"))
    op.create_table("external_job_exclusions",
        sa.Column("key", sa.String(64), primary_key=True),
        sa.Column("source_name", sa.String(80)), sa.Column("external_id", sa.String(180)),
        sa.Column("external_url", sa.String(1000)), sa.Column("reason", sa.String(80), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("actor_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL")))


def downgrade():
    op.drop_table("external_job_exclusions")
    op.drop_column("jobs", "editorial_overrides")
