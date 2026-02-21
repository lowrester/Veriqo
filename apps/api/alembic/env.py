"""Alembic environment configuration."""

import asyncio
import os
import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import pool
from sqlalchemy.engine import Connection

from alembic import context

# Add src directory to path so we can import veriqko package
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from veriqko.config import get_settings

# Import all models to ensure they are registered with Base
from veriqko.db.base import Base
from veriqko.devices.models import Device  # noqa: F401
from veriqko.evidence.models import Evidence  # noqa: F401
from veriqko.jobs.models import Job, JobHistory, TestResult, TestStep  # noqa: F401
from veriqko.printing.models import LabelTemplate, Printer  # noqa: F401
from veriqko.reports.models import Report  # noqa: F401
from veriqko.settings.models import SystemSetting  # noqa: F401
from veriqko.stations.models import Station  # noqa: F401
from veriqko.users.models import User  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.database_url)

# Debug: Print masked URL and .env status to help diagnose connection issues
import re

# Improved masking: keep the protocol and username, hide the password
masked_url = re.sub(r'(://[^:]+):([^@]+)@', r'\1:***@', settings.database_url)
print(f"INFO [alembic.env] Connecting to: {masked_url}", file=sys.stderr)

# Check if .env was found
env_file_path = settings.model_config.get("env_file")
if isinstance(env_file_path, list):
    env_file = Path(env_file_path[0])
else:
    env_file = Path(env_file_path or ".env")

if env_file.exists():
    print(f"INFO [alembic.env] Loaded config from: {env_file.absolute()}", file=sys.stderr)
else:
    print(f"WARN [alembic.env] Config file NOT FOUND at: {env_file.absolute()}", file=sys.stderr)

# Check if using the default password
default_db_url = "postgresql+asyncpg://veriqko:veriqko@localhost:5432/veriqko"
is_default = settings.database_url == default_db_url
print(f"DEBUG [alembic.env] Using DEFAULT password: {is_default}", file=sys.stderr)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Run migrations with connection."""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in async mode."""
    from sqlalchemy.ext.asyncio import create_async_engine

    # Create engine directly from settings to ensure it matches API config
    connectable = create_async_engine(
        settings.database_url,
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
