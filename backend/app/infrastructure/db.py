from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import DeclarativeBase
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from app.core.config import settings


class Base(DeclarativeBase):
    """Base class for all ORM models"""
    pass


# Create async engine
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    future=True,
)

# Create async session factory
AsyncSessionFactory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Context manager for database sessions"""
    async with AsyncSessionFactory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for FastAPI to get database session"""
    async with AsyncSessionFactory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database tables"""
    async with engine.begin() as conn:
        # Import all models here to ensure they are registered
        from app.domain.models import (
            TickerWatchlist, OptionWatchlist, Strategy, Trade, CustomStrategy, StrategyLog,
            StrategyExecution, StrategySignal, StrategyPerformance, StrategyTemplate, StrategyBacktest
        )
        from app.models.user import User
        from app.models.integrations import UserIntegration, ConnectedAccount
        from app.models.personal_finance import Institution, Connection, Account, Security, Holding, Transaction, SyncJob
        from app.models.notification import Notification, NotificationTemplate, NotificationDigest
        from app.models.notification_settings import NotificationSettings
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Close database connections"""
    await engine.dispose()


# Alias for compatibility with routers using this name
get_async_session = get_db

