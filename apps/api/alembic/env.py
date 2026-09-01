from __future__ import annotations

import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

# Add the API project directory to Python's import path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.core.config import get_settings
from app.core.database import Base
from app.models import Country, Field, SatelliteObservation  # noqa: F401
from app.models.satellite_metric import SatelliteMetric  # noqa: F401


config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


# Load the application's database configuration
settings = get_settings()

config.set_main_option(
    "sqlalchemy.url",
    settings.database_url,
)


# SQLAlchemy metadata containing all application-managed tables
target_metadata = Base.metadata


def include_object(object, name, type_, reflected, compare_to):
    """
    Prevent Alembic from generating DROP statements for database tables
    that exist in PostgreSQL/PostGIS but are not managed by this application.
    """

    # A reflected table that has no corresponding SQLAlchemy model should
    # be ignored during autogeneration.
    if type_ == "table" and reflected and compare_to is None:
        return False

    return True


def run_migrations_offline() -> None:
    """Run migrations without creating an Engine."""

    url = config.get_main_option("sqlalchemy.url")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations using a live database connection."""

    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()