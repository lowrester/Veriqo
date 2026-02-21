import asyncio
from collections.abc import AsyncGenerator, Generator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from veriqko.config import get_settings
from veriqko.db.base import get_db
from veriqko.main import app

settings = get_settings()

# We use a separate test database or the same one?
# ideally a test db. For now, let's assume we can mock or use a transaction rollback strategy.
# Since we are using an actual Postgres, we might want to override the URL.
# For this "infrastructure" phase, let's setup the engine.

# Override database URL for tests (if we had a test db)
# TEST_DATABASE_URL = settings.database_url.replace("veriqko", "veriqko_test")

@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def db_engine():
    engine = create_async_engine(str(settings.database_url), poolclass=NullPool)
    # async with engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.create_all)
    yield engine
    # async with engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest.fixture(scope="function")
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    async_session = sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session
        # transaction rollback handled by test isolation usually,
        # but here we rely on dependency override

@pytest.fixture(scope="function")
async def async_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Fixture for creating an HTTP client for testing the FastAPI application.
    """

    # Override the get_db dependency
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers() -> dict:
    # Returns headers for a mocked authenticated user
    # In a real scenario, we might generate a valid JWT here
    return {"Authorization": "Bearer mock_token"}
