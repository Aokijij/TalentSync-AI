"""Bind social account linking to a reauthenticated browser session."""
from alembic import op
import sqlalchemy as sa

revision = "0032_social_linking"
down_revision = "0031_social_identity"
branch_labels = None
depends_on = None


def upgrade():
    # SQLite requires table recreation to add foreign key constraints.
    with op.batch_alter_table("oauth_attempts") as batch:
        batch.add_column(sa.Column("purpose", sa.String(10), server_default="login", nullable=False))
        batch.add_column(sa.Column("link_user_id", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("link_session_id", sa.Integer(), nullable=True))
        batch.create_foreign_key("fk_oauth_link_user", "users", ["link_user_id"], ["id"], ondelete="CASCADE")
        batch.create_foreign_key("fk_oauth_link_session", "user_sessions", ["link_session_id"], ["id"], ondelete="CASCADE")
        batch.create_index("ix_oauth_attempts_link_user_id", ["link_user_id"])
        batch.create_index("ix_oauth_attempts_link_session_id", ["link_session_id"])


def downgrade():
    with op.batch_alter_table("oauth_attempts") as batch:
        batch.drop_index("ix_oauth_attempts_link_session_id")
        batch.drop_index("ix_oauth_attempts_link_user_id")
        batch.drop_constraint("fk_oauth_link_session", type_="foreignkey")
        batch.drop_constraint("fk_oauth_link_user", type_="foreignkey")
        batch.drop_column("link_session_id")
        batch.drop_column("link_user_id")
        batch.drop_column("purpose")
