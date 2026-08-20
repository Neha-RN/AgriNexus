from sqlalchemy.orm import Session

from app.models.satellite_observation import SatelliteObservation


def list_observations_for_field(
    db: Session, field_id: int
) -> list[SatelliteObservation]:
    return (
        db.query(SatelliteObservation)
        .filter(SatelliteObservation.field_id == field_id)
        .order_by(SatelliteObservation.observation_date.desc())
        .all()
    )