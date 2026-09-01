from datetime import date
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.core.database import get_db
from app.main import app
from app.models.field import Field
from app.services.cdse_client import CDSEScene
from app.services.satellite_observation_service import (
    sync_observations_from_scenes,
)

client = TestClient(app)


def test_scene_converted_to_observation_when_new() -> None:
    scenes = [
        CDSEScene(
            external_scene_id="S2A_TEST_1",
            observation_date=date(2026, 6, 25),
            cloud_cover=0.39,
        )
    ]

    mock_existing_query = MagicMock()
    mock_existing_query.filter.return_value.first.return_value = None

    db = MagicMock()
    db.query.return_value = mock_existing_query

    created_records: list = []

    def fake_add(obj):
        created_records.append(obj)

    def fake_refresh(obj):
        obj.id = 1

    db.add.side_effect = fake_add
    db.refresh.side_effect = fake_refresh

    results = sync_observations_from_scenes(
        db,
        field_id=1,
        source="sentinel-2-l2a",
        scenes=scenes,
    )

    assert len(results) == 1
    assert len(created_records) == 1
    assert created_records[0].id == 1
    assert created_records[0].external_scene_id == "S2A_TEST_1"
    assert created_records[0].observation_date == date(2026, 6, 25)


def test_duplicate_external_scene_id_not_inserted_twice() -> None:
    scenes = [
        CDSEScene(
            external_scene_id="S2A_TEST_DUP",
            observation_date=date(2026, 6, 25),
            cloud_cover=0.39,
        )
    ]

    existing_observation = SimpleNamespace(
        id=99,
        field_id=1,
        source="sentinel-2-l2a",
        external_scene_id="S2A_TEST_DUP",
        observation_date=date(2026, 6, 25),
        cloud_cover=0.39,
    )

    mock_existing_query = MagicMock()
    mock_existing_query.filter.return_value.first.return_value = (
        existing_observation
    )

    db = MagicMock()
    db.query.return_value = mock_existing_query

    results = sync_observations_from_scenes(
        db,
        field_id=1,
        source="sentinel-2-l2a",
        scenes=scenes,
    )

    assert len(results) == 1
    assert results[0] is existing_observation
    db.add.assert_not_called()


def test_sync_endpoint_unknown_field_returns_404() -> None:
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
        response = client.post(
            "/api/v1/fields/999/observations/sync"
        )

        assert response.status_code == 404

    finally:
        app.dependency_overrides.pop(get_db, None)


@patch("app.api.v1.fields.CDSEClient")
def test_sync_endpoint_returns_created_observations(
    mock_client_cls,
) -> None:
    fake_field = SimpleNamespace(
        id=1,
        name="Test Field",
        geometry="fake-wkb",
    )

    mock_client_instance = MagicMock()

    mock_client_instance.search_scenes.return_value = [
        CDSEScene(
            external_scene_id="S2A_TEST_2",
            observation_date=date(2026, 6, 25),
            cloud_cover=1.28,
        )
    ]

    mock_client_cls.return_value = mock_client_instance

    def fake_get_db():
        mock_field_query = MagicMock()
        mock_field_query.filter.return_value.first.return_value = (
            fake_field
        )

        mock_existing_query = MagicMock()
        mock_existing_query.filter.return_value.first.return_value = None

        db = MagicMock()

        db.query.side_effect = lambda model: (
            mock_field_query if model is Field else mock_existing_query
        )

        def fake_refresh(obj):
            obj.id = 1

        db.refresh.side_effect = fake_refresh

        yield db

    with patch(
        "app.api.v1.fields.to_shape"
    ) as mock_to_shape, patch(
        "app.api.v1.fields.mapping"
    ) as mock_mapping:

        mock_to_shape.return_value = "shapely-geom"

        mock_mapping.return_value = {
            "type": "Polygon",
            "coordinates": [],
        }

        app.dependency_overrides[get_db] = fake_get_db

        try:
            response = client.post(
                "/api/v1/fields/1/observations/sync"
                "?start_date=2026-05-28"
                "&end_date=2026-08-26"
                "&max_cloud_cover=30"
            )

            assert response.status_code == 200

            body = response.json()

            assert len(body) == 1
            assert body[0]["id"] == 1
            assert body[0]["field_id"] == 1
            assert body[0]["source"] == "sentinel-2-l2a"
            assert body[0]["external_scene_id"] == "S2A_TEST_2"
            assert body[0]["observation_date"] == "2026-06-25"

            # Numeric/Decimal values may be serialized as strings
            # by Pydantic/FastAPI.
            assert float(body[0]["cloud_cover"]) == 1.28

        finally:
            app.dependency_overrides.pop(get_db, None)

    mock_client_instance.search_scenes.assert_called_once()

    call_kwargs = (
        mock_client_instance.search_scenes.call_args.kwargs
    )

    assert call_kwargs["start_date"] == date(2026, 5, 28)
    assert call_kwargs["end_date"] == date(2026, 8, 26)
    assert call_kwargs["max_cloud_cover"] == 30.0