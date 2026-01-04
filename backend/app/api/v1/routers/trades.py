from fastapi import APIRouter, Depends, HTTPException, Query, Body
from typing import List, Optional

from app.services.trade_service import TradeService
from app.services.trade_payment_service import TradePaymentService
from app.repositories.sqlalchemy.trade_repo import SQLAlchemyTradeRepository
from app.infrastructure.db import get_async_session
from app.schemas.trades import (
    TradeCreateRequest, TradeUpdateRequest, TradeCloseRequest,
    TradeListRequest, TradeStatsResponse, TradePerformanceResponse,
    TradeBatchRequest, TradeBatchUpdateRequest, TradeAnalysisRequest,
    TradeAnalysisResponse, TradePaymentRequest, TradePaymentResponse
)
from app.domain.errors import NotFoundError, ConflictError, ValidationError

router = APIRouter(prefix="/trades", tags=["trades"])

# Dependency for trade service
async def get_trade_service() -> TradeService:
    """Get trade service with repository"""
    session = await get_async_session()
    repository = SQLAlchemyTradeRepository(session)
    return TradeService(repository)


# Dependency for trade payment service
async def get_trade_payment_service() -> TradePaymentService:
    """Get trade payment service with personal finance service"""
    from app.services.personal_finance_service import PersonalFinanceService
    from app.repositories.sqlalchemy.personal_finance_repo import (
        SQLAlchemyInstitutionRepository, SQLAlchemyConnectionRepository,
        SQLAlchemyAccountRepository, SQLAlchemySecurityRepository,
        SQLAlchemyHoldingRepository, SQLAlchemyTransactionRepository,
        SQLAlchemySyncJobRepository, SQLAlchemyFileImportRepository,
        SQLAlchemyPersonalFinanceAnalyticsRepository,
        SQLAlchemyPersonalFinanceIntegrationRepository
    )
    
    session = await get_async_session()
    institution_repo = SQLAlchemyInstitutionRepository(session)
    connection_repo = SQLAlchemyConnectionRepository(session)
    account_repo = SQLAlchemyAccountRepository(session)
    security_repo = SQLAlchemySecurityRepository(session)
    holding_repo = SQLAlchemyHoldingRepository(session)
    transaction_repo = SQLAlchemyTransactionRepository(session)
    sync_job_repo = SQLAlchemySyncJobRepository(session)
    file_import_repo = SQLAlchemyFileImportRepository(session)
    analytics_repo = SQLAlchemyPersonalFinanceAnalyticsRepository(session)
    integration_repo = SQLAlchemyPersonalFinanceIntegrationRepository(session)
    
    pf_service = PersonalFinanceService(
        institution_repo, connection_repo, account_repo, security_repo, holding_repo,
        transaction_repo, sync_job_repo, file_import_repo, analytics_repo, integration_repo
    )
    
    return TradePaymentService(pf_service)


@router.post("/", response_model=dict)
async def create_trade(
    trade_data: TradeCreateRequest,
    service: TradeService = Depends(get_trade_service)
):
    """Create a new trade"""
    try:
        return await service.create_trade(trade_data)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[dict])
async def list_trades(
    status: Optional[str] = Query(None, description="Filter by status (OPEN, CLOSED_WIN, CLOSED_LOSS)"),
    strategy_id: Optional[int] = Query(None, description="Filter by strategy ID"),
    ticker: Optional[str] = Query(None, description="Filter by ticker"),
    limit: Optional[int] = Query(None, ge=1, le=1000, description="Limit number of results"),
    offset: Optional[int] = Query(None, ge=0, le=10000, description="Offset for pagination"),
    service: TradeService = Depends(get_trade_service)
):
    """List trades with optional filters"""
    try:
        request = TradeListRequest(
            status=status,
            strategy_id=strategy_id,
            ticker=ticker,
            limit=limit,
            offset=offset
        )
        return await service.list_trades(request)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/open", response_model=List[dict])
async def get_open_trades(
    service: TradeService = Depends(get_trade_service)
):
    """Get all open trades"""
    try:
        return await service.get_open_trades()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{trade_id}", response_model=dict)
async def get_trade(
    trade_id: int,
    service: TradeService = Depends(get_trade_service)
):
    """Get a single trade by ID"""
    try:
        return await service.get_trade_by_id(trade_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{trade_id}", response_model=dict)
async def update_trade(
    trade_id: int,
    updates: TradeUpdateRequest,
    service: TradeService = Depends(get_trade_service)
):
    """Update a trade"""
    try:
        return await service.update_trade(trade_id, updates)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{trade_id}/close", response_model=dict)
async def close_trade(
    trade_id: int,
    close_data: TradeCloseRequest,
    service: TradeService = Depends(get_trade_service)
):
    """Close a trade and calculate P&L"""
    try:
        return await service.close_trade(trade_id, close_data)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=e.message)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{trade_id}", response_model=dict)
