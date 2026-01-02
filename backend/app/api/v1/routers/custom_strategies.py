from fastapi import APIRouter, Depends, HTTPException, Query, Body
from typing import List, Optional
import json

from app.services.custom_strategy_service import (
    CustomStrategyService, StrategySchedulerService, StrategyTemplateService,
    StrategyBacktestService, StrategyExecutionService
)
from app.repositories.sqlalchemy.custom_strategy_repo import (
    SQLAlchemyCustomStrategyRepository, SQLAlchemyStrategyExecutionRepository,
    SQLAlchemyStrategyLogRepository, SQLAlchemyStrategyPerformanceRepository,
    SQLAlchemyStrategyTemplateRepository, SQLAlchemyStrategyBacktestRepository,
    SQLAlchemyStrategySignalRepository, SQLAlchemyStrategyValidationRepository,
    SQLAlchemyStrategySchedulerRepository, SQLAlchemyCustomStrategyBatchRepository,
    SQLAlchemyCustomStrategyAnalyticsRepository
)
from app.infrastructure.db import get_async_session
from app.schemas.custom_strategies import (
    CustomStrategyCreateRequest, CustomStrategyUpdateRequest,
    StrategyExecutionRequest, StrategyExecutionResponse,
    StrategyLogCreateRequest, StrategyLogResponse,
    StrategyPerformanceResponse, StrategyPerformanceUpdateRequest,
    StrategyTemplateCreateRequest, StrategyTemplateResponse,
    BacktestRequest, BacktestResponse,
    StrategySignalCreateRequest, StrategySignalResponse,
    CustomStrategyListRequest, StrategyLogListRequest,
    StrategySignalListRequest, StrategyTemplateListRequest,
    StrategyBatchRequest, StrategyBatchResponse,
    StrategyValidationRequest, StrategyValidationResponse,
    StrategyExecutionType, StrategyScheduleType,
    StrategyStatus, StrategyLogLevel
)
from app.domain.errors import NotFoundError, ConflictError, ValidationError

# Create routers for different custom strategy modules
router = APIRouter(prefix="/custom-strategies", tags=["custom-strategies"])

strategies_router = APIRouter(prefix="/strategies", tags=["strategies"])
execution_router = APIRouter(prefix="/execution", tags=["strategy-execution"])
templates_router = APIRouter(prefix="/templates", tags=["strategy-templates"])
backtest_router = APIRouter(prefix="/backtest", tags=["strategy-backtest"])
signals_router = APIRouter(prefix="/signals", tags=["strategy-signals"])
validation_router = APIRouter(prefix="/validation", tags=["strategy-validation"])
scheduler_router = APIRouter(prefix="/scheduler", tags=["strategy-scheduler"])
batch_router = APIRouter(prefix="/batch", tags=["batch-operations"])
analytics_router = APIRouter(prefix="/analytics", tags=["strategy-analytics"])

# Dependencies for services
async def get_custom_strategy_service() -> CustomStrategyService:
    """Get custom strategy service with repository"""
    session = await get_async_session()
    strategy_repo = SQLAlchemyCustomStrategyRepository(session)
    execution_repo = SQLAlchemyStrategyExecutionRepository(session)
    log_repo = SQLAlchemyStrategyLogRepository(session)
    performance_repo = SQLAlchemyStrategyPerformanceRepository(session)
    template_repo = SQLAlchemyStrategyTemplateRepository(session)
    backtest_repo = SQLAlchemyStrategyBacktestRepository(session)
    signal_repo = SQLAlchemyStrategySignalRepository(session)
    validation_repo = SQLAlchemyStrategyValidationRepository(session)
    scheduler_repo = SQLAlchemyStrategySchedulerRepository(session)
    batch_repo = SQLAlchemyCustomStrategyBatchRepository(session)
    analytics_repo = SQLAlchemyCustomStrategyAnalyticsRepository(session)
    return CustomStrategyService(
        strategy_repo, execution_repo, log_repo, performance_repo, template_repo,
        backtest_repo, signal_repo, validation_repo, scheduler_repo, batch_repo, analytics_repo
    )

async def get_scheduler_service() -> StrategySchedulerService:
    """Get scheduler service with repository"""
    session = await get_async_session()
    scheduler_repo = SQLAlchemyStrategySchedulerRepository(session)
    return StrategySchedulerService(scheduler_repo)

async def get_template_service() -> StrategyTemplateService:
    """Get template service with repository"""
    session = await get_async_session()
    template_repo = SQLAlchemyStrategyTemplateRepository(session)
    return StrategyTemplateService(template_repo)

