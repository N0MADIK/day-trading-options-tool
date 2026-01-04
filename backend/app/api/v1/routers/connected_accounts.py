"""Connected Accounts API router - Facade for finance-flow compatibility"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID

from app.infrastructure.db import get_async_session
from app.core.deps import get_current_user
# NOTE: PersonalFinanceService import moved to TODO when implementing actual endpoints
# This avoids circular imports at module load time
from app.schemas.connected_accounts import (
    ConnectedAccountResponse,
    ConnectedAccountCreate,
    ConnectedAccountUpdate,
    ConnectedAccountSync
)

router = APIRouter(prefix="/connected-accounts", tags=["connected-accounts"])




@router.get("/", response_model=List[ConnectedAccountResponse])
async def list_connected_accounts(
    current_user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    List all connected accounts for the current user.
    This aggregates data from institutions, connections, and accounts tables.
    """
    # For now, return mock structure until we integrate with personal_finance_service
    # TODO: Implement proper aggregation from existing tables
    return []


@router.get("/{account_id}", response_model=ConnectedAccountResponse)
async def get_connected_account(
    account_id: UUID,
    current_user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Get a single connected account by ID"""
    # TODO: Implement
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Account not found"
    )


@router.post("/", response_model=ConnectedAccountResponse, status_code=status.HTTP_201_CREATED)
async def create_connected_account(
    account_data: ConnectedAccountCreate,
    current_user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Create a new connected account (usually after Plaid/SnapTrade link)"""
    # TODO: Implement - this should create institution + connection + account
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Not yet implemented"
    )


@router.put("/{account_id}", response_model=ConnectedAccountResponse)
async def update_connected_account(
    account_id: UUID,
    account_data: ConnectedAccountUpdate,
    current_user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Update a connected account"""
    # TODO: Implement
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Account not found"
    )


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def disconnect_account(
    account_id: UUID,
    current_user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Disconnect/remove an account"""
    # TODO: Implement - should soft delete or mark as disconnected
    pass


@router.post("/{account_id}/sync", response_model=ConnectedAccountSync)
async def sync_account(
    account_id: UUID,
    current_user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Trigger a sync for an account to refresh holdings and transactions"""
    # TODO: Implement - should use Plaid/SnapTrade to fetch latest data
    return ConnectedAccountSync(
        account_id=account_id,
        status="pending",
        message="Sync queued"
    )