async def delete_trade(
    trade_id: int,
    service: TradeService = Depends(get_trade_service)
):
    """Delete a trade"""
    try:
        return await service.delete_trade(trade_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/summary", response_model=TradeStatsResponse)
async def get_trade_statistics(
    service: TradeService = Depends(get_trade_service)
):
    """Get comprehensive trade statistics"""
    try:
        return await service.get_trade_statistics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ticker/{ticker}", response_model=List[dict])
async def get_trades_by_ticker(
    ticker: str,
    service: TradeService = Depends(get_trade_service)
):
    """Get all trades for a specific ticker"""
    try:
        return await service.get_trades_by_ticker(ticker)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/strategy/{strategy_id}", response_model=List[dict])
async def get_trades_by_strategy(
    strategy_id: int,
    service: TradeService = Depends(get_trade_service)
):
    """Get all trades for a specific strategy"""
    try:
        return await service.get_trades_by_strategy(strategy_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/batch/update", response_model=dict)
async def batch_update_trades(
    batch_data: TradeBatchUpdateRequest,
    service: TradeService = Depends(get_trade_service)
):
    """Update multiple trades at once"""
    try:
        return await service.batch_update_trades(batch_data)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch/close", response_model=dict)
async def batch_close_trades(
    trade_ids: List[int] = Body(...),
    exit_prices: List[float] = Body(...),
    service: TradeService = Depends(get_trade_service)
):
    """Close multiple trades at once"""
    try:
        return await service.batch_close_trades(trade_ids, exit_prices)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/batch/delete", response_model=dict)
async def batch_delete_trades(
    batch_data: TradeBatchRequest,
    service: TradeService = Depends(get_trade_service)
):
    """Delete multiple trades at once"""
    try:
        return await service.batch_delete_trades(batch_data)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance/{trade_id}", response_model=TradePerformanceResponse)
async def get_trade_performance(
    trade_id: int,
    service: TradeService = Depends(get_trade_service)
):
    """Get detailed performance metrics for a specific trade"""
    try:
        return await service.get_trade_performance_details(trade_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analysis/performance", response_model=TradeAnalysisResponse)
async def get_performance_analysis(
    period: str = Query("3mo", description="Analysis period (1mo, 3mo, 6mo, 1y, all)"),
    group_by: str = Query("month", description="Group results by (day, week, month, quarter)"),
    strategy_id: Optional[int] = Query(None, description="Filter by strategy ID"),
    service: TradeService = Depends(get_trade_service)
):
    """Get detailed trade performance analysis"""
    try:
        request = TradeAnalysisRequest(
            period=period,
            group_by=group_by,
            strategy_id=strategy_id
        )
        return await service.get_trade_performance_analysis(request)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search", response_model=List[dict])
async def search_trades(
    q: str = Query(..., min_length=2, description="Search query (contract symbol or notes)"),
    service: TradeService = Depends(get_trade_service)
):
    """Search trades by contract symbol or notes"""
    try:
        return await service.search_trades(q)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/risk/metrics", response_model=dict)
async def get_risk_metrics(
    service: TradeService = Depends(get_trade_service)
):
    """Get risk metrics for open trades"""
    try:
        return await service.get_risk_metrics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/payment-analysis", response_model=TradePaymentResponse)
async def analyze_trade_payment(
    payment_request: TradePaymentRequest,
    service: TradePaymentService = Depends(get_trade_payment_service)
):
    """
    Analyze how to pay for a trade using available cash or selling assets with tax implications
    
    This endpoint determines the optimal way to fund a trade by:
    1. Checking if available cash can cover the trade cost
    2. If cash is insufficient, calculating which assets to sell to minimize tax impact
    3. Computing capital gains taxes based on holding periods (long-term vs short-term)
    4. Providing detailed breakdown of asset sales and tax implications
    
    **Tax Logic:**
    - Long-term capital gains (held > 365 days): 15% tax rate
    - Short-term capital gains (held ≤ 365 days): 25% tax rate
    - No tax on losses (only profits are taxed)
    - Assets are sold in tax-efficient order to minimize overall tax burden
    
    **Payment Strategies:**
    - `use_cash`: Direct cash payment when sufficient funds available
    - `sell_assets`: Liquidate assets when cash insufficient but portfolio value adequate
    - `insufficient_funds`: Even selling all assets won't cover the trade cost
    
    **Request Body:**
    ```json
    {
      "user_id": 1,
      "symbol": "NVDA",
      "shares": 50,
      "price": 800.0,
      "trade_type": "buy"
    }
    ```
    
    **Response:**
    ```json
    {
      "success": true,
      "trade": {
        "symbol": "NVDA",
        "shares": 50,
        "price": 800.0,
        "total_cost": 40000.0,
        "trade_type": "BUY"
      },
      "payment_analysis": {
        "action": "sell_assets",
        "cash_used": 40000.0,
        "assets_sold": [
          {
            "symbol": "AAPL",
            "shares_sold": 20,
            "sale_price_per_share": 150.0,
            "gross_proceeds": 3000.0,
            "taxes": 450.0,
            "net_proceeds": 2550.0,
            "purchase_date": "2023-01-01",
            "days_held": 1098,
            "tax_rate": "0.15 (long-term)"
          }
        ],
        "taxes_paid": 450.0,
        "total_sold_value": 3000.0,
        "remaining_cash": 2550.0,
        "message": "Trade paid for by selling assets. Total taxes: $450.00, Remaining cash: $2,550.00"
      }
    }
    ```
    
    Args:
        payment_request: Trade details and user ID for payment analysis
        
    Returns:
        Comprehensive payment analysis including asset sales, taxes, and remaining cash
        
    Raises:
        HTTPException: For validation errors, missing user data, or service errors
    """
    try:
        result = await service.analyze_trade_payment(
            user_id=payment_request.user_id,
            trade_info={
                "symbol": payment_request.symbol,
                "shares": payment_request.shares,
                "price": payment_request.price,
                "trade_type": payment_request.trade_type
            }
        )
        
        return TradePaymentResponse(
            success=result["success"],
            trade=result["trade"],
            payment_analysis=result["payment_analysis"],
            message=result["payment_analysis"].get("message")
        )
        
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
