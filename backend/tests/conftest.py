"""Pytest configuration and fixtures for backend tests"""
import pytest
import asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from httpx import AsyncClient, ASGITransport

from app.infrastructure.db import Base
from app.main import app
from app.core.deps import get_current_user
# Import models to ensure they are registered with Base.metadata
from app.domain import models


# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///./data/test_trading.db"

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    future=True,
)

# Create test session factory
TestAsyncSessionFactory = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def test_db():
    """Create test database tables"""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
async def db_session(test_db) -> AsyncGenerator[AsyncSession, None]:
    """Get database session for testing"""
    async with TestAsyncSessionFactory() as session:
        yield session
        await session.rollback()


@pytest.fixture(scope="function")
async def client(test_db) -> AsyncGenerator[AsyncClient, None]:
    """Get async HTTP client for testing API endpoints"""
    
    # Override the get_current_user dependency to return a test user
    async def override_get_current_user():
        return "test_user_123"
    
    app.dependency_overrides[get_current_user] = override_get_current_user
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
async def authenticated_client(test_db) -> AsyncGenerator[AsyncClient, None]:
    """Get authenticated async HTTP client for testing protected endpoints"""
    
    async def override_get_current_user():
        # Return a valid UUID string (required for UUID-based user IDs)
        return "12345678-1234-1234-1234-123456789012"
    
    app.dependency_overrides[get_current_user] = override_get_current_user
    
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, 
        base_url="http://test",
        headers={"Authorization": "Bearer test_token"}
    ) as client:
        yield client
    
    app.dependency_overrides.clear()