async def get_backtest_service() -> StrategyBacktestService:
    """Get backtest service with repository"""
    session = await get_async_session()
    backtest_repo = SQLAlchemyStrategyBacktestRepository(session)
    return StrategyBacktestService(backtest_repo)

# Strategy Management Endpoints
@strategies_router.post("/", response_model=dict)
async def create_custom_strategy(
    strategy_data: CustomStrategyCreateRequest,
    service: CustomStrategyService = Depends(get_custom_strategy_service)
):
    """Create a new custom strategy"""
    try:
        return await service.create_custom_strategy(strategy_data)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@strategies_router.get("/", response_model=dict)
async def list_custom_strategies(
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    execution_type: Optional[StrategyExecutionType] = Query(None, description="Filter by execution type"),
    schedule_type: Optional[StrategyScheduleType] = Query(None, description="Filter by schedule type"),
    tags: Optional[List[str]] = Query(None, description="Filter by tags"),
    search: Optional[str] = Query(None, min_length=2, description="Search term"),
    limit: Optional[int] = Query(None, ge=1, le=1000, description="Limit number of results"),
    offset: Optional[int] = Query(None, ge=0, le=10000, description="Offset for pagination"),
    service: CustomStrategyService = Depends(get_custom_strategy_service)
):
    """List custom strategies with optional filters"""
    try:
        request = CustomStrategyListRequest(
            is_active=is_active,
            execution_type=execution_type,
            schedule_type=schedule_type,
            tags=tags,
            search=search,
            limit=limit,
            offset=offset
        )
        return await service.list_custom_strategies(request)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@strategies_router.get("/{strategy_id}", response_model=dict)
async def get_custom_strategy_by_id(
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

@strategies_router.put("/{strategy_id}", response_model=dict)
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

@strategies_router.delete("/{strategy_id}", response_model=dict)
async def delete_custom_strategy(
    strategy_id: int,
    service: CustomStrategyService = Depends(get_custom_strategy_service)
):
    """Delete a custom strategy"""
    try:
        return await service.delete_custom_strategy(strategy_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@strategies_router.post("/{strategy_id}/toggle", response_model=dict)
async def toggle_strategy_active(
    strategy_id: int,
    service: CustomStrategyService = Depends(get_custom_strategy_service)
):
    """Toggle strategy active status"""
    try:
        return await service.toggle_strategy_active(strategy_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@strategies_router.get("/search", response_model=dict)
async def search_custom_strategies(
    q: str = Query(..., min_length=2, description="Search query"),
    service: CustomStrategyService = Depends(get_custom_strategy_service)
):
    """Search custom strategies by name or description"""
    try:
        return await service.search_custom_strategies(q)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@strategies_router.get("/execution-type/{execution_type}", response_model=dict)
async def get_strategies_by_execution_type(
    execution_type: StrategyExecutionType,
    service: CustomStrategyService = Depends(get_custom_strategy_service)
):
    """Get strategies by execution type"""
    try:
        strategies = await service.strategy_repo.get_strategies_by_execution_type(execution_type)
        
        return {
            "success": True,
            "strategies": strategies,
            "total_count": len(strategies)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@strategies_router.get("/schedule-type/{schedule_type}", response_model=dict)
async def get_strategies_by_schedule_type(
    schedule_type: StrategyScheduleType,
    service: CustomStrategyService = Depends(get_custom_strategy_service)
):
    """Get strategies by schedule type"""
    try:
        strategies = await service.strategy_repo.get_strategies_by_schedule_type(schedule_type)
        
        return {
            "success": True,
            "strategies": strategies,
            "total_count": len(strategies)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@strategies_router.get("/tags/{tags}", response_model=dict)
async def get_strategies_by_tags(
    tags: str = Query(..., description="Comma-separated tags"),
    service: CustomStrategyService = Depends(get_custom_strategy_service)
):
    """Get strategies by tags"""
    try:
        tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
        strategies = await service.strategy_repo.get_strategies_by_tags(tag_list)
        
        return {
            "success": True,
            "strategies": strategies,
            "total_count": len(strategies)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Strategy Execution Endpoints
@execution_router.post("/", response_model=dict)
async def execute_strategy(
    execution_request: StrategyExecutionRequest,
    service: CustomStrategyService = Depends(get_custom_strategy_service)
):
    """Execute a strategy"""
    try:
        return await service.execute_strategy(execution_request)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@execution_router.get("/{execution_id}", response_model=dict)
async def get_execution_by_id(
    execution_id: str,
    service: CustomStrategyService = Depends(get_custom_strategy_service)
):
    """Get a single strategy execution by ID"""
    try:
        return await service.get_execution_by_id(execution_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@execution_router.get("/strategy/{strategy_id}", response_model=dict)
async def get_executions_by_strategy(
    strategy_id: int,
    limit: int = Query(50, ge=1, le=1000, description="Limit number of results"),
    service: CustomStrategyService = Depends(get_custom_strategy_service)
):
    """Get all executions for a strategy"""
    try:
        return await service.get_executions_by_strategy(strategy_id, limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@execution_router.post("/{execution_id}/cancel", response_model=dict)
async def cancel_execution(
    execution_id: str,
    service: CustomStrategyService = Depends(get_custom_strategy_service)
):
    """Cancel a running execution"""
    try:
        return await service.cancel_execution(execution_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@execution_router.get("/running", response_model=dict)
async def get_running_executions(
    service: CustomStrategyService = Depends(get_custom_strategy_service)
):
    """Get all currently running executions"""
    try:
        executions = await service.execution_repo.get_running_executions()
        
        return {
            "success": True,
            "executions": executions,
            "total_count": len(executions)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Strategy Template Endpoints
@templates_router.post("/", response_model=dict)
async def create_strategy_template(
    template_data: StrategyTemplateCreateRequest,
    service: CustomStrategyService = Depends(get_custom_strategy_service)
):
    """Create a new strategy template"""
    try:
        return await service.create_strategy_template(template_data)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@templates_router.get("/", response_model=dict)
async def list_strategy_templates(
    category: Optional[str] = Query(None, description="Filter by category"),
    is_public: Optional[bool] = Query(None, description="Filter by public status"),
    tags: Optional[List[str]] = Query(None, description="Filter by tags"),
    search: Optional[str] = Query(None, min_length=2, description="Search term"),
    created_by: Optional[str] = Query(None, description="Filter by creator"),
    min_rating: Optional[float] = Query(None, ge=0.0, le=5.0, description="Filter by minimum rating"),
    limit: Optional[int] = Query(None, ge=1, le=1000, description="Limit number of results"),
    offset: Optional[int] = Query(None, ge=0, le=10000, description="Offset for pagination"),
    service: CustomStrategyService = Depends(get_custom_strategy_service)
):
    """List strategy templates with optional filters"""
    try:
        request = StrategyTemplateListRequest(
            category=category,
            is_public=is_public,
            tags=tags,
            search=search,
            created_by=created_by,
            min_rating=min_rating,
            limit=limit,
            offset=offset
        )
        return await service.list_strategy_templates(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@templates_router.get("/{template_id}", response_model=dict)
async def get_template_by_id(
    template_id: int,
    service: CustomStrategyService = Depends(get_custom_strategy_service)
):
    """Get a single strategy template by ID"""
    try:
        return await service.get_template_by_id(template_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@templates_router.get("/search", response_model=dict)
async def search_strategy_templates(
    q: str = Query(..., min_length=2, description="Search query"),
    service: CustomStrategyService = Depends(get_custom_strategy_service)
):
    """Search templates by name, description, or tags"""
    try:
        return await service.search_strategy_templates(q)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@templates_router.get("/public", response_model=dict)
async def get_public_templates(
    limit: int = Query(50, ge=1, le=100, description="Limit number of results"),
    service: StrategyTemplateService = Depends(get_template_service)
):
    """Get all public strategy templates"""
    try:
        return await service.get_public_templates(limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@templates_router.get("/category/{category}", response_model=dict)
async def get_templates_by_category(
    category: str,
    service: StrategyTemplateService = Depends(get_template_service)
):
    """Get templates by category"""
    try:
        return await service.get_templates_by_category(category)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@templates_router.get("/popular", response_model=dict)
async def get_popular_templates(
    limit: int = Query(20, ge=1, le=100, description="Limit number of results"),
    service: StrategyTemplateService = Depends(get_template_service)
):
    """Get most popular templates by usage count"""
    try:
        return await service.get_popular_templates(limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@templates_router.post("/{template_id}/rate", response_model=dict)
async def rate_template(
    template_id: int,
    user_id: str = Body(..., description="User ID"),
    rating: float = Body(..., ge=0.0, le=5.0, description="Rating from 0.0 to 5.0"),
    service: StrategyTemplateService = Depends(get_template_service)
):
    """Rate a strategy template"""
    try:
        return await service.rate_template(template_id, user_id, rating)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Strategy Backtest Endpoints
@backtest_router.post("/", response_model=dict)
async def run_backtest(
    backtest_request: BacktestRequest,
    service: CustomStrategyService = Depends(get_custom_strategy_service)
):
    """Run a strategy backtest"""
    try:
        return await service.run_backtest(backtest_request)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@backtest_router.get("/{backtest_id}", response_model=dict)
async def get_backtest_by_id(
    backtest_id: str,
    service: CustomStrategyService = Depends(get_custom_strategy_service)
):
    """Get a single backtest result by ID"""
    try:
        return await service.get_backtest_by_id(backtest_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@backtest_router.get("/strategy/{strategy_id}", response_model=dict)
async def get_backtests_by_strategy(
    strategy_id: int,
    limit: int = Query(20, ge=1, le=100, description="Limit number of results"),
    service: CustomStrategyService = Depends(get_custom_strategy_service)
):
    """Get all backtests for a strategy"""
    try:
        return await service.get_backtests_by_strategy(strategy_id, limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@backtest_router.post("/compare", response_model=dict)
async def compare_backtests(
    backtest_ids: List[str] = Body(..., description="List of backtest IDs to compare"),
    service: StrategyBacktestService = Depends(get_backtest_service)
):
    """Compare multiple backtest results"""
    try:
        return await service.compare_backtests(backtest_ids)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@backtest_router.delete("/{backtest_id}", response_model=dict)
async def delete_backtest(
    backtest_id: str,
    service: StrategyBacktestService = Depends(get_custom_strategy_service)
):
    """Delete a backtest result"""
    try:
        return await service.delete_backtest(backtest_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Strategy Signal Endpoints
@signals_router.post("/", response_model=dict)
async def create_strategy_signal(
    signal_data: StrategySignalCreateRequest,
    service: CustomStrategyService = Depends(get_custom_strategy_service)
):
    """Create a new strategy signal"""
    try:
        return await service.create_strategy_signal(signal_data)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@signals_router.get("/", response_model=dict)
async def get_signals_by_strategy(
    strategy_id: int,
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    signal_type: Optional[str] = Query(None, description="Filter by signal type"),
    action: Optional[str] = Query(None, regex="^(BUY|SELL|HOLD)$", description="Filter by action"),
    is_executed: Optional[bool] = Query(None, description="Filter by execution status"),
    start_time: Optional[datetime] = Query(None, description="Filter by start time"),
    end_time: Optional[datetime] = Query(None, description="Filter by end time"),
    min_confidence: Optional[float] = Query(None, ge=0.0, le=1.0, description="Filter by minimum confidence"),
    limit: Optional[int] = Query(None, ge=1, le=1000, description="Limit number of results"),
    offset: Optional[int] = Query(None, ge=0, le=10000, description="Offset for pagination"),
    service: CustomStrategyService = Depends(get_custom_strategy_service)
):
    """Get signals for a strategy with filters"""
    try:
        request = StrategySignalListRequest(
            strategy_id=strategy_id,
            symbol=symbol,
            signal_type=signal_type,
            action=action,
            is_executed=is_executed,
            start_time=start_time,
            end_time=end_time,
            min_confidence=min_confidence,
            limit=limit,
            offset=offset
        )
        return await service.get_signals_by_strategy(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@signals_router.get("/symbol/{symbol}", response_model=dict)
async def get_signals_by_symbol(
    symbol: str,
    limit: int = Query(50, ge=1, le=1000, description="Limit number of results"),
    service: CustomStrategyService = Depends(get_custom_strategy_service)
):
    """Get all signals for a symbol"""
    try:
        signals = await service.signal_repo.get_signals_by_symbol(symbol, limit)
        
        return {
            "success": True,
            "signals": signals,
            "total_count": len(signals)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@signals_router.get("/{signal_id}", response_model=dict)
async def get_signal_by_id(
    signal_id: int,
    service: CustomStrategyService = Depends(get_custom_strategy_service)
):
    """Get a single strategy signal by ID"""
    try:
        signal = await service.signal_repo.get_signal_by_id(signal_id)
        if not signal:
            raise HTTPException(status_code=404, detail="Signal not found")
        
        return {
            "success": True,
            "signal": signal
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@signals_router.put("/{signal_id}/execute", response_model=dict)
async def update_signal_executed(
    signal_id: int,
    executed_at: datetime = Body(..., description="Execution timestamp"),
    execution_details: Optional[Dict[str, Any]] = Body(None, description="Execution details"),
    service: CustomStrategyService = Depends(get_custom_strategy_service)
):
    """Mark a signal as executed"""
    try:
        return await service.update_signal_executed(signal_id, executed_at, execution_details)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Strategy Validation Endpoints
@validation_router.post("/validate", response_model=dict)
async def validate_strategy_code(
    validation_request: StrategyValidationRequest,
    service: CustomStrategyService = Depends(get_custom_strategy_service)
):
    """Validate strategy code"""
    try:
        return await service.validate_strategy_code(validation_request)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Batch Operations Endpoints
@batch_router.put("/strategies", response_model=dict)
async def batch_update_strategies(
    strategy_ids: List[int] = Body(..., min_items=1, max_items=100, description="List of strategy IDs"),
    updates: Dict[str, Any] = Body(None, description="Updates to apply"),
    service: CustomStrategyService = Depends(get_custom_strategy_service)
):
    """Update multiple strategies at once"""
    try:
        return await service.batch_update_strategies(strategy_ids, updates)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@batch_router.delete("/strategies", response_model=dict)
async def batch_delete_strategies(
    strategy_ids: List[int] = Body(..., min_items=1, max_items=100, description="List of strategy IDs"),
    service: CustomStrategyService = Depends(get_custom_strategy_service)
):
    """Delete multiple strategies at once"""
    try:
        return await service.batch_delete_strategies(strategy_ids)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@batch_router.post("/strategies/execute", response_model=dict)
async def batch_execute_strategies(
    strategy_ids: List[int] = Body(..., min_items=1, max_items=100, description="List of strategy IDs"),
    parameters: Optional[Dict[str, Any]] = Body(None, description="Parameters to apply"),
    service: CustomStrategyService = Depends(get_custom_strategy_service)
):
    """Execute multiple strategies at once"""
    try:
        return await service.batch_execute_strategies(strategy_ids, parameters)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@batch_router.put("/strategies/toggle", response_model=dict)
async def batch_toggle_strategies(
    strategy_ids: List[int] = Body(..., min_items=1, max_items=100, description="List of strategy IDs"),
    active: bool = Body(..., description="Active status to set"),
    service: CustomStrategyService = Depends(get_custom_strategy_service)
):
    """Toggle active status for multiple strategies"""
    try:
        return await service.batch_toggle_strategies(strategy_ids, active)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Analytics Endpoints
@analytics_router.get("/performance/{strategy_id}", response_model=dict)
async def get_strategy_performance(
    strategy_id: int,
    period_days: int = Query(30, ge=1, le=3650, description="Period in days"),
    service: CustomStrategyService = Depends(get_custom_strategy_service)
):
    """Get strategy performance metrics"""
    try:
        return await service.get_strategy_performance(strategy_id, period_days)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@analytics_router.get("/health/{strategy_id}", response_model=dict)
async def get_strategy_health_metrics(
    strategy_id: int,
    service: CustomStrategyService = Depends(get_custom_strategy_service)
):
    """Get health metrics for a strategy"""
    try:
        return await service.get_strategy_health_metrics(strategy_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@analytics_router.get("/usage-stats", response_model=dict)
async def get_usage_statistics(
    period_days: int = Query(30, ge=1, le=3650, description="Period in days"),
    service: CustomStrategyService = Depends(get_custom_strategy_service)
):
    """Get overall strategy usage statistics"""
    try:
        return await service.get_usage_statistics(period_days)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Scheduler Endpoints
@scheduler_router.get("/scheduled", response_model=dict)
async def get_scheduled_strategies(
    service: StrategySchedulerService = Depends(get_scheduler_service)
):
    """Get all scheduled strategies"""
    try:
        return await service.get_scheduled_strategies()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@scheduler_router.get("/next-runs", response_model=dict)
async def get_next_run_times(
    strategy_ids: List[int] = Query(..., description="List of strategy IDs"),
    service: StrategySchedulerService = Depends(get_scheduler_service)
):
    """Get next run times for multiple strategies"""
    try:
        return await service.get_next_run_times(strategy_ids)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Include sub-routers
router.include_router(strategies_router)
router.include_router(execution_router)
router.include_router(templates_router)
router.include_router(backtest_router)
router.include_router(signals_router)
router.include_router(validation_router)
router.include_router(batch_router)
router.include_router(analytics_router)
router.include_router(scheduler_router)
