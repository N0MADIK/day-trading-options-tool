from fastapi import APIRouter

from app.api.v1.routers import health, watchlist, options, trades, strategies, notifications, personal_finance, custom_strategies

api_router = APIRouter(prefix="/api/v1")

# Include sub-routers
api_router.include_router(health.router)
api_router.include_router(watchlist.router)
api_router.include_router(options.router)
api_router.include_router(trades.router)
api_router.include_router(strategies.router)
api_router.include_router(notifications.router)
api_router.include_router(personal_finance.router)
api_router.include_router(custom_strategies.router)
