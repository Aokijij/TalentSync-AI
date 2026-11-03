"""Evidence and retry dates for external vacancies; old rows start unconfirmed."""
import sqlalchemy as sa

from alembic import op

revision = "0054_external_job_freshness"
down_revision = "0053_registration_consent"
branch_labels = depends_on = None


def upgrade():
    op.add_column("jobs", sa.Column("external_check_state", sa.String(24), nullable=False, server_default="pending"))
    op.add_column("jobs", sa.Column("external_checked_at", sa.DateTime()))
    op.add_column("jobs", sa.Column("external_verified_at", sa.DateTime()))
    op.add_column("jobs", sa.Column("external_check_reason", sa.String(40), nullable=False, server_default=""))
    op.add_column("jobs", sa.Column("external_next_check_at", sa.DateTime()))
    op.create_index("ix_jobs_external_next_check", "jobs", ["source_kind", "status", "external_next_check_at"])


def downgrade():
    op.drop_index("ix_jobs_external_next_check", table_name="jobs")
    for name in ("external_next_check_at", "external_check_reason", "external_verified_at", "external_checked_at", "external_check_state"):
        op.drop_column("jobs", name)
