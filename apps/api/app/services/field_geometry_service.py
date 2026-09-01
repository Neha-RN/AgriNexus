from __future__ import annotations

import json
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.field import Field


def get_field_geometry_geojson(
    db: Session,
    field_id: int,
) -> dict[str, Any]:
    """
    Return a field's PostGIS geometry as a GeoJSON dictionary.

    The geometry is stored with SRID 4326, so its coordinates are already
    longitude/latitude and suitable for CDSE requests.
    """
    geometry_json = (
        db.query(
            func.ST_AsGeoJSON(Field.geometry)
        )
        .filter(Field.id == field_id)
        .scalar()
    )

    if geometry_json is None:
        raise ValueError(
            f"Field {field_id} does not exist or has no geometry"
        )

    return json.loads(geometry_json)