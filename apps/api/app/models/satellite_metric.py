from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class SatelliteMetric(Base):
    """
    A derived metric calculated from a satellite observation.

    Examples:
    - NDVI
    - NDWI
    - EVI

    The original satellite scene remains stored separately in
    SatelliteObservation.
    """

    __tablename__ = "satellite_metrics"

    __table_args__ = (
        UniqueConstraint(
            "observation_id",
            "metric_type",
            name="uq_satellite_metric_observation_type",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    observation_id: Mapped[int] = mapped_column(
        ForeignKey(
            "satellite_observations.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    metric_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )

    value: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(8, 5),
        nullable=True,
    )

    calculated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    observation: Mapped["SatelliteObservation"] = relationship(
        "SatelliteObservation",
        back_populates="metrics",
    )