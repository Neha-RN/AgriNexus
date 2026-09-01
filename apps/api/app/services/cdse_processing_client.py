from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

import httpx

from app.services.cdse_client import (
    CDSEClient,
    CDSEClientError,
)

PROCESSING_URL = "https://sh.dataspace.copernicus.eu/process/v1"

DEFAULT_TIMEOUT_SECONDS = 60.0


@dataclass(frozen=True)
class CDSEProcessingResult:
    """
    Raw result returned by the CDSE Processing API.
    """

    content: bytes
    content_type: str


class CDSEProcessingClient(CDSEClient):
    """
    Client for requesting processed Sentinel-2 data from the
    Copernicus Data Space Ecosystem Processing API.
    """

    def process_sentinel2(
        self,
        geometry: dict[str, Any],
        start_date: date,
        end_date: date,
        evalscript: str,
        width: int = 512,
        height: int = 512,
    ) -> CDSEProcessingResult:
        """
        Request processed Sentinel-2 L2A data for a GeoJSON geometry.
        """

        token = self._get_access_token()

        payload: dict[str, Any] = {
            "input": {
                "bounds": {
                    "geometry": geometry,
                    "properties": {
                        "crs": (
                            "http://www.opengis.net/def/crs/"
                            "OGC/1.3/CRS84"
                        )
                    },
                },
                "data": [
                    {
                        "type": "S2L2A",
                        "dataFilter": {
                            "timeRange": {
                                "from": (
                                    f"{start_date.isoformat()}"
                                    "T00:00:00Z"
                                ),
                                "to": (
                                    f"{end_date.isoformat()}"
                                    "T23:59:59Z"
                                ),
                            },
                            "mosaickingOrder": "leastCC",
                        },
                    }
                ],
            },
            "output": {
                "width": width,
                "height": height,
                "responses": [
                    {
                        "identifier": "default",
                        "format": {
                            "type": "image/tiff",
                        },
                    }
                ],
            },
            "evalscript": evalscript,
        }

        try:
            response = httpx.post(
                PROCESSING_URL,
                json=payload,
                headers={
                    "Authorization": f"Bearer {token}",
                },
                timeout=DEFAULT_TIMEOUT_SECONDS,
            )
        except httpx.HTTPError:
            raise CDSEClientError(
                "Failed to reach CDSE Processing API"
            ) from None

        if response.status_code != 200:
            raise CDSEClientError(
                "CDSE Processing API failed "
                f"with status {response.status_code}: "
                f"{response.text[:500]}"
            )

        return CDSEProcessingResult(
            content=response.content,
            content_type=response.headers.get(
                "content-type",
                "",
            ),
        )