"""Reviewable incidents, response observations and model snapshots."""
from alembic import op
import sqlalchemy as sa

revision = "0028_ecosystem_health"
down_revision = "0027_blind_hiring"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("applications", sa.Column("first_response_at", sa.DateTime()))
    op.create_table("trust_incidents", sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("reporter_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("application_id", sa.Integer(), sa.ForeignKey("applications.id", ondelete="SET NULL")),
        sa.Column("category", sa.String(40), nullable=False), sa.Column("details", sa.Text(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False), sa.Column("shared_summary", sa.Text()), sa.Column("appeal", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False), sa.Column("updated_at", sa.DateTime(), nullable=False))
    op.create_index("ix_trust_incidents_reporter_user_id", "trust_incidents", ["reporter_user_id"])
    op.create_index("ix_trust_incidents_company_id", "trust_incidents", ["company_id"])
    op.create_table("model_audit_runs", sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("actor_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("version", sa.String(80), nullable=False), sa.Column("metrics", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False))


def downgrade():
    op.drop_table("model_audit_runs")
    op.drop_table("trust_incidents")
    op.drop_column("applications", "first_response_at")
