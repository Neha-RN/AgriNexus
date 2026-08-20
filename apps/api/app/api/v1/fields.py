from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.field import FieldRead
from app.schemas.satellite_observation import SatelliteObservationRead
from app.services import field_service, satellite_observation_service

router = APIRouter(prefix="/fields", tags=["fields"])


@router.get("", response_model=list[FieldRead])
def get_fields(db: Session = Depends(get_db)) -> list[FieldRead]:
    return field_service.list_fields(db)


@router.get(
    "/{field_id}/observations", response_model=list[SatelliteObservationRead]
)
def get_field_observations(
    field_id: int, db: Session = Depends(get_db)
) -> list[SatelliteObservationRead]:
    field = field_service.get_field(db, field_id)
    if field is None:
        raise HTTPException(status_code=404, detail="Field not found")

    return satellite_observation_service.list_observations_for_field(
        db, field_id
    )