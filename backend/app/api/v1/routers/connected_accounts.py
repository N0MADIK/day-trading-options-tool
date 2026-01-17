"""Connected Accounts API router - Facade for finance-flow compatibility

This router follows the token broker pattern from financial_connections_guidelines.md:
- Only IntegrationService decrypts tokens
- This router handles metadata only
- No raw tokens are exposed to this layer
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import UUID, uuid4
from datetime import datetime

from app.infrastructure.db import get_async_session
from app.core.deps import get_current_user
from app.models.integrations import ConnectedAccount, UserIntegration, IntegrationStatus
from app.services.integration_service import IntegrationService
from app.schemas.connected_accounts import (
    ConnectedAccountResponse,
    ConnectedAccountCreate,
    ConnectedAccountUpdate,
    ConnectedAccountSync
)

router = APIRouter(prefix="/connected-accounts", tags=["connected-accounts"])


def _map_integration_status_to_connection_status(status: IntegrationStatus) -> str:
    """Map integration status to connection status string"""
    mapping = {
        IntegrationStatus.ACTIVE: "active",
        IntegrationStatus.INACTIVE: "disabled",
        IntegrationStatus.ERROR: "error",
        IntegrationStatus.EXPIRED: "needs_reauth"
    }
    return mapping.get(status, "error")


@router.get("/", response_model=List[ConnectedAccountResponse])
async def list_connected_accounts(
    current_user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    List all connected accounts for the current user.
    Aggregates data from UserIntegration and ConnectedAccount tables.
    
    Following financial_connections_guidelines.md:
    - Returns only metadata (no tokens)
    - Token operations delegated to IntegrationService
    """
    # Query all integrations for this user
    result = await session.execute(
        select(UserIntegration).where(UserIntegration.user_id == current_user_id)
    )
    integrations = result.scalars().all()
    
    accounts = []
    for integration in integrations:
        for account in integration.connected_accounts:
            # Map to the finance-flow expected format
            # Note: Using a deterministic UUID based on the integer ID for compatibility
            account_uuid = UUID(int=account.id)
            user_uuid = UUID(int=hash(current_user_id) % (2**128))
            
            accounts.append(ConnectedAccountResponse(
                id=account_uuid,
                user_id=user_uuid,
                institution_name=account.institution_name or integration.integration_type.value.title(),
                institution_type=account.account_type or "brokerage",
                account_name=account.account_name or "Account",
                account_number_masked=account.external_account_id[-4:] if account.external_account_id else None,
                balance=0.0,  # Balance requires decryption - handled by separate endpoint
                is_connected=account.is_active,
                connection_status=_map_integration_status_to_connection_status(integration.status),
                last_synced_at=account.last_successful_sync,
                metadata={
                    "integration_id": integration.id,
                    "account_id": account.id,
                    "integration_type": integration.integration_type.value
                },
                created_at=account.created_at or datetime.utcnow(),
                updated_at=account.updated_at
            ))
    
    return accounts


