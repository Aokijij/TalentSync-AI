"""Align historical nullable collections and SQLite recruitment statuses."""
from alembic import op
import sqlalchemy as sa

revision = "0047_schema_alignment"
down_revision = "0046_account_erasure"
branch_labels = None
depends_on = None

COLLECTIONS = {
    "jobs": ("benefits", "skills"),
    "profiles": ("skills", "experiences", "educations", "certifications"),
    "recommendations": ("reasons",),
}


def upgrade():
    for table, columns in COLLECTIONS.items():
        for column in columns:
            # Older imports can contain SQL NULL or the JSON literal null.
            op.execute(sa.text(f"UPDATE {table} SET {column} = '[]' WHERE {column} IS NULL OR CAST({column} AS TEXT) = 'null'"))
        if table == "profiles":
            op.execute(sa.text("UPDATE profiles SET updated_at = COALESCE((SELECT created_at FROM users WHERE users.id = profiles.user_id), CURRENT_TIMESTAMP) WHERE updated_at IS NULL"))
        with op.batch_alter_table(table) as batch:
            for column in columns:
                batch.alter_column(column, existing_type=sa.JSON(), nullable=False)
            if table == "profiles":
                batch.alter_column("updated_at", existing_type=sa.DateTime(), nullable=False)
    # PostgreSQL already has the complete native enum since migration 0007.
    if op.get_bind().dialect.name == "sqlite":
        with op.batch_alter_table("applications") as batch:
            batch.alter_column("status", existing_type=sa.String(9), type_=sa.String(19), existing_nullable=False)


def downgrade():
    for table, columns in COLLECTIONS.items():
        with op.batch_alter_table(table) as batch:
            for column in columns:
                batch.alter_column(column, existing_type=sa.JSON(), nullable=True)
            if table == "profiles":
                batch.alter_column("updated_at", existing_type=sa.DateTime(), nullable=True)
    if op.get_bind().dialect.name == "sqlite":
        with op.batch_alter_table("applications") as batch:
            batch.alter_column("status", existing_type=sa.String(19), type_=sa.String(9), existing_nullable=False)
