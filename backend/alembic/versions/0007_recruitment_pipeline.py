"""expand recruitment pipeline statuses

Revision ID: 0007_recruitment_pipeline
Revises: 0006_notifications
Create Date: 2026-09-02
"""

from alembic import op

revision = "0007_recruitment_pipeline"
down_revision = "0006_notifications"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # SQLAlchemy stores enum member names in PostgreSQL. SQLite keeps this
    # column as text and therefore needs no schema alteration.
    if op.get_bind().dialect.name == "postgresql":
        for value in ("SEEN", "SHORTLISTED", "TECHNICAL_INTERVIEW", "PSYCHOMETRIC_TEST", "HIRED"):
            op.execute(f"ALTER TYPE applicationstatus ADD VALUE IF NOT EXISTS '{value}'")


def downgrade() -> None:
    # PostgreSQL enum values cannot be removed safely while rows may use them.
    pass
