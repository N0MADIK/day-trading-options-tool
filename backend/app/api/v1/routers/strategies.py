from fastapi import APIRouter, Depends, HTTPException, Query, Body
from typing import List, Optional

from app.services.strategy_service import (
    StrategyService, CustomStrategyService, StrategyAnalyticsService
)
from app.repositories.sqlalchemy.strategy_repo import (
    SQLAlchemyStrategyRepository, SQLAlchemyCustomStrategyRepository,
    SQLAlchemyStrategyAnalyticsRepository
)
from app.infrastructure.db import get_async_session
from app.schemas.strategies import (
    StrategyCreateRequest, StrategyUpdateRequest, StrategyType,
    CustomStrategyCreateRequest, CustomStrategyUpdateRequest,
    ScheduleType, ExecutionType, StrategyListRequest,
    StrategyStatsResponse, StrategyExecutionRequest,
    StrategyPerformanceResponse, StrategyBacktestRequest,
    StrategyBacktestResponse, StrategyBatchRequest,
    StrategyRecommendationRequest, StrategyRecommendationResponse
)
from app.domain.errors import NotFoundError, ConflictError, ValidationError

# Create routers for different strategy types
router = APIRouter(prefix="/strategies", tags=["strategies"])

custom_router = APIRouter(prefix="/custom", tags=["custom-strategies"])
analytics_router = APIRouter(prefix="/analytics", tags=["strategy-analytics"])

# Dependencies for services
async def get_strategy_service() -> StrategyService:
    """Get strategy service with repository"""
    session = await get_async_session()
    strategy_repo = SQLAlchemyStrategyRepository(session)
    custom_strategy_repo = SQLAlchemyCustomStrategyRepository(session)
    analytics_repo = SQLAlchemyStrategyAnalyticsRepository(session)
    return StrategyService(strategy_repo, custom_strategy_repo, analytics_repo)

async def get_custom_strategy_service() -> CustomStrategyService:
    """Get custom strategy service with repository"""
    session = await get_async_session()
    repository = SQLAlchemyCustomStrategyRepository(session)
    return CustomStrategyService(repository)

async def get_analytics_service() -> StrategyAnalyticsService:
    """Get analytics service with repository"""
    session = await get_async_session()
    repository = SQLAlchemyStrategyAnalyticsRepository(session)
    return StrategyAnalyticsService(repository)


# Standard Strategy Endpoints
@router.post("/", response_model=dict)
async def create_strategy(
    strategy_data: StrategyCreateRequest,
    service: StrategyService = Depends(get_strategy_service)
):
    """Create a new strategy"""
    try:
        return await service.create_strategy(strategy_data)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[dict])
async def list_strategies(
    strategy_type: Optional[StrategyType] = Query(None, description="Filter by strategy type"),
    notifications_enabled: Optional[bool] = Query(None, description="Filter by notification status"),
    limit: Optional[int] = Query(None, ge=1, le=1000, description="Limit number of results"),
    offset: Optional[int] = Query(None, ge=0, le=10000, description="Offset for pagination"),
    service: StrategyService = Depends(get_strategy_service)
):
    """List strategies with optional filters"""
    try:
        request = StrategyListRequest(
            strategy_type=strategy_type,
            notifications_enabled=notifications_enabled,
            limit=limit,
            offset=offset
        )
        return await service.list_strategies(request)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{strategy_id}", response_model=dict)
