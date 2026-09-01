from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Repo root: apps/api/app/core/config.py -> up 4 levels -> repo root
_ENV_PATH = Path(__file__).resolve().parents[4] / ".env"
if _ENV_PATH.exists():
    load_dotenv(_ENV_PATH)


class Settings:
    """Minimal typed settings wrapper. No unrelated dependencies."""

    def __init__(self) -> None:
        raw_url = os.getenv("DATABASE_URL")
        if not raw_url:
            raise RuntimeError("DATABASE_URL environment variable is not set")
        self.database_url: str = self._normalize_url(raw_url)

        # CDSE credentials are optional at startup — only required when the
        # sync endpoint is actually invoked. This keeps the app bootable
        # (tests, local dev without CDSE access) without them configured.
        self.cdse_client_id: Optional[str] = os.getenv("CDSE_CLIENT_ID")
        self.cdse_client_secret: Optional[str] = os.getenv("CDSE_CLIENT_SECRET")

    @staticmethod
    def _normalize_url(url: str) -> str:
        # Force the psycopg3 driver explicitly, per requirements.
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+psycopg://", 1)
        return url


@lru_cache
def get_settings() -> Settings:
    return Settings()