from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import Date, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class SatelliteObservation(Base):
    """
    Minimal, provider-independent record of a satellite pass over a field.
    No imagery, no NDVI, no provider-specific fields — those come later
    once a specific provider is integrated.
    """

    __tablename__ = "satellite_observations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    field_id: Mapped[int] = mapped_column(
        ForeignKey("fields.id"), nullable=False, index=True
    )
    observation_date: Mapped[date] = mapped_column(Date, nullable=False)
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    cloud_cover: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 2), nullable=True
    )
    external_scene_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )

    field: Mapped["Field"] = relationship(
        "Field", back_populates="observations"
    )