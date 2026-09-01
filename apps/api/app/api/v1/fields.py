from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from geoalchemy2.shape import to_shape
from shapely.geometry import mapping
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.field import FieldRead
from app.schemas.satellite_observation import SatelliteObservationRead
from app.services import field_service, satellite_observation_service
from app.services.cdse_client import CDSEClient, CDSEClientError

router = APIRouter(prefix="/fields", tags=["fields"])

DEFAULT_LOOKBACK_DAYS = 90
DEFAULT_MAX_CLOUD_COVER = 30.0
SENTINEL_2_L2A_SOURCE = "sentinel-2-l2a"


@router.get("", response_model=list[FieldRead])
def get_fields(db: Session = Depends(get_db)) -> list[FieldRead]:
    return field_service.list_fields(db)


@router.get(
    "/{field_id}/observations", response_model=list[SatelliteObservationRead]
)
def get_field_observations(
    field_id: int, db: Session = Depends(get_db)
) -> list[SatelliteObservationRead]:
    """Database read only — never calls CDSE."""
    field = field_service.get_field(db, field_id)
    if field is None:
        raise HTTPException(status_code=404, detail="Field not found")

    return satellite_observation_service.list_observations_for_field(
        db, field_id
    )


@router.post(
    "/{field_id}/observations/sync",
    response_model=list[SatelliteObservationRead],
)
def sync_field_observations(
    field_id: int,
    start_date: Optional[date] = Query(default=None),
    end_date: Optional[date] = Query(default=None),
    max_cloud_cover: float = Query(default=DEFAULT_MAX_CLOUD_COVER),
    db: Session = Depends(get_db),
) -> list[SatelliteObservationRead]:
    """
    Searches CDSE Sentinel-2 L2A catalog for the field's geometry and
    persists any newly discovered scenes as SatelliteObservation rows.
    """
    field = field_service.get_field(db, field_id)
    if field is None:
        raise HTTPException(status_code=404, detail="Field not found")

    if field.geometry is None:
        raise HTTPException(
            status_code=422, detail="Field has no geometry to search with"
        )

    resolved_end_date = end_date or date.today()
    resolved_start_date = start_date or (
        resolved_end_date - timedelta(days=DEFAULT_LOOKBACK_DAYS)
    )

    geometry = mapping(to_shape(field.geometry))

    client = CDSEClient()
    try:
        scenes = client.search_scenes(
            geometry=geometry,
            start_date=resolved_start_date,
            end_date=resolved_end_date,
            max_cloud_cover=max_cloud_cover,
        )
    except CDSEClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from None

    return satellite_observation_service.sync_observations_from_scenes(
        db, field_id=field_id, source=SENTINEL_2_L2A_SOURCE, scenes=scenes
    )