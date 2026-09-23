"""Add optional screening questions and private application adjustments."""

import sqlalchemy as sa
from alembic import op

revision = "0018_screening_questions"
down_revision = "0017_languages"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "jobs",
        sa.Column("application_questions", sa.JSON(), nullable=False, server_default="[]"),
    )
    op.add_column(
        "applications",
        sa.Column("screening_answers", sa.JSON(), nullable=False, server_default="[]"),
    )
    op.add_column(
        "applications",
        sa.Column("screening_adjustment", sa.Float(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("applications", "screening_adjustment")
    op.drop_column("applications", "screening_answers")
    op.drop_column("jobs", "application_questions")
