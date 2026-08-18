from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class FieldRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    country_id: int
    name: str
    crop_type: str | None = None
    area_hectares: Decimal | None = None