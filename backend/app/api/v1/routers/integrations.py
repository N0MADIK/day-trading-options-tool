"""API endpoints for external service integrations"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db import get_async_session
from app.services.integration_service import IntegrationService
from app.schemas.integrations import (
    CreateIntegrationRequest, UpdateCredentialsRequest, IntegrationResponse,
    TestConnectionResponse, SyncAccountsResponse, ConnectedAccountResponse,
    PlaidLinkTokenRequest, SnapTradeRegisterRequest, SnapTradeConnectionRequest,
    IntegrationTypeEnum
)
from app.integrations import PlaidIntegration, SnapTradeIntegration
from app.domain.errors import NotFoundError, ValidationError, ExternalServiceError
from app.core.deps import get_current_user


router = APIRouter(prefix="/integrations", tags=["integrations"])


async def get_integration_service(session: AsyncSession = Depends(get_async_session)) -> IntegrationService:
    """Get integration service instance"""
    return IntegrationService(session)


# General integration endpoints
@router.get("/", response_model=List[IntegrationResponse])
async def get_user_integrations(
    current_user: str = Depends(get_current_user),
    service: IntegrationService = Depends(get_integration_service)
):
    """Get all integrations for the current user"""
    try:
        integrations = await service.get_user_integrations(current_user)
        return integrations
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=IntegrationResponse)
async def create_integration(
    request: CreateIntegrationRequest,
    current_user: str = Depends(get_current_user),
    service: IntegrationService = Depends(get_integration_service)
):
    """Create a new integration with user credentials"""
    try:
        from app.models.integrations import IntegrationType
        
        integration_type = IntegrationType(request.integration_type.value)
        result = await service.create_integration(
            user_id=current_user,
            integration_type=integration_type,
            credentials=request.credentials,
            is_sandbox=request.is_sandbox
        )
        return IntegrationResponse(**result)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except ExternalServiceError as e:
        raise HTTPException(status_code=502, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{integration_id}/credentials")
async def update_integration_credentials(
    integration_id: int,
    request: UpdateCredentialsRequest,
    current_user: str = Depends(get_current_user),
    service: IntegrationService = Depends(get_integration_service)
):
    """Update credentials for an existing integration"""
    try:
        result = await service.update_credentials(
            user_id=current_user,
            integration_id=integration_id,
            credentials=request.credentials
        )
        return result
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except ExternalServiceError as e:
        raise HTTPException(status_code=502, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{integration_id}")
async def delete_integration(
    integration_id: int,
    current_user: str = Depends(get_current_user),
    service: IntegrationService = Depends(get_integration_service)
):
    """Delete an integration"""
    try:
        result = await service.delete_integration(current_user, integration_id)
        return result
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{integration_id}/test", response_model=TestConnectionResponse)
async def test_integration_connection(
    integration_id: int,
    current_user: str = Depends(get_current_user),
    service: IntegrationService = Depends(get_integration_service)
):
    """Test connection for an integration"""
    try:
        result = await service.test_connection(current_user, integration_id)
        return TestConnectionResponse(connected=True, details=result)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except ExternalServiceError as e:
        return TestConnectionResponse(connected=False, error=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{integration_id}/sync", response_model=SyncAccountsResponse)
async def sync_integration_accounts(
    integration_id: int,
    current_user: str = Depends(get_current_user),
    service: IntegrationService = Depends(get_integration_service)
):
    """Sync accounts from an integration"""
    try:
        result = await service.sync_accounts(current_user, integration_id)
        return SyncAccountsResponse(**result)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except ExternalServiceError as e:
        raise HTTPException(status_code=502, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{integration_id}/accounts", response_model=List[ConnectedAccountResponse])
async def get_integration_accounts(
    integration_id: int,
    current_user: str = Depends(get_current_user),
    service: IntegrationService = Depends(get_integration_service)
):
    """Get connected accounts for an integration"""
    try:
        accounts = await service.get_integration_accounts(current_user, integration_id)
        return [ConnectedAccountResponse(**account) for account in accounts]
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Plaid-specific endpoints
@router.post("/plaid/link-token")
async def create_plaid_link_token(
    request: PlaidLinkTokenRequest,
    current_user: str = Depends(get_current_user)
):
    """Create a Plaid Link token for user authentication"""
    try:
        async with PlaidIntegration() as plaid:
            result = await plaid.create_link_token(
                user_id=request.user_id or current_user,
                webhook_url=request.webhook_url
            )
            return result
    except ExternalServiceError as e:
        raise HTTPException(status_code=502, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/plaid/exchange-token")
async def exchange_plaid_public_token(
    public_token: str,
    current_user: str = Depends(get_current_user)
):
    """Exchange Plaid public token for access token"""
    try:
        async with PlaidIntegration() as plaid:
            result = await plaid.exchange_public_token(public_token)
            return result
    except ExternalServiceError as e:
        raise HTTPException(status_code=502, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# SnapTrade-specific endpoints
@router.post("/snaptrade/register")
async def register_snaptrade_user(
    request: SnapTradeRegisterRequest,
    current_user: str = Depends(get_current_user)
):
    """Register a new SnapTrade user"""
    try:
        async with SnapTradeIntegration() as snaptrade:
            result = await snaptrade.register_user(request.user_id or current_user)
            return result
    except ExternalServiceError as e:
        raise HTTPException(status_code=502, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/snaptrade/brokerages")
async def get_supported_brokerages(
    current_user: str = Depends(get_current_user)
):
    """Get list of supported brokerages"""
    try:
        async with SnapTradeIntegration() as snaptrade:
            result = await snaptrade.get_brokerages()
            return result
    except ExternalServiceError as e:
        raise HTTPException(status_code=502, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/snaptrade/connect")
async def initiate_snaptrade_connection(
    request: SnapTradeConnectionRequest,
    user_secret: str,
    current_user: str = Depends(get_current_user)
):
    """Initiate OAuth connection to a brokerage via SnapTrade"""
    try:
        async with SnapTradeIntegration() as snaptrade:
            result = await snaptrade.initiate_connection(
                credentials={'user_secret': user_secret},
                brokerage_id=request.brokerage_id,
                redirect_uri=request.redirect_uri
            )
            return result
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except ExternalServiceError as e:
        raise HTTPException(status_code=502, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
