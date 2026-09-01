from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from app.services.cdse_client import CDSEClient, CDSEClientError


def _mock_token_response():
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {
        "access_token": "fake-token-123"
    }
    return response


def _mock_catalog_response(features):
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {
        "features": features
    }
    return response


@patch("app.services.cdse_client.httpx.post")
def test_authentication_request_succeeds(mock_post) -> None:
    mock_post.return_value = _mock_token_response()

    client = CDSEClient(
        client_id="id",
        client_secret="secret",
    )

    token = client._get_access_token()

    assert token == "fake-token-123"

    mock_post.assert_called_once()

    called_kwargs = mock_post.call_args.kwargs

    assert called_kwargs["data"]["grant_type"] == "client_credentials"
    assert called_kwargs["data"]["client_id"] == "id"
    assert called_kwargs["data"]["client_secret"] == "secret"


@patch("app.services.cdse_client.get_settings")
def test_authentication_missing_credentials_raises(mock_get_settings) -> None:
    settings = MagicMock()
    settings.cdse_client_id = None
    settings.cdse_client_secret = None

    mock_get_settings.return_value = settings

    client = CDSEClient()

    with pytest.raises(CDSEClientError):
        client._get_access_token()


@patch("app.services.cdse_client.httpx.post")
def test_catalog_search_sends_field_geometry(mock_post) -> None:
    mock_post.side_effect = [
        _mock_token_response(),
        _mock_catalog_response([]),
    ]

    geometry = {
        "type": "Polygon",
        "coordinates": [
            [
                [80.12, 10.92],
                [80.125, 10.92],
                [80.125, 10.925],
                [80.12, 10.925],
                [80.12, 10.92],
            ]
        ],
    }

    client = CDSEClient(
        client_id="id",
        client_secret="secret",
    )

    client.search_scenes(
        geometry=geometry,
        start_date=date(2026, 5, 28),
        end_date=date(2026, 8, 26),
        max_cloud_cover=30,
    )

    catalog_call = mock_post.call_args_list[1]
    sent_payload = catalog_call.kwargs["json"]

    assert sent_payload["intersects"] == geometry
    assert sent_payload["collections"] == [
        "sentinel-2-l2a"
    ]


@patch("app.services.cdse_client.httpx.post")
def test_catalog_search_applies_date_range_and_cloud_filter(
    mock_post,
) -> None:
    mock_post.side_effect = [
        _mock_token_response(),
        _mock_catalog_response([]),
    ]

    client = CDSEClient(
        client_id="id",
        client_secret="secret",
    )

    client.search_scenes(
        geometry={
            "type": "Polygon",
            "coordinates": [],
        },
        start_date=date(2026, 5, 28),
        end_date=date(2026, 8, 26),
        max_cloud_cover=30,
    )

    catalog_call = mock_post.call_args_list[1]
    sent_payload = catalog_call.kwargs["json"]

    assert sent_payload["datetime"] == (
        "2026-05-28T00:00:00Z/"
        "2026-08-26T23:59:59Z"
    )

    assert sent_payload["filter"] == (
        "eo:cloud_cover <= 30"
    )


@patch("app.services.cdse_client.httpx.post")
def test_catalog_search_parses_scenes(mock_post) -> None:
    features = [
        {
            "id": (
                "S2A_MSIL2A_20260625T050241_"
                "N0512_R119_T44PLT_20260625T100609.SAFE"
            ),
            "properties": {
                "datetime": "2026-06-25T05:02:41Z",
                "eo:cloud_cover": 0.39,
            },
        }
    ]

    mock_post.side_effect = [
        _mock_token_response(),
        _mock_catalog_response(features),
    ]

    client = CDSEClient(
        client_id="id",
        client_secret="secret",
    )

    scenes = client.search_scenes(
        geometry={
            "type": "Polygon",
            "coordinates": [],
        },
        start_date=date(2026, 5, 28),
        end_date=date(2026, 8, 26),
        max_cloud_cover=30,
    )

    assert len(scenes) == 1

    assert scenes[0].external_scene_id.startswith(
        "S2A_MSIL2A_20260625"
    )

    assert scenes[0].observation_date == date(
        2026,
        6,
        25,
    )

    assert scenes[0].cloud_cover == 0.39


@patch("app.services.cdse_client.httpx.post")
def test_authentication_failure_raises_clean_error(
    mock_post,
) -> None:
    response = MagicMock()
    response.status_code = 401

    mock_post.return_value = response

    client = CDSEClient(
        client_id="bad-id",
        client_secret="bad-secret",
    )

    with pytest.raises(CDSEClientError) as exc_info:
        client._get_access_token()

    error_message = str(exc_info.value)

    assert "bad-id" not in error_message
    assert "bad-secret" not in error_message