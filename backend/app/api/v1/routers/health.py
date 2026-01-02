from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.infrastructure.db import get_db

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    """Basic health check"""
    return {
        "status": "healthy",
        "service": "options-trading-api",
        "version": "1.0.0"
    }


@router.get("/health/db")
async def database_health_check(
    session: AsyncSession = Depends(get_db)
):
    """Database health check"""
    try:
        # Simple query to test database connection
        result = await session.execute(text("SELECT 1"))
        await session.commit()
        
        return {
            "status": "healthy",
            "database": "connected",
            "query_result": result.scalar_one()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }
