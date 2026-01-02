from typing import AsyncGenerator
from fastapi import Depends

from app.infrastructure.db import get_db, AsyncSession
from app.services.watchlist_service import WatchlistService


async def get_watchlist_service(
    session: AsyncSession = Depends(get_db)
) -> WatchlistService:
    """Dependency to get watchlist service instance"""
    return WatchlistService(session)
