"""Candidate social identities and one-use OAuth browser transactions."""
from alembic import op
import sqlalchemy as sa

revision = "0031_social_identity"
down_revision = "0030_recommendation_feedback"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("social_identities", sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider", sa.String(20), nullable=False), sa.Column("subject", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("provider", "subject", name="uq_social_identity_subject"),
        sa.UniqueConstraint("user_id", "provider", name="uq_social_identity_user_provider"))
    op.create_index("ix_social_identities_user_id", "social_identities", ["user_id"])
    op.create_table("oauth_attempts", sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("provider", sa.String(20), nullable=False), sa.Column("state_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("browser_hash", sa.String(64), nullable=False), sa.Column("verifier_cipher", sa.Text(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False), sa.Column("used_at", sa.DateTime()))
    op.create_index("ix_oauth_attempts_expires_at", "oauth_attempts", ["expires_at"])


def downgrade():
    op.drop_table("oauth_attempts")
    op.drop_table("social_identities")
