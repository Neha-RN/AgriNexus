from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

_ENV_PATH = Path(__file__).resolve().parents[4] / ".env"

if _ENV_PATH.exists():
    load_dotenv(_ENV_PATH)


class Settings:
    """Application configuration loaded from environment variables."""

    def __init__(self) -> None:
        raw_url = os.getenv("DATABASE_URL")

        if not raw_url:
            raise RuntimeError("DATABASE_URL environment variable is not set")

        self.database_url: str = self._normalize_url(raw_url)

    @staticmethod
    def _normalize_url(url: str) -> str:
        if url.startswith("postgresql://"):
            return url.replace(
                "postgresql://",
                "postgresql+psycopg://",
                1,
            )

        return url


@lru_cache
def get_settings() -> Settings:
    return Settings()