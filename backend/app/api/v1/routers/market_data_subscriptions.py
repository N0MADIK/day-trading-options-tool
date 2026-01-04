"""Market Data Subscriptions API router"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import UUID

from app.infrastructure.db import get_async_session
from app.core.deps import get_current_user
from app.models.market_data_subscription import MarketDataSubscription
from app.schemas.market_data_subscription import (
    MarketDataSubscriptionCreate,
    MarketDataSubscriptionUpdate,
    MarketDataSubscriptionResponse,
    MarketDataProviderInfo
)

router = APIRouter(prefix="/market-data-subscriptions", tags=["market-data-subscriptions"])

# List of available market data providers
MARKET_DATA_PROVIDERS = [
    MarketDataProviderInfo(
        id="yfinance",
        name="Yahoo Finance",
        type="free",
        description="Free market data with 15-min delay",
        supports_realtime=False,
        requires_api_key=False
    ),
    MarketDataProviderInfo(
        id="alpaca",
        name="Alpaca Markets",
        type="api_key",
        description="Real-time and historical data for US equities",
        supports_realtime=True,
        requires_api_key=True
    ),
    MarketDataProviderInfo(
        id="polygon",
        name="Polygon.io",
        type="api_key",
        description="Real-time and historical market data",
        supports_realtime=True,
        requires_api_key=True
    ),
    MarketDataProviderInfo(
        id="tradier",
        name="Tradier",
        type="oauth",
        description="Options and equities data",
        supports_realtime=True,
        requires_api_key=True
    ),
    MarketDataProviderInfo(
        id="tiingo",
        name="Tiingo",
        type="api_key",
        description="EOD and real-time data",
        supports_realtime=True,
        requires_api_key=True
    ),
    MarketDataProviderInfo(
        id="interactive_brokers",
        name="Interactive Brokers",
        type="oauth",
        description="Professional trading data",
        supports_realtime=True,
        requires_api_key=False
    ),
]


@router.get("/providers", response_model=List[MarketDataProviderInfo])
async def list_providers():
    """List all available market data providers"""
    return MARKET_DATA_PROVIDERS


@router.get("/", response_model=List[MarketDataSubscriptionResponse])
async def list_subscriptions(
    current_user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """List all market data subscriptions for the current user"""
    user_id = UUID(current_user_id)
    result = await session.execute(
        select(MarketDataSubscription).where(MarketDataSubscription.user_id == user_id)
    )
    return result.scalars().all()


@router.post("/", response_model=MarketDataSubscriptionResponse, status_code=status.HTTP_201_CREATED)
async def create_subscription(
    subscription_data: MarketDataSubscriptionCreate,
    current_user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Create a new market data subscription"""
    user_id = UUID(current_user_id)
    
    # Check if subscription already exists for this provider
    existing = await session.execute(
        select(MarketDataSubscription).where(
            MarketDataSubscription.user_id == user_id,
            MarketDataSubscription.provider_name == subscription_data.provider_name
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Subscription already exists for provider: {subscription_data.provider_name}"
        )
    
    subscription = MarketDataSubscription(
        user_id=user_id,
        provider_name=subscription_data.provider_name,
        provider_type=subscription_data.provider_type,
        api_key_encrypted=subscription_data.api_key_encrypted,
        api_secret_encrypted=subscription_data.api_secret_encrypted,
        subscription_tier=subscription_data.subscription_tier,
        features=subscription_data.features or [],
        is_active=True
    )
    
    session.add(subscription)
    await session.commit()
    await session.refresh(subscription)
    return subscription


@router.get("/{subscription_id}", response_model=MarketDataSubscriptionResponse)
async def get_subscription(
    subscription_id: UUID,
    current_user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Get a single subscription by ID"""
    user_id = UUID(current_user_id)
    result = await session.execute(
        select(MarketDataSubscription).where(
            MarketDataSubscription.id == subscription_id,
            MarketDataSubscription.user_id == user_id
        )
    )
    subscription = result.scalar_one_or_none()
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )
    return subscription


@router.put("/{subscription_id}", response_model=MarketDataSubscriptionResponse)
async def update_subscription(
    subscription_id: UUID,
    update_data: MarketDataSubscriptionUpdate,
    current_user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Update a subscription (e.g., update credentials)"""
    user_id = UUID(current_user_id)
    result = await session.execute(
        select(MarketDataSubscription).where(
            MarketDataSubscription.id == subscription_id,
            MarketDataSubscription.user_id == user_id
        )
    )
    subscription = result.scalar_one_or_none()
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )
    
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(subscription, field, value)
    
    await session.commit()
    await session.refresh(subscription)
    return subscription


@router.delete("/{subscription_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subscription(
    subscription_id: UUID,
    current_user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Delete a subscription"""
    user_id = UUID(current_user_id)
    result = await session.execute(
        select(MarketDataSubscription).where(
            MarketDataSubscription.id == subscription_id,
            MarketDataSubscription.user_id == user_id
        )
    )
    subscription = result.scalar_one_or_none()
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )
    
    await session.delete(subscription)
    await session.commit()
