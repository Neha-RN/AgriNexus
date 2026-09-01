from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from geoalchemy2.shape import to_shape
from shapely.geometry import mapping
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.satellite_observation import SatelliteObservation
from app.schemas.field import FieldRead
from app.schemas.satellite_metric import SatelliteMetricRead
from app.schemas.satellite_observation import SatelliteObservationRead
from app.services import (
    field_service,
    satellite_observation_service,
)
from app.services.cdse_client import (
    CDSEClient,
    CDSEClientError,
)
from app.services.cdse_processing_client import (
    CDSEProcessingClient,
)
from app.services.field_geometry_service import (
    get_field_geometry_geojson,
)
from app.services.ndvi_service import (
    calculate_mean_ndvi,
)
from app.services.satellite_metric_service import (
    create_or_update_metric,
    list_metrics_for_observation,
)


router = APIRouter(
    prefix="/fields",
    tags=["fields"],
)


DEFAULT_LOOKBACK_DAYS = 90
DEFAULT_MAX_CLOUD_COVER = 30.0

SENTINEL_2_L2A_SOURCE = "sentinel-2-l2a"


NDVI_EVALSCRIPT = """
//VERSION=3

function setup() {
    return {
        input: ["B04", "B08"],
        output: {
            bands: 2,
            sampleType: "FLOAT32"
        }
    };
}

function evaluatePixel(sample) {
    return [
        sample.B04,
        sample.B08
    ];
}
"""


@router.get(
    "",
    response_model=list[FieldRead],
)
def get_fields(
    db: Session = Depends(get_db),
) -> list[FieldRead]:
    """
    Return all fields.
    """
    return field_service.list_fields(db)


@router.get(
    "/{field_id}/observations",
    response_model=list[SatelliteObservationRead],
)
def get_field_observations(
    field_id: int,
    db: Session = Depends(get_db),
) -> list[SatelliteObservationRead]:
    """
    Return satellite observations already stored in the database.

    This endpoint never calls CDSE.
    """

    field = field_service.get_field(
        db,
        field_id,
    )

    if field is None:
        raise HTTPException(
            status_code=404,
            detail="Field not found",
        )

    return (
        satellite_observation_service
        .list_observations_for_field(
            db,
            field_id,
        )
    )


@router.post(
    "/{field_id}/observations/sync",
    response_model=list[SatelliteObservationRead],
)
def sync_field_observations(
    field_id: int,
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    max_cloud_cover: float = Query(
        default=DEFAULT_MAX_CLOUD_COVER,
    ),
    db: Session = Depends(get_db),
) -> list[SatelliteObservationRead]:
    """
    Search the CDSE Sentinel-2 L2A catalog for the field geometry.

    Newly discovered scenes are persisted as SatelliteObservation
    records. Existing scenes are not duplicated.
    """

    field = field_service.get_field(
        db,
        field_id,
    )

    if field is None:
        raise HTTPException(
            status_code=404,
            detail="Field not found",
        )

    if field.geometry is None:
        raise HTTPException(
            status_code=422,
            detail="Field has no geometry to search with",
        )

    resolved_end_date = end_date or date.today()

    resolved_start_date = (
        start_date
        or resolved_end_date
        - timedelta(days=DEFAULT_LOOKBACK_DAYS)
    )

    if resolved_start_date > resolved_end_date:
        raise HTTPException(
            status_code=422,
            detail="start_date cannot be after end_date",
        )

    geometry = mapping(
        to_shape(field.geometry)
    )

    client = CDSEClient()

    try:
        scenes = client.search_scenes(
            geometry=geometry,
            start_date=resolved_start_date,
            end_date=resolved_end_date,
            max_cloud_cover=max_cloud_cover,
        )

    except CDSEClientError as exc:
        raise HTTPException(
            status_code=502,
            detail=str(exc),
        ) from None

    return (
        satellite_observation_service
        .sync_observations_from_scenes(
            db,
            field_id=field_id,
            source=SENTINEL_2_L2A_SOURCE,
            scenes=scenes,
        )
    )


@router.get(
    "/{field_id}/observations/{observation_id}/metrics",
    response_model=list[SatelliteMetricRead],
)
def get_observation_metrics(
    field_id: int,
    observation_id: int,
    db: Session = Depends(get_db),
) -> list[SatelliteMetricRead]:
    """
    Return all previously calculated metrics for a satellite observation.

    This endpoint only reads from PostgreSQL.
    It does not contact CDSE or recalculate NDVI.
    """

    field = field_service.get_field(
        db,
        field_id,
    )

    if field is None:
        raise HTTPException(
            status_code=404,
            detail="Field not found",
        )

    observation = (
        db.query(SatelliteObservation)
        .filter(
            SatelliteObservation.id == observation_id,
            SatelliteObservation.field_id == field_id,
        )
        .first()
    )

    if observation is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "Satellite observation not found "
                "for this field"
            ),
        )

    return list_metrics_for_observation(
        db=db,
        observation_id=observation_id,
    )


@router.post(
    "/{field_id}/observations/{observation_id}/metrics/ndvi",
)
def calculate_observation_ndvi(
    field_id: int,
    observation_id: int,
    db: Session = Depends(get_db),
) -> dict:
    """
    Calculate the mean NDVI for a specific satellite observation.

    Pipeline:

    1. Validate the field.
    2. Validate the satellite observation.
    3. Retrieve the field geometry.
    4. Request Sentinel-2 B04 and B08 data from CDSE.
    5. Calculate mean NDVI.
    6. Create or update the NDVI_MEAN metric.
    """

    field = field_service.get_field(
        db,
        field_id,
    )

    if field is None:
        raise HTTPException(
            status_code=404,
            detail="Field not found",
        )

    observation = (
        db.query(SatelliteObservation)
        .filter(
            SatelliteObservation.id == observation_id,
            SatelliteObservation.field_id == field_id,
        )
        .first()
    )

    if observation is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "Satellite observation not found "
                "for this field"
            ),
        )

    try:
        geometry = get_field_geometry_geojson(
            db=db,
            field_id=field_id,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from None

    processing_client = CDSEProcessingClient()

    try:
        processing_result = (
            processing_client.process_sentinel2(
                geometry=geometry,
                start_date=observation.observation_date,
                end_date=observation.observation_date,
                evalscript=NDVI_EVALSCRIPT,
            )
        )

        mean_ndvi = calculate_mean_ndvi(
            processing_result.content
        )

    except CDSEClientError as exc:
        raise HTTPException(
            status_code=502,
            detail=str(exc),
        ) from None

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to calculate NDVI: "
                f"{str(exc)}"
            ),
        ) from None

    metric = create_or_update_metric(
        db=db,
        observation_id=observation_id,
        metric_type="NDVI_MEAN",
        value=mean_ndvi,
    )

    return {
        "field_id": field_id,
        "observation_id": observation_id,
        "metric_type": metric.metric_type,
        "value": (
            float(metric.value)
            if metric.value is not None
            else None
        ),
        "calculated_at": metric.calculated_at,
    }