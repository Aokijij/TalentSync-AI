"""Simplify the candidate selection flow.

Revision ID: 0014_simplified_flow
Revises: 0013_profiles_company
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0014_simplified_flow"
down_revision: str | None = "0013_profiles_company"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

SIMPLIFIED_STAGES = [
    {"id": "submitted", "title": "Recibidas"},
    {"id": "reviewing", "title": "En revisión"},
    {"id": "interview", "title": "Entrevista"},
    {"id": "hired", "title": "Contratados"},
    {"id": "rejected", "title": "No seleccionados"},
]

LEGACY_STAGES = [
    {"id": "submitted", "title": "Nuevos"},
    {"id": "shortlisted", "title": "Preseleccionados"},
    {"id": "technical_interview", "title": "Entrevista técnica"},
    {"id": "psychometric_test", "title": "Prueba psicotécnica"},
    {"id": "hired", "title": "Contratados"},
    {"id": "rejected", "title": "Descartados"},
]

LEGACY_IDS = {stage["id"] for stage in LEGACY_STAGES}
SIMPLIFIED_IDS = {stage["id"] for stage in SIMPLIFIED_STAGES}


def _replace_known_job_flows(stages: list[dict] | None, replacement: list[dict]) -> bool:
    if not isinstance(stages, list) or not stages:
        return False
    ids = {str(stage.get("id", "")) for stage in stages if isinstance(stage, dict)}
    known = LEGACY_IDS | SIMPLIFIED_IDS
    return bool(ids) and ids <= known and ids != {stage["id"] for stage in replacement}


def _update_job_flows(replacement: list[dict]) -> None:
    if op.get_context().as_sql:
        return
    bind = op.get_bind()
    jobs = sa.table(
        "jobs",
        sa.column("id", sa.Integer),
        sa.column("pipeline_stages", sa.JSON),
    )
    for row in bind.execute(sa.select(jobs.c.id, jobs.c.pipeline_stages)):
        if _replace_known_job_flows(row.pipeline_stages, replacement):
            bind.execute(
                jobs.update()
                .where(jobs.c.id == row.id)
                .values(pipeline_stages=replacement)
            )


def upgrade() -> None:
    applications = sa.table(
        "applications",
        sa.column("pipeline_stage", sa.String(80)),
    )
    op.execute(
        applications.update()
        .where(applications.c.pipeline_stage == "shortlisted")
        .values(pipeline_stage="reviewing")
    )
    op.execute(
        applications.update()
        .where(
            applications.c.pipeline_stage.in_(
                ["technical_interview", "psychometric_test"]
            )
        )
        .values(pipeline_stage="interview")
    )
    _update_job_flows(SIMPLIFIED_STAGES)


def downgrade() -> None:
    applications = sa.table(
        "applications",
        sa.column("pipeline_stage", sa.String(80)),
    )
    op.execute(
        applications.update()
        .where(applications.c.pipeline_stage == "reviewing")
        .values(pipeline_stage="shortlisted")
    )
    op.execute(
        applications.update()
        .where(applications.c.pipeline_stage == "interview")
        .values(pipeline_stage="technical_interview")
    )
    _update_job_flows(LEGACY_STAGES)
