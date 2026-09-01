"""add satellite metrics

Revision ID: 250c998a0b06
Revises: 0002
Create Date: 2026-09-01 16:32:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "250c998a0b06"
down_revision: Union[str, Sequence[str], None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the satellite_metrics table."""

    op.create_table(
        "satellite_metrics",
        sa.Column(
            "id",
            sa.Integer(),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column(
            "observation_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "metric_type",
            sa.String(length=32),
            nullable=False,
        ),
        sa.Column(
            "value",
            sa.Numeric(precision=8, scale=5),
            nullable=True,
        ),
        sa.Column(
            "calculated_at",
            sa.DateTime(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["observation_id"],
            ["satellite_observations.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "observation_id",
            "metric_type",
            name="uq_satellite_metric_observation_type",
        ),
    )

    op.create_index(
        "ix_satellite_metrics_observation_id",
        "satellite_metrics",
        ["observation_id"],
        unique=False,
    )


def downgrade() -> None:
    """Remove the satellite_metrics table."""

    op.drop_index(
        "ix_satellite_metrics_observation_id",
        table_name="satellite_metrics",
    )

    op.drop_table("satellite_metrics")