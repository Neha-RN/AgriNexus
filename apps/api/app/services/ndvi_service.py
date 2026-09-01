from __future__ import annotations

from io import BytesIO

import numpy as np
import rasterio
from sqlalchemy.orm import Session

from app.models.satellite_observation import SatelliteObservation
from app.services.cdse_client import CDSEClientError
from app.services.cdse_processing_client import CDSEProcessingClient
from app.services.field_geometry_service import get_field_geometry_geojson
from app.services.satellite_metric_service import create_or_update_metric

NDVI_METRIC_TYPE = "NDVI_MEAN"

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


def calculate_mean_ndvi(geotiff_bytes: bytes) -> float | None:
    """
    Calculate mean NDVI from a two-band GeoTIFF.

    Band 1: Sentinel-2 B04 (Red)
    Band 2: Sentinel-2 B08 (Near Infrared)
    """

    with rasterio.open(BytesIO(geotiff_bytes)) as dataset:
        if dataset.count < 2:
            raise ValueError(
                "NDVI input GeoTIFF must contain B04 and B08 bands"
            )

        red = dataset.read(1).astype(np.float32)
        nir = dataset.read(2).astype(np.float32)

        denominator = nir + red

        valid_mask = (
            np.isfinite(red)
            & np.isfinite(nir)
            & (denominator != 0)
        )

        if not np.any(valid_mask):
            return None

        ndvi = np.full(
            red.shape,
            np.nan,
            dtype=np.float32,
        )

        ndvi[valid_mask] = (
            (nir[valid_mask] - red[valid_mask])
            / denominator[valid_mask]
        )

        valid_ndvi = ndvi[np.isfinite(ndvi)]

        if valid_ndvi.size == 0:
            return None

        return float(np.mean(valid_ndvi))


def calculate_and_store_ndvi(
    db: Session,
    observation: SatelliteObservation,
):
    """
    Request Sentinel-2 B04 and B08 data for the observation date,
    calculate mean NDVI, and store or update the NDVI metric.
    """

    geometry = get_field_geometry_geojson(
        db=db,
        field_id=observation.field_id,
    )

    processing_client = CDSEProcessingClient()

    try:
        result = processing_client.process_sentinel2(
            geometry=geometry,
            start_date=observation.observation_date,
            end_date=observation.observation_date,
            evalscript=NDVI_EVALSCRIPT,
        )
    except CDSEClientError:
        raise

    mean_ndvi = calculate_mean_ndvi(result.content)

    return create_or_update_metric(
        db=db,
        observation_id=observation.id,
        metric_type=NDVI_METRIC_TYPE,
        value=mean_ndvi,
    )