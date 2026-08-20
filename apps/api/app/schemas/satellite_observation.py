from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict


class SatelliteObservationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    field_id: int
    observation_date: date
    source: str
    cloud_cover: Optional[Decimal] = None
    external_scene_id: Optional[str] = None