@router.get("/{account_id}", response_model=ConnectedAccountResponse)
async def get_connected_account(
    account_id: int,  # Using int since our DB uses integer PKs
    current_user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Get a single connected account by ID"""
    # Join with UserIntegration to verify ownership
    result = await session.execute(
        select(ConnectedAccount, UserIntegration)
        .join(UserIntegration)
        .where(
            ConnectedAccount.id == account_id,
            UserIntegration.user_id == current_user_id
        )
    )
    row = result.first()
    
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    account, integration = row
    account_uuid = UUID(int=account.id)
    user_uuid = UUID(int=hash(current_user_id) % (2**128))
    
    return ConnectedAccountResponse(
        id=account_uuid,
        user_id=user_uuid,
        institution_name=account.institution_name or integration.integration_type.value.title(),
        institution_type=account.account_type or "brokerage",
        account_name=account.account_name or "Account",
        account_number_masked=account.external_account_id[-4:] if account.external_account_id else None,
        balance=0.0,
        is_connected=account.is_active,
        connection_status=_map_integration_status_to_connection_status(integration.status),
        last_synced_at=account.last_successful_sync,
        metadata={
            "integration_id": integration.id,
            "account_id": account.id,
            "integration_type": integration.integration_type.value
        },
        created_at=account.created_at or datetime.utcnow(),
        updated_at=account.updated_at
    )


@router.post("/", response_model=ConnectedAccountResponse, status_code=status.HTTP_201_CREATED)
async def create_connected_account(
    account_data: ConnectedAccountCreate,
    current_user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Create a new connected account.
    Note: Typically accounts are created via the integration flow (Plaid/SnapTrade).
    This endpoint is for manual/direct account creation.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Use /integrations/plaid or /integrations/snaptrade to connect accounts"
    )


@router.put("/{account_id}", response_model=ConnectedAccountResponse)
async def update_connected_account(
    account_id: int,
    account_data: ConnectedAccountUpdate,
    current_user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Update a connected account (e.g., rename or toggle connection)"""
    result = await session.execute(
        select(ConnectedAccount, UserIntegration)
        .join(UserIntegration)
        .where(
            ConnectedAccount.id == account_id,
            UserIntegration.user_id == current_user_id
        )
    )
    row = result.first()
    
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    account, integration = row
    
    # Update fields
    if account_data.account_name is not None:
        account.account_name = account_data.account_name
    if account_data.is_connected is not None:
        account.is_active = account_data.is_connected
    
    await session.commit()
    await session.refresh(account)
    
    account_uuid = UUID(int=account.id)
    user_uuid = UUID(int=hash(current_user_id) % (2**128))
    
    return ConnectedAccountResponse(
        id=account_uuid,
        user_id=user_uuid,
        institution_name=account.institution_name or integration.integration_type.value.title(),
        institution_type=account.account_type or "brokerage",
        account_name=account.account_name or "Account",
        account_number_masked=account.external_account_id[-4:] if account.external_account_id else None,
        balance=0.0,
        is_connected=account.is_active,
        connection_status=_map_integration_status_to_connection_status(integration.status),
        last_synced_at=account.last_successful_sync,
        metadata={
            "integration_id": integration.id,
            "account_id": account.id,
            "integration_type": integration.integration_type.value
        },
        created_at=account.created_at or datetime.utcnow(),
        updated_at=account.updated_at
    )


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def disconnect_account(
    account_id: int,
    current_user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Disconnect/remove an account.
    Per financial_connections_guidelines.md: marks account as inactive.
    Token revocation at provider would be handled by IntegrationService.
    """
    result = await session.execute(
        select(ConnectedAccount, UserIntegration)
        .join(UserIntegration)
        .where(
            ConnectedAccount.id == account_id,
            UserIntegration.user_id == current_user_id
        )
    )
    row = result.first()
    
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    account, integration = row
    
    # Mark as inactive (soft delete per guidelines)
    account.is_active = False
    account.sync_enabled = False
    
    await session.commit()


@router.post("/{account_id}/sync", response_model=ConnectedAccountSync)
async def sync_account(
    account_id: int,
    current_user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Trigger a sync for an account to refresh holdings and transactions.
    Delegates to IntegrationService which handles token decryption (token broker pattern).
    """
    # Find the account and its integration
    result = await session.execute(
        select(ConnectedAccount, UserIntegration)
        .join(UserIntegration)
        .where(
            ConnectedAccount.id == account_id,
            UserIntegration.user_id == current_user_id
        )
    )
    row = result.first()
    
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    account, integration = row
    
    # Use IntegrationService for sync (token broker pattern)
    integration_service = IntegrationService(session)
    
    try:
        sync_result = await integration_service.full_sync(current_user_id, integration.id)
        
        account_uuid = UUID(int=account.id)
        
        return ConnectedAccountSync(
            account_id=account_uuid,
            status="completed",
            message=f"Synced {sync_result.get('total', 0)} accounts",
            last_synced_at=datetime.utcnow()
        )
    except Exception as e:
        account_uuid = UUID(int=account.id)
        return ConnectedAccountSync(
            account_id=account_uuid,
            status="failed",
            message=str(e)
        )
