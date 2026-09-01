from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Optional

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)

TOKEN_URL = (
    "https://identity.dataspace.copernicus.eu/auth/realms/CDSE"
    "/protocol/openid-connect/token"
)
CATALOG_URL = "https://sh.dataspace.copernicus.eu/catalog/v1/search"

DEFAULT_TIMEOUT_SECONDS = 30.0


class CDSEClientError(Exception):
    """Raised when CDSE auth or catalog search fails. Never includes secrets."""


@dataclass(frozen=True)
class CDSEScene:
    external_scene_id: str
    observation_date: date
    cloud_cover: Optional[float]


class CDSEClient:
    """
    Thin wrapper around CDSE OAuth + Catalog API.
    Holds no imagery/raster logic — metadata only.
    """

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
    ) -> None:
        settings = get_settings()
        self._client_id = client_id or settings.cdse_client_id
        self._client_secret = client_secret or settings.cdse_client_secret

    def _get_access_token(self) -> str:
        if not self._client_id or not self._client_secret:
            raise CDSEClientError("CDSE credentials are not configured")

        try:
            response = httpx.post(
                TOKEN_URL,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self._client_id,
                    "client_secret": self._client_secret,
                },
                timeout=DEFAULT_TIMEOUT_SECONDS,
            )
        except httpx.HTTPError as exc:
            # Never include exc's underlying request details, which could
            # echo the posted client_secret.
            raise CDSEClientError(
                "Failed to reach CDSE authentication endpoint"
            ) from None

        if response.status_code != 200:
            raise CDSEClientError(
                f"CDSE authentication failed with status {response.status_code}"
            )

        token = response.json().get("access_token")
        if not token:
            raise CDSEClientError(
                "CDSE authentication response missing access_token"
            )
        return token

    def search_scenes(
        self,
        geometry: dict[str, Any],
        start_date: date,
        end_date: date,
        max_cloud_cover: float,
        collection: str = "sentinel-2-l2a",
    ) -> list[CDSEScene]:
        token = self._get_access_token()

        payload: dict[str, Any] = {
            "collections": [collection],
            "datetime": (
                f"{start_date.isoformat()}T00:00:00Z/"
                f"{end_date.isoformat()}T23:59:59Z"
            ),
            "intersects": geometry,
            "filter": f"eo:cloud_cover <= {max_cloud_cover}",
            "limit": 100,
        }

        try:
            response = httpx.post(
                CATALOG_URL,
                json=payload,
                headers={"Authorization": f"Bearer {token}"},
                timeout=DEFAULT_TIMEOUT_SECONDS,
            )
        except httpx.HTTPError:
            raise CDSEClientError("Failed to reach CDSE catalog endpoint") from None

        if response.status_code != 200:
            raise CDSEClientError(
                f"CDSE catalog search failed with status {response.status_code}"
            )

        body = response.json()
        features = body.get("features", [])

        scenes: list[CDSEScene] = []
        for feature in features:
            scene = self._feature_to_scene(feature)
            if scene is not None:
                scenes.append(scene)
        return scenes

    @staticmethod
    def _feature_to_scene(feature: dict[str, Any]) -> Optional[CDSEScene]:
        feature_id = feature.get("id")
        properties = feature.get("properties", {}) or {}
        datetime_str = properties.get("datetime")
        cloud_cover = properties.get("eo:cloud_cover")

        if not feature_id or not datetime_str:
            logger.warning("Skipping CDSE feature missing id or datetime")
            return None

        acquired_at = datetime.fromisoformat(datetime_str.replace("Z", "+00:00"))

        return CDSEScene(
            external_scene_id=feature_id,
            observation_date=acquired_at.date(),
            cloud_cover=float(cloud_cover) if cloud_cover is not None else None,
        )