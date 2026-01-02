from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class StrategyType(str, Enum):
    """Strategy type enumeration"""
    PREDEFINED = "PREDEFINED"
    CUSTOM = "CUSTOM"
    AI_GENERATED = "AI_GENERATED"


class ScheduleType(str, Enum):
    """Schedule type for custom strategies"""
    INTERVAL = "INTERVAL"
    CRON = "CRON"
    MANUAL = "MANUAL"


class ExecutionType(str, Enum):
    """Execution type for custom strategies"""
    HOST = "HOST"
    CLOUD = "CLOUD"
    LOCAL = "LOCAL"


class StrategyCreateRequest(BaseModel):
    """Request for creating a new strategy"""
    name: str = Field(..., min_length=1, max_length=100, description="Strategy name")
    description: Optional[str] = Field("", max_length=1000, description="Strategy description")
    scan_criteria: Optional[Dict[str, Any]] = Field(None, description="Scanning criteria configuration")
    default_stop_loss_pct: float = Field(0.20, ge=0, le=1, description="Default stop loss percentage")
    default_take_profit_pct: float = Field(0.50, ge=0, le=5, description="Default take profit percentage")
    notifications_enabled: bool = Field(True, description="Enable notifications for this strategy")
    strategy_type: StrategyType = Field(StrategyType.PREDEFINED, description="Type of strategy")
    
    @validator('name')
    def normalize_name(cls, v):
        return v.strip().title()


class StrategyUpdateRequest(BaseModel):
    """Request for updating an existing strategy"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Strategy name")
    description: Optional[str] = Field(None, max_length=1000, description="Strategy description")
    scan_criteria: Optional[Dict[str, Any]] = Field(None, description="Scanning criteria configuration")
    default_stop_loss_pct: Optional[float] = Field(None, ge=0, le=1, description="Default stop loss percentage")
    default_take_profit_pct: Optional[float] = Field(None, ge=0, le=5, description="Default take profit percentage")
    notifications_enabled: Optional[bool] = Field(None, description="Enable notifications for this strategy")
    
    @validator('name')
    def normalize_name(cls, v):
        return v.strip().title() if v else None


class StrategyResponse(BaseModel):
    """Response model for strategy data"""
    id: int
    name: str
    description: Optional[str] = None
    scan_criteria: Optional[Dict[str, Any]] = None
    default_stop_loss_pct: float
    default_take_profit_pct: float
    notifications_enabled: bool
    strategy_type: StrategyType
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Computed fields
    trade_count: Optional[int] = None
    win_rate: Optional[float] = None
    total_pnl: Optional[float] = None
    
    class Config:
        from_attributes = True


class CustomStrategyCreateRequest(BaseModel):
    """Request for creating a custom strategy (Python script)"""
    name: str = Field(..., min_length=1, max_length=100, description="Strategy name")
    code: str = Field(..., min_length=1, description="Python code for the strategy")
    schedule_type: ScheduleType = Field(ScheduleType.INTERVAL, description="Schedule type")
    schedule_value: str = Field("60", description="Schedule value (interval seconds or cron expression)")
    execution_type: ExecutionType = Field(ExecutionType.HOST, description="Execution environment")
    targets: Optional[str] = Field(None, description="Target tickers or criteria")
    description: Optional[str] = Field("", max_length=1000, description="Strategy description")
    
    @validator('name')
    def normalize_name(cls, v):
        return v.strip().title()


class CustomStrategyUpdateRequest(BaseModel):
    """Request for updating a custom strategy"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Strategy name")
    code: Optional[str] = Field(None, min_length=1, description="Python code for the strategy")
    schedule_type: Optional[ScheduleType] = Field(None, description="Schedule type")
    schedule_value: Optional[str] = Field(None, description="Schedule value")
    execution_type: Optional[ExecutionType] = Field(None, description="Execution environment")
    targets: Optional[str] = Field(None, description="Target tickers or criteria")
    description: Optional[str] = Field(None, max_length=1000, description="Strategy description")
    is_active: Optional[bool] = Field(None, description="Whether the strategy is active")
    
    @validator('name')
    def normalize_name(cls, v):
        return v.strip().title() if v else None


class CustomStrategyResponse(BaseModel):
    """Response model for custom strategy data"""
    id: int
    name: str
    code: str
    schedule_type: ScheduleType
    schedule_value: str
    execution_type: ExecutionType
    is_active: bool
    targets: Optional[str] = None
    description: Optional[str] = None
    last_run: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Computed fields
    execution_count: Optional[int] = None
    success_rate: Optional[float] = None
    avg_trades_per_run: Optional[float] = None
    
    class Config:
        from_attributes = True


