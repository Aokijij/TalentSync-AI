"""Index the actual company ranking and vacancy selector access paths."""
from alembic import op

revision = "0042_loading_indexes"
down_revision = "0041_career_coach"
branch_labels = None
depends_on = None

INDEXES = [
    ("ix_jobs_company_status_created", "jobs", ["company_id", "status", "created_at"]),
    ("ix_applications_job_status", "applications", ["job_id", "status"]),
    ("ix_recommendations_job_user", "recommendations", ["job_id", "user_id"]),
    ("ix_attempts_user_passed_valid", "assessment_attempts", ["user_id", "passed", "valid_until"]),
    ("ix_notifications_action_type_read_user", "notifications", ["action_url", "type", "is_read", "user_id"]),
]


def upgrade():
    for name, table, columns in INDEXES:
        op.create_index(name, table, columns)


def downgrade():
    for name, table, _ in reversed(INDEXES):
        op.drop_index(name, table_name=table)
