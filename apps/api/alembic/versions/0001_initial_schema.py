"""Initial AgriNexus schema.

Revision ID: 0001
Revises:
"""

from __future__ import annotations

import geoalchemy2
import sqlalchemy as sa
from alembic import op


revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable PostGIS before creating spatial columns.
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    op.create_table(
        "countries",
        sa.Column(
            "id",
            sa.Integer(),
            primary_key=True,
            autoincrement=True,
        ),
        sa.Column(
            "code",
            sa.String(length=8),
            nullable=False,
        ),
        sa.Column(
            "name",
            sa.String(length=128),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "code",
            name="uq_countries_code",
        ),
        sa.UniqueConstraint(
            "name",
            name="uq_countries_name",
        ),
    )

    op.create_index(
        "ix_countries_code",
        "countries",
        ["code"],
        unique=False,
    )

    op.create_table(
        "fields",
        sa.Column(
            "id",
            sa.Integer(),
            primary_key=True,
            autoincrement=True,
        ),
        sa.Column(
            "country_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "name",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "crop_type",
            sa.String(length=128),
            nullable=True,
        ),
        sa.Column(
            "area_hectares",
            sa.Numeric(12, 4),
            nullable=True,
        ),
        sa.Column(
            "geometry",
            geoalchemy2.types.Geometry(
                geometry_type="MULTIPOLYGON",
                srid=4326,
                spatial_index=False,
            ),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["country_id"],
            ["countries.id"],
            name="fk_fields_country_id",
        ),
    )

    op.create_index(
        "ix_fields_country_id",
        "fields",
        ["country_id"],
    )

    op.create_index(
        "idx_fields_geometry",
        "fields",
        ["geometry"],
        postgresql_using="gist",
    )


def downgrade() -> None:
    op.drop_index(
        "idx_fields_geometry",
        table_name="fields",
    )

    op.drop_index(
        "ix_fields_country_id",
        table_name="fields",
    )

    op.drop_table("fields")

    op.drop_index(
        "ix_countries_code",
        table_name="countries",
    )

    op.drop_constraint(
        "uq_countries_name",
        "countries",
        type_="unique",
    )

    op.drop_constraint(
        "uq_countries_code",
        "countries",
        type_="unique",
    )

    op.drop_table("countries")