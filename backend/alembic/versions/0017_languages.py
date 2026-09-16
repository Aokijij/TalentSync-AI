"""Store candidate language levels and vacancy language requirements."""
import re
import unicodedata

import sqlalchemy as sa
from alembic import context, op

revision = "0017_languages"
down_revision = "0016_resume_colors"
branch_labels = None
depends_on = None


def upgrade():
    for table in ("profiles", "jobs"):
        op.add_column(table, sa.Column("languages", sa.JSON(), nullable=False, server_default="[]"))
    if context.is_offline_mode():
        return
    # Preserve explicit levels already written in older vacancy requirements.
    jobs = sa.table("jobs", sa.column("id", sa.Integer), sa.column("requirements", sa.Text), sa.column("languages", sa.JSON))
    connection = op.get_bind()
    for job in connection.execute(sa.select(jobs.c.id, jobs.c.requirements)):
        text = "".join(c for c in unicodedata.normalize("NFKD", job.requirements.lower()) if not unicodedata.combining(c))
        languages = []
        for aliases, name in [("ingles|english", "inglés"), ("frances|french", "francés"), ("portugues|portuguese", "portugués"), ("aleman|german", "alemán"), ("espanol|spanish", "español")]:
            match = re.search(rf"\b(?:{aliases})\b[^.\n]{{0,45}}?\b([abc][12])\b", text)
            if match:
                languages.append({"name": name, "level": match.group(1).upper()})
        if languages:
            connection.execute(jobs.update().where(jobs.c.id == job.id).values(languages=languages))


def downgrade():
    for table in ("jobs", "profiles"):
        op.drop_column(table, "languages")
