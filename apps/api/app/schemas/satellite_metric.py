from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict


class SatelliteMetricRead(BaseModel):
    """
    API response schema for a derived satellite metric.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    observation_id: int
    metric_type: str
    value: Optional[Decimal] = None
    calculated_at: datetime