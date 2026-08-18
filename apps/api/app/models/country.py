from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.field import Field


class Country(Base):
    __tablename__ = "countries"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    code: Mapped[str] = mapped_column(
        String(8),
        nullable=False,
        unique=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        unique=True,
    )

    fields: Mapped[list["Field"]] = relationship(
        "Field",
        back_populates="country",
        cascade="all, delete-orphan",
    )