async def get_strategy(
    strategy_id: int,
    service: StrategyService = Depends(get_strategy_service)
):
    """Get a single strategy by ID"""
    try:
        return await service.get_strategy_by_id(strategy_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{strategy_id}", response_model=dict)
async def update_strategy(
    strategy_id: int,
    updates: StrategyUpdateRequest,
    service: StrategyService = Depends(get_strategy_service)
):
    """Update a strategy"""
    try:
        return await service.update_strategy(strategy_id, updates)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{strategy_id}", response_model=dict)
async def delete_strategy(
    strategy_id: int,
    service: StrategyService = Depends(get_strategy_service)
):
    """Delete a strategy"""
    try:
        return await service.delete_strategy(strategy_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/summary", response_model=StrategyStatsResponse)
async def get_strategy_statistics(
    service: StrategyService = Depends(get_strategy_service)
):
    """Get comprehensive strategy statistics"""
    try:
        return await service.get_strategy_statistics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search", response_model=List[dict])
async def search_strategies(
    q: str = Query(..., min_length=2, description="Search query (name or description)"),
    service: StrategyService = Depends(get_strategy_service)
):
    """Search strategies by name or description"""
    try:
        return await service.search_strategies(q)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Custom Strategy Endpoints
@custom_router.post("/", response_model=dict)
async def create_custom_strategy(
    strategy_data: CustomStrategyCreateRequest,
    service: CustomStrategyService = Depends(get_custom_strategy_service)
):
    """Create a new custom strategy"""
    try:
        return await service.create_custom_strategy(strategy_data)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@custom_router.get("/", response_model=List[dict])
async def list_custom_strategies(
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    execution_type: Optional[ExecutionType] = Query(None, description="Filter by execution type"),
    limit: Optional[int] = Query(None, ge=1, le=1000, description="Limit number of results"),
    offset: Optional[int] = Query(None, ge=0, le=10000, description="Offset for pagination"),
    service: CustomStrategyService = Depends(get_custom_strategy_service)
):
    """List custom strategies with optional filters"""
    try:
        return await service.list_custom_strategies(
            is_active=is_active,
            execution_type=execution_type,
            limit=limit,
            offset=offset
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@custom_router.get("/{strategy_id}", response_model=dict)
async def get_custom_strategy(
    strategy_id: int,
    service: CustomStrategyService = Depends(get_custom_strategy_service)
):
    """Get a single custom strategy by ID"""
    try:
        return await service.get_custom_strategy_by_id(strategy_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@custom_router.put("/{strategy_id}", response_model=dict)
async def update_custom_strategy(
    strategy_id: int,
    updates: CustomStrategyUpdateRequest,
    service: CustomStrategyService = Depends(get_custom_strategy_service)
):
    """Update a custom strategy"""
    try:
        return await service.update_custom_strategy(strategy_id, updates)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@custom_router.delete("/{strategy_id}", response_model=dict)
async def delete_custom_strategy(
    strategy_id: int,
    service: CustomStrategyService = Depends(get_custom_strategy_service)
):
    """Delete a custom strategy"""
    try:
        return await service.delete_custom_strategy(strategy_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@custom_router.post("/{strategy_id}/execute", response_model=dict)
async def execute_custom_strategy(
    strategy_id: int,
    execution_data: StrategyExecutionRequest,
    service: CustomStrategyService = Depends(get_custom_strategy_service)
):
    """Execute a custom strategy"""
    try:
        execution_data.strategy_id = strategy_id  # Ensure ID matches
        return await service.execute_custom_strategy(execution_data)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@custom_router.get("/{strategy_id}/logs", response_model=List[dict])
async def get_strategy_logs(
    strategy_id: int,
    limit: Optional[int] = Query(None, ge=1, le=1000, description="Limit number of results"),
    offset: Optional[int] = Query(None, ge=0, le=10000, description="Offset for pagination"),
    service: CustomStrategyService = Depends(get_custom_strategy_service)
):
    """Get execution logs for a custom strategy"""
    try:
        return await service.get_strategy_logs(
            strategy_id=strategy_id,
            limit=limit,
            offset=offset
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@custom_router.post("/{strategy_id}/toggle", response_model=dict)
async def toggle_strategy_activation(
    strategy_id: int,
    is_active: bool = Body(..., description="Activate or deactivate strategy"),
    service: CustomStrategyService = Depends(get_custom_strategy_service)
):
    """Activate or deactivate a custom strategy"""
    try:
        return await service.toggle_strategy_activation(strategy_id, is_active)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@custom_router.get("/scheduled", response_model=List[dict])
async def get_scheduled_strategies(
    service: CustomStrategyService = Depends(get_custom_strategy_service)
):
    """Get all active scheduled strategies"""
    try:
        return await service.get_scheduled_strategies()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@custom_router.put("/batch/update", response_model=dict)
async def batch_update_custom_strategies(
    batch_data: StrategyBatchRequest,
    service: CustomStrategyService = Depends(get_custom_strategy_service)
):
    """Update multiple custom strategies at once"""
    try:
        return await service.batch_update_custom_strategies(batch_data)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@custom_router.delete("/batch/delete", response_model=dict)
async def batch_delete_custom_strategies(
    batch_data: StrategyBatchRequest,
    service: CustomStrategyService = Depends(get_custom_strategy_service)
):
    """Delete multiple custom strategies at once"""
    try:
        return await service.batch_delete_custom_strategies(batch_data)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Analytics Endpoints
@analytics_router.get("/performance/{strategy_id}", response_model=StrategyPerformanceResponse)
async def get_strategy_performance(
    strategy_id: int,
    period: str = Query("3mo", description="Analysis period (1mo, 3mo, 6mo, 1y)"),
    service: StrategyAnalyticsService = Depends(get_analytics_service)
):
    """Get performance metrics for a specific strategy"""
    try:
        return await service.get_strategy_performance(strategy_id, period)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@analytics_router.post("/backtest", response_model=StrategyBacktestResponse)
async def backtest_strategy(
    request: StrategyBacktestRequest,
    service: StrategyAnalyticsService = Depends(get_analytics_service)
):
    """Run backtest for a strategy"""
    try:
        return await service.backtest_strategy(request)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@analytics_router.post("/compare", response_model=dict)
async def compare_strategies(
    strategy_ids: List[int] = Body(..., description="List of strategy IDs to compare"),
    period: str = Query("3mo", description="Analysis period (1mo, 3mo, 6mo, 1y)"),
    service: StrategyAnalyticsService = Depends(get_analytics_service)
):
    """Compare performance of multiple strategies"""
    try:
        return await service.compare_strategies(strategy_ids, period)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@analytics_router.post("/recommendations", response_model=StrategyRecommendationResponse)
async def get_strategy_recommendations(
    request: StrategyRecommendationRequest,
    service: StrategyAnalyticsService = Depends(get_analytics_service)
):
    """Get AI-powered strategy recommendations"""
    try:
        return await service.get_strategy_recommendations(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Include sub-routers
router.include_router(custom_router)
router.include_router(analytics_router)
