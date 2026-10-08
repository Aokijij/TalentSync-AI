"""Company verification and scoped team membership."""
from alembic import op
import sqlalchemy as sa

revision = "0023_organization_access"
down_revision = "0022_account_security"
branch_labels = None
depends_on = None


def upgrade():
    for column in [
        sa.Column("verification_required", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("verification_status", sa.String(30), nullable=False, server_default="pending"),
        sa.Column("verification_submission", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("verification_feedback", sa.Text()),
    ]:
        op.add_column("companies", column)
    op.create_table("company_members",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False),
        sa.Column("role", sa.String(30), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("assigned_job_ids", sa.JSON(), nullable=False),
    )
    op.create_table("company_invitations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("role", sa.String(30), nullable=False),
        sa.Column("token_hash", sa.String(64), unique=True, nullable=False),
        sa.Column("assigned_job_ids", sa.JSON(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("used_at", sa.DateTime()),
    )


def downgrade():
    op.drop_table("company_invitations")
    op.drop_table("company_members")
    for column in ("verification_feedback", "verification_submission", "verification_status", "verification_required"):
        op.drop_column("companies", column)
