"""Local interview documents and ephemeral browser signaling."""
from alembic import op
import sqlalchemy as sa

revision = "0029_interview_rooms"
down_revision = "0028_ecosystem_health"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("interview_rooms", sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("application_id", sa.Integer(), sa.ForeignKey("applications.id", ondelete="CASCADE"), unique=True, nullable=False),
        sa.Column("creator_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("title", sa.String(150), nullable=False), sa.Column("code", sa.Text(), nullable=False),
        sa.Column("whiteboard", sa.JSON(), nullable=False), sa.Column("closed", sa.Boolean(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False), sa.Column("created_at", sa.DateTime(), nullable=False), sa.Column("updated_at", sa.DateTime(), nullable=False))
    op.create_table("interview_participants", sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("room_id", sa.String(32), sa.ForeignKey("interview_rooms.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("slot", sa.Integer(), nullable=False), sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("room_id", "slot", name="uq_interview_participant_slot"))
    op.create_index("ix_interview_participants_room_id", "interview_participants", ["room_id"])
    op.create_table("interview_signals", sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("room_id", sa.String(32), sa.ForeignKey("interview_rooms.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sender_id", sa.String(32), nullable=False), sa.Column("recipient_id", sa.String(32), nullable=False),
        sa.Column("kind", sa.String(10), nullable=False), sa.Column("payload", sa.JSON(), nullable=False), sa.Column("expires_at", sa.DateTime(), nullable=False))
    op.create_index("ix_interview_signals_room_id", "interview_signals", ["room_id"])


def downgrade():
    op.drop_table("interview_signals")
    op.drop_table("interview_participants")
    op.drop_table("interview_rooms")
