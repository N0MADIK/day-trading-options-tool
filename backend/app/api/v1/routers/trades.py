from fastapi import APIRouter, Depends, HTTPException, Query, Body
from typing import List, Optional

from app.services.trade_service import TradeService
from app.repositories.sqlalchemy.trade_repo import SQLAlchemyTradeRepository
from app.infrastructure.db import get_async_session
from app.schemas.trades import (
    TradeCreateRequest, TradeUpdateRequest, TradeCloseRequest,
    TradeListRequest, TradeStatsResponse, TradePerformanceResponse,
    TradeBatchRequest, TradeBatchUpdateRequest, TradeAnalysisRequest,
    TradeAnalysisResponse
)
from app.domain.errors import NotFoundError, ConflictError, ValidationError

router = APIRouter(prefix="/trades", tags=["trades"])

# Dependency for trade service
async def get_trade_service() -> TradeService:
    """Get trade service with repository"""
    session = await get_async_session()
    repository = SQLAlchemyTradeRepository(session)
    return TradeService(repository)


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
