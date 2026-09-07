"""Add department to candidate profiles and jobs.

Revision ID: 0012_colombian_departments
Revises: 0011_profile_preferred_sector
"""

from alembic import op
import sqlalchemy as sa


revision = "0012_colombian_departments"
down_revision = "0011_profile_preferred_sector"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("profiles", sa.Column("department", sa.String(length=120), nullable=True))
    op.add_column("jobs", sa.Column("department", sa.String(length=120), nullable=True))
    for table in ("profiles", "jobs"):
        op.execute(f"""
            UPDATE {table}
            SET department = CASE
                WHEN location IN ('Medellín', 'Medellin', 'Envigado', 'Bello', 'Itagüí', 'Rionegro', 'Apartadó', 'Sabaneta') THEN 'Antioquia'
                WHEN location IN ('Bogotá', 'Bogota') THEN 'Bogotá D.C.'
                WHEN location IN ('Cali', 'Palmira', 'Buenaventura', 'Buga', 'Cartago', 'Tuluá', 'Jamundí') THEN 'Valle del Cauca'
                WHEN location IN ('Barranquilla', 'Soledad', 'Puerto Colombia') THEN 'Atlántico'
                WHEN location IN ('Bucaramanga', 'Floridablanca', 'Girón', 'Piedecuesta', 'Barrancabermeja') THEN 'Santander'
                ELSE department
            END
        """)


def downgrade() -> None:
    op.drop_column("jobs", "department")
    op.drop_column("profiles", "department")