class StrategyListRequest(BaseModel):
    """Request for listing strategies with filters"""
    strategy_type: Optional[StrategyType] = Field(None, description="Filter by strategy type")
    is_active: Optional[bool] = Field(None, description="Filter by active status (for custom strategies)")
    notifications_enabled: Optional[bool] = Field(None, description="Filter by notification status")
    limit: Optional[int] = Field(None, ge=1, le=1000, description="Limit number of results")
    offset: Optional[int] = Field(None, ge=0, le=10000, description="Offset for pagination")


class StrategyStatsResponse(BaseModel):
    """Response model for strategy statistics"""
    total_strategies: int = Field(..., ge=0, description="Total number of strategies")
    active_strategies: int = Field(..., ge=0, description="Number of active strategies")
    custom_strategies: int = Field(..., ge=0, description="Number of custom strategies")
    predefined_strategies: int = Field(..., ge=0, description="Number of predefined strategies")
    strategies_with_trades: int = Field(..., ge=0, description="Strategies that have generated trades")
    avg_win_rate: Optional[float] = Field(None, description="Average win rate across all strategies")
    total_strategy_pnl: Optional[float] = Field(None, description="Total P&L from all strategies")


class StrategyExecutionRequest(BaseModel):
    """Request for executing a custom strategy"""
    strategy_id: int = Field(..., description="Custom strategy ID")
    dry_run: bool = Field(False, description="Run in dry-run mode (no actual trades)")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Override parameters for execution")


class StrategyExecutionResponse(BaseModel):
    """Response model for strategy execution"""
    execution_id: int
    strategy_id: int
    status: str
    output: Optional[str] = None
    trades_generated: int
    execution_time: datetime
    dry_run: bool
    error_message: Optional[str] = None


class StrategyPerformanceResponse(BaseModel):
    """Response model for strategy performance analysis"""
    strategy_id: int
    strategy_name: str
    period: str
    total_trades: int
    win_rate: float
    total_pnl: float
    avg_trade_pnl: Optional[float] = None
    max_consecutive_wins: int
    max_consecutive_losses: int
    sharpe_ratio: Optional[float] = None
    max_drawdown: Optional[float] = None


class StrategyBacktestRequest(BaseModel):
    """Request for backtesting a strategy"""
    strategy_id: int
    start_date: datetime
    end_date: datetime
    initial_capital: float = Field(10000, ge=1000, description="Initial capital for backtest")
    commission: float = Field(1.0, ge=0, le=10, description="Commission per trade")
    slippage: float = Field(0.1, ge=0, le=5, description="Slippage per trade")


class StrategyBacktestResponse(BaseModel):
    """Response model for strategy backtest results"""
    strategy_id: int
    strategy_name: str
    period: str
    initial_capital: float
    final_capital: float
    total_return: float
    total_return_pct: float
    max_drawdown: float
    max_drawdown_pct: float
    sharpe_ratio: Optional[float] = None
    trades_count: int
    wins: int
    losses: int
    win_rate: float
    avg_win: Optional[float] = None
    avg_loss: Optional[float] = None
    profit_factor: Optional[float] = None
    daily_returns: List[float] = []


class StrategyLogResponse(BaseModel):
    """Response model for strategy execution logs"""
    id: int
    strategy_id: int
    timestamp: datetime
    status: str
    output: Optional[str] = None
    trades_generated: int
    execution_time_ms: Optional[int] = None
    error_details: Optional[str] = None
    
    class Config:
        from_attributes = True


class StrategyBatchRequest(BaseModel):
    """Request for batch strategy operations"""
    strategy_ids: List[int] = Field(..., min_items=1, max_items=100, description="List of strategy IDs")
    action: str = Field(..., description="Action to perform (activate, deactivate, delete)")


class StrategyRecommendationRequest(BaseModel):
    """Request for AI strategy recommendations"""
    risk_tolerance: str = Field("medium", description="Risk tolerance level (low, medium, high)")
    time_horizon: str = Field("medium", description="Trading time horizon (short, medium, long)")
    preferred_sectors: Optional[List[str]] = Field(None, description="Preferred market sectors")
    max_strategies: int = Field(5, ge=1, le=20, description="Maximum number of recommendations")


class StrategyRecommendationResponse(BaseModel):
    """Response model for strategy recommendations"""
    recommendations: List[Dict[str, Any]]
    analysis_summary: str
    confidence_score: float
    generated_at: datetime
