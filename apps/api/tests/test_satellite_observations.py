from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from app.core.database import get_db
from app.main import app
from app.models.field import Field
from app.models.satellite_observation import SatelliteObservation
from app.schemas.satellite_observation import SatelliteObservationRead
from app.services.satellite_observation_service import (
    list_observations_for_field,
)

client = TestClient(app)


def test_satellite_observation_model_importable() -> None:
    assert SatelliteObservation.__tablename__ == "satellite_observations"


def test_satellite_observation_schema_serialization() -> None:
    fake_observation = SimpleNamespace(
        id=1,
        field_id=3,
        observation_date=date(2026, 8, 15),
        source="sentinel-2",
        cloud_cover=Decimal("12.50"),
        external_scene_id="S2A_MSIL2A_20260815",
    )

    result = SatelliteObservationRead.model_validate(fake_observation)

    assert result.id == 1
    assert result.field_id == 3
    assert result.observation_date == date(2026, 8, 15)
    assert result.source == "sentinel-2"
    assert result.cloud_cover == Decimal("12.50")
    assert result.external_scene_id == "S2A_MSIL2A_20260815"


def test_satellite_observation_schema_optional_fields_none() -> None:
    fake_observation = SimpleNamespace(
        id=2,
        field_id=3,
        observation_date=date(2026, 8, 10),
        source="landsat-8",
        cloud_cover=None,
        external_scene_id=None,
    )

    result = SatelliteObservationRead.model_validate(fake_observation)
    assert result.cloud_cover is None
    assert result.external_scene_id is None


def test_list_observations_for_field_orders_by_date_desc() -> None:
    older = SimpleNamespace(id=1, observation_date=date(2026, 8, 1))
    newer = SimpleNamespace(id=2, observation_date=date(2026, 8, 15))

    mock_query = MagicMock()
    mock_query.filter.return_value.order_by.return_value.all.return_value = [
        newer,
        older,
    ]

    db = MagicMock()
    db.query.return_value = mock_query

    result = list_observations_for_field(db, field_id=3)

    db.query.assert_called_once_with(SatelliteObservation)
    assert result == [newer, older]


def test_observations_route_registered() -> None:
    paths = app.openapi()["paths"]
    assert "/api/v1/fields/{field_id}/observations" in paths

def test_get_observations_for_unknown_field_returns_404() -> None:
    def fake_get_db():
        mock_field_query = MagicMock()
        mock_field_query.filter.return_value.first.return_value = None

        db = MagicMock()
        db.query.side_effect = lambda model: (
            mock_field_query if model is Field else MagicMock()
        )
        yield db

    app.dependency_overrides[get_db] = fake_get_db
    try:
        response = client.get("/api/v1/fields/999/observations")
        assert response.status_code == 404
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_get_observations_for_known_field_returns_ordered_list() -> None:
    fake_field = SimpleNamespace(id=1, name="Test Field")

    def fake_get_db():
        mock_field_query = MagicMock()
        mock_field_query.filter.return_value.first.return_value = fake_field

        mock_obs_query = MagicMock()
        mock_obs_query.filter.return_value.order_by.return_value.all.return_value = [
            {
                "id": 2,
                "field_id": 1,
                "observation_date": "2026-08-15",
                "source": "sentinel-2",
                "cloud_cover": 10.0,
                "external_scene_id": "S2_2",
            },
            {
                "id": 1,
                "field_id": 1,
                "observation_date": "2026-08-01",
                "source": "sentinel-2",
                "cloud_cover": 20.0,
                "external_scene_id": "S2_1",
            },
        ]

        db = MagicMock()
        db.query.side_effect = lambda model: (
            mock_field_query if model is Field else mock_obs_query
        )
        yield db

    app.dependency_overrides[get_db] = fake_get_db
    try:
        response = client.get("/api/v1/fields/1/observations")
        assert response.status_code == 200
        body = response.json()
        assert len(body) == 2
        assert body[0]["id"] == 2
        assert body[1]["id"] == 1
    finally:
        app.dependency_overrides.pop(get_db, None)