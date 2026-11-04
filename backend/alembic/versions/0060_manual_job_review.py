"""Record time-bounded manual source verification separately from API checks."""
import sqlalchemy as sa

from alembic import op

revision = "0060_manual_job_review"
down_revision = "0059_editorial_jobs"
branch_labels = depends_on = None


def upgrade():
    with op.batch_alter_table("jobs") as batch:
        batch.add_column(sa.Column("external_manual_verified_at", sa.DateTime(), nullable=True))
        batch.add_column(sa.Column("external_manual_verified_until", sa.DateTime(), nullable=True))
        batch.add_column(sa.Column("external_manual_verified_by", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("external_manual_note", sa.Text(), nullable=True))
        batch.add_column(sa.Column("external_manual_source_url", sa.String(1000), nullable=True))
        batch.create_foreign_key("fk_jobs_manual_reviewer", "users", ["external_manual_verified_by"], ["id"], ondelete="SET NULL")


def downgrade():
    with op.batch_alter_table("jobs") as batch:
        batch.drop_constraint("fk_jobs_manual_reviewer", type_="foreignkey")
        for name in ("external_manual_source_url", "external_manual_note", "external_manual_verified_by", "external_manual_verified_until", "external_manual_verified_at"):
            batch.drop_column(name)
