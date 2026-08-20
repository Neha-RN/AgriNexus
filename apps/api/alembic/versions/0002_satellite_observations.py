"""add satellite_observations table

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-20
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "satellite_observations",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("field_id", sa.Integer(), nullable=False),
        sa.Column("observation_date", sa.Date(), nullable=False),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("cloud_cover", sa.Numeric(5, 2), nullable=True),
        sa.Column("external_scene_id", sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(
            ["field_id"],
            ["fields.id"],
            name="fk_satellite_observations_field_id",
        ),
    )
    op.create_index(
        "ix_satellite_observations_field_id",
        "satellite_observations",
        ["field_id"],
    )
    op.create_index(
        "ix_satellite_observations_field_id_observation_date",
        "satellite_observations",
        ["field_id", "observation_date"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_satellite_observations_field_id_observation_date",
        table_name="satellite_observations",
    )
    op.drop_index(
        "ix_satellite_observations_field_id",
        table_name="satellite_observations",
    )
    op.drop_table("satellite_observations")