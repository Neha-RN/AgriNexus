from decimal import Decimal
from typing import Any, Optional

from geoalchemy2.shape import to_shape
from pydantic import BaseModel, ConfigDict, field_validator
from shapely.geometry import mapping


class FieldRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    country_id: int
    name: str
    crop_type: Optional[str] = None
    area_hectares: Optional[Decimal] = None
    geometry: Optional[dict[str, Any]] = None

    @field_validator("geometry", mode="before")
    @classmethod
    def _geometry_to_geojson(cls, value: Any) -> Optional[dict[str, Any]]:
        if value is None:
            return None
        if isinstance(value, dict):
            return value
        shape = to_shape(value)
        return mapping(shape)