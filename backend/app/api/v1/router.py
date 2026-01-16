from fastapi import APIRouter

from app.api.v1.routers import (
    health, watchlist, options, trades, strategies, notifications,
    personal_finance, custom_strategies, integrations, auth,
    # New routers for finance-flow integration
    profiles, user_roles, connected_accounts, market_data_subscriptions,
    net_worth, custom_notification_rules, websocket_router, market_data,
    notification_settings, holdings, transactions
)

api_router = APIRouter(prefix="/api/v1")

# Include existing routers
api_router.include_router(auth.router)
api_router.include_router(health.router)
api_router.include_router(watchlist.router)
api_router.include_router(options.router)
api_router.include_router(trades.router)
api_router.include_router(strategies.router)
api_router.include_router(notifications.router)
api_router.include_router(personal_finance.router)
api_router.include_router(custom_strategies.router)
api_router.include_router(integrations.router)

# New routers for finance-flow frontend compatibility
api_router.include_router(profiles.router)
api_router.include_router(user_roles.router)
api_router.include_router(connected_accounts.router)
api_router.include_router(market_data_subscriptions.router)
api_router.include_router(net_worth.router)
api_router.include_router(custom_notification_rules.router)
api_router.include_router(websocket_router.router)
api_router.include_router(market_data.router)
api_router.include_router(notification_settings.router)
api_router.include_router(holdings.router)
api_router.include_router(transactions.router)

