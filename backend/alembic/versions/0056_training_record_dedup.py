"""Reconcile repeated training records without removing learning history."""
import re
import unicodedata
from urllib.parse import urlsplit, urlunsplit

import sqlalchemy as sa
from alembic import context, op

revision = "0056_training_record_dedup"
down_revision = "0055_external_job_content"
branch_labels = depends_on = None


def _text(value):
    value = unicodedata.normalize("NFKD", str(value or "")).casefold()
    return re.sub(r"[^a-z0-9]+", " ", "".join(c for c in value if not unicodedata.combining(c))).strip()


def _keys(row):
    keys = set()
    if row.get("resource_id"):
        keys.add(("resource", str(row["resource_id"])))
    if row.get("url"):
        value = urlsplit(str(row["url"]))
        keys.add(("url", urlunsplit((value.scheme.lower(), value.netloc.lower(), value.path.rstrip("/"), value.query, ""))))
    name, issuer = _text(row.get("name") or row.get("title")), _text(row.get("issuer") or row.get("provider"))
    if name and issuer:
        keys.add(("title", name, issuer, str(row.get("year") or "")))
    return keys


def _unique(rows):
    output, identities = [], []
    for raw in rows or []:
        row = dict(raw)
        if row.get("source") == "external_certificate":
            row["kind"] = "certificate"
        keys = _keys(row)
        index = next((i for i, known in enumerate(identities) if keys & known), None)
        if index is None:
            output.append(row)
            identities.append(keys)
        else:
            previous_id = output[index].get("id")
            output[index].update({key: value for key, value in row.items() if value not in (None, "", [], {})})
            if previous_id:
                output[index]["id"] = previous_id
            identities[index] |= keys
    return output


def upgrade():
    if context.is_offline_mode():
        op.execute("-- Training JSON reconciliation requires an online alembic upgrade.")
        return
    profiles = sa.table("profiles", sa.column("id", sa.Integer()), sa.column("certifications", sa.JSON()), sa.column("evidence", sa.JSON()))
    connection = op.get_bind()
    for row in connection.execute(sa.select(profiles)).mappings().all():
        certificates = _unique(row["certifications"])
        ordinary = [item for item in row["evidence"] or [] if item.get("kind") not in {"certificate", "training"}]
        training = _unique([item for item in row["evidence"] or [] if item.get("kind") in {"certificate", "training"}])
        evidence = ordinary + training
        if certificates != row["certifications"] or evidence != row["evidence"]:
            connection.execute(profiles.update().where(profiles.c.id == row["id"]).values(certifications=certificates, evidence=evidence))


def downgrade():
    # Removed duplicates are deliberately not reconstructed. The deployment
    # keeps an external database backup for an exact historical restoration.
    pass
