from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from app.models.satellite_metric import SatelliteMetric


def list_metrics_for_observation(
    db: Session,
    observation_id: int,
) -> list[SatelliteMetric]:
    """
    Return all calculated metrics for a satellite observation.
    """
    return (
        db.query(SatelliteMetric)
        .filter(
            SatelliteMetric.observation_id == observation_id
        )
        .order_by(SatelliteMetric.metric_type.asc())
        .all()
    )


def get_metric(
    db: Session,
    observation_id: int,
    metric_type: str,
) -> Optional[SatelliteMetric]:
    """
    Return a specific metric for an observation.
    """
    return (
        db.query(SatelliteMetric)
        .filter(
            SatelliteMetric.observation_id == observation_id,
            SatelliteMetric.metric_type == metric_type,
        )
        .first()
    )


def create_or_update_metric(
    db: Session,
    observation_id: int,
    metric_type: str,
    value: Optional[float],
) -> SatelliteMetric:
    """
    Create a metric if it does not exist.

    If the same observation already has this metric type,
    update the existing value instead of creating a duplicate.
    """
    existing_metric = get_metric(
        db=db,
        observation_id=observation_id,
        metric_type=metric_type,
    )

    if existing_metric is not None:
        existing_metric.value = (
            Decimal(str(value))
            if value is not None
            else None
        )
        existing_metric.calculated_at = datetime.utcnow()

        db.commit()
        db.refresh(existing_metric)

        return existing_metric

    metric = SatelliteMetric(
        observation_id=observation_id,
        metric_type=metric_type,
        value=Decimal(str(value)) if value is not None else None,
        calculated_at=datetime.utcnow(),
    )

    db.add(metric)
    db.commit()
    db.refresh(metric)

    return metric