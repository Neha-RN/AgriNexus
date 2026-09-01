from datetime import date
from typing import Optional

from sqlalchemy.orm import Session

from app.models.satellite_observation import SatelliteObservation
from app.services.cdse_client import CDSEScene


def list_observations_for_field(
    db: Session, field_id: int
) -> list[SatelliteObservation]:
    return (
        db.query(SatelliteObservation)
        .filter(SatelliteObservation.field_id == field_id)
        .order_by(SatelliteObservation.observation_date.desc())
        .all()
    )


def get_observation_by_external_id(
    db: Session, field_id: int, source: str, external_scene_id: str
) -> Optional[SatelliteObservation]:
    return (
        db.query(SatelliteObservation)
        .filter(
            SatelliteObservation.field_id == field_id,
            SatelliteObservation.source == source,
            SatelliteObservation.external_scene_id == external_scene_id,
        )
        .first()
    )


def create_observation(
    db: Session,
    field_id: int,
    source: str,
    observation_date: date,
    cloud_cover: Optional[float],
    external_scene_id: str,
) -> SatelliteObservation:
    observation = SatelliteObservation(
        field_id=field_id,
        source=source,
        observation_date=observation_date,
        cloud_cover=cloud_cover,
        external_scene_id=external_scene_id,
    )
    db.add(observation)
    db.commit()
    db.refresh(observation)
    return observation


def sync_observations_from_scenes(
    db: Session,
    field_id: int,
    source: str,
    scenes: list[CDSEScene],
) -> list[SatelliteObservation]:
    """
    Converts CDSE scenes into SatelliteObservation rows, skipping any scene
    that already has a matching (field_id, source, external_scene_id) row.
    Returns the full set of resulting observations (existing + newly created).
    """
    results: list[SatelliteObservation] = []

    for scene in scenes:
        existing = get_observation_by_external_id(
            db, field_id, source, scene.external_scene_id
        )
        if existing is not None:
            results.append(existing)
            continue

        created = create_observation(
            db,
            field_id=field_id,
            source=source,
            observation_date=scene.observation_date,
            cloud_cover=scene.cloud_cover,
            external_scene_id=scene.external_scene_id,
        )
        results.append(created)

    return results