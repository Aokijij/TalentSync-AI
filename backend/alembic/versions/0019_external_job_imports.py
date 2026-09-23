"""Add traceable external companies and vacancies."""

import sqlalchemy as sa
from alembic import op

revision = "0019_external_job_imports"
down_revision = "0018_screening_questions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "companies",
        sa.Column("is_external", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column("companies", sa.Column("source_name", sa.String(80)))
    op.create_index("ix_companies_source_name", "companies", ["source_name"])
    op.add_column(
        "jobs",
        sa.Column("source_kind", sa.String(20), nullable=False, server_default="internal"),
    )
    op.add_column("jobs", sa.Column("source_name", sa.String(80)))
    op.add_column("jobs", sa.Column("external_id", sa.String(180)))
    op.add_column("jobs", sa.Column("external_url", sa.String(1000)))
    op.add_column("jobs", sa.Column("expires_at", sa.DateTime()))
    op.add_column("jobs", sa.Column("last_seen_at", sa.DateTime()))
    op.create_index("ix_jobs_source_name", "jobs", ["source_name"])
    op.create_index("ix_jobs_expires_at", "jobs", ["expires_at"])
    with op.batch_alter_table("jobs") as batch_op:
        batch_op.create_unique_constraint(
            "uq_job_external_source", ["source_name", "external_id"]
        )


def downgrade() -> None:
    with op.batch_alter_table("jobs") as batch_op:
        batch_op.drop_constraint("uq_job_external_source", type_="unique")
    op.drop_index("ix_jobs_expires_at", table_name="jobs")
    op.drop_index("ix_jobs_source_name", table_name="jobs")
    for column in (
        "last_seen_at",
        "expires_at",
        "external_url",
        "external_id",
        "source_name",
        "source_kind",
    ):
        op.drop_column("jobs", column)
    op.drop_index("ix_companies_source_name", table_name="companies")
    op.drop_column("companies", "source_name")
    op.drop_column("companies", "is_external")
