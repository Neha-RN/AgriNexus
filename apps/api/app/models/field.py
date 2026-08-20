from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from geoalchemy2 import Geometry
from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.country import Country


class Field(Base):
    __tablename__ = "fields"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    country_id: Mapped[int] = mapped_column(
        ForeignKey("countries.id"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    crop_type: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
    )

    area_hectares: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 4),
        nullable=True,
    )

    geometry: Mapped[object | None] = mapped_column(
        Geometry(
            geometry_type="MULTIPOLYGON",
            srid=4326,
            spatial_index=False,
        ),
        nullable=True,
    )

    country: Mapped["Country"] = relationship(
        "Country",
        back_populates="fields",
    )

    observations: Mapped[list["SatelliteObservation"]] = relationship(
    "SatelliteObservation",
    back_populates="field",
    cascade="all, delete-orphan",
    )