"""Record explicit registration consent; never fabricate acceptance for old users."""
import sqlalchemy as sa

from alembic import op

revision = "0053_registration_consent"
down_revision = "0052_social_registration"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("legal_acceptance", sa.JSON(), server_default="{}", nullable=False))


def downgrade():
    with op.batch_alter_table("users") as batch:
        batch.drop_column("legal_acceptance")
