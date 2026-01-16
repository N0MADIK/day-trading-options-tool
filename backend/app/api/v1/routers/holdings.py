"""Holdings API router - Simple delegator to personal finance holdings"""
from fastapi import APIRouter, Depends, Query
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db import get_async_session
from app.core.deps import get_current_user
from app.api.v1.routers.personal_finance import get_personal_finance_service, PersonalFinanceService
from app.schemas.personal_finance import HoldingListRequest

router = APIRouter(prefix="/holdings", tags=["holdings"])


@router.get("/", response_model=dict)
async def list_user_holdings(
    account_id: Optional[str] = Query(None, description="Filter by account ID"),
    current_user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    List holdings for the current user's connected accounts.
    Delegates to personal_finance.holdings_router.
    """
    service = await get_personal_finance_service()
    
    # Convert account_id from string to int if provided
    account_id_int = int(account_id) if account_id else None
    
    request = HoldingListRequest(
        account_id=account_id_int,
        security_id=None,
        currency=None,
        limit=1000,
        offset=0
    )
    
    return await service.list_holdings(request)
