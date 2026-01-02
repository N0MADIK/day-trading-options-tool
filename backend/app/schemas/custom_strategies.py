from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class StrategyExecutionType(str, Enum):
    """Strategy execution type enumeration"""
    PYTHON_SCRIPT = "PYTHON_SCRIPT"
    DOCKER_CONTAINER = "DOCKER_CONTAINER"
    WEBHOOK = "WEBHOOK"
    NATIVE = "NATIVE"


class StrategyScheduleType(str, Enum):
    """Strategy schedule type enumeration"""
    INTERVAL = "INTERVAL"
    CRON = "CRON"
    MANUAL = "MANUAL"
    EVENT_DRIVEN = "EVENT_DRIVEN"


class StrategyStatus(str, Enum):
    """Strategy status enumeration"""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    RUNNING = "RUNNING"
    ERROR = "ERROR"
    PAUSED = "PAUSED"


class StrategyLogLevel(str, Enum):
    """Strategy log level enumeration"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


# Custom Strategy Models
class CustomStrategyCreateRequest(BaseModel):
    """Request for creating a custom strategy"""
    name: str = Field(..., min_length=1, max_length=200, description="Strategy name")
    description: Optional[str] = Field(None, max_length=1000, description="Strategy description")
    code: str = Field(..., min_length=10, max_length=50000, description="Strategy code")
    execution_type: StrategyExecutionType = Field(..., description="Execution type")
    schedule_type: StrategyScheduleType = Field(..., description="Schedule type")
    schedule_value: str = Field(..., min_length=1, max_length=100, description="Schedule value")
    is_active: bool = Field(True, description="Whether strategy is active")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Strategy parameters")
    environment_vars: Optional[Dict[str, str]] = Field(None, description="Environment variables")
    timeout_seconds: Optional[int] = Field(300, ge=1, le=3600, description="Execution timeout in seconds")
    retry_count: Optional[int] = Field(3, ge=0, le=10, description="Number of retries on failure")
    tags: Optional[List[str]] = Field(None, description="Strategy tags")
    
    @validator('name')
    def normalize_name(cls, v):
        return v.strip()
    
    @validator('code')
    def validate_code(cls, v):
        # Basic Python syntax validation
        try:
            compile(v, '<string>', 'exec')
        except SyntaxError as e:
            raise ValueError(f"Invalid Python code: {e}")
        return v
    
    @validator('schedule_value')
    def validate_schedule_value(cls, v, values):
        schedule_type = values.get('schedule_type')
        if schedule_type == StrategyScheduleType.INTERVAL:
            try:
                minutes = int(v)
                if minutes < 1 or minutes > 10080:  # Max 1 week
                    raise ValueError("Interval minutes must be between 1 and 10080")
            except ValueError:
                raise ValueError("Interval schedule value must be a valid integer in minutes")
        elif schedule_type == StrategyScheduleType.CRON:
            # Basic cron validation (min hour day month dow)
            parts = v.split()
            if len(parts) != 5:
                raise ValueError("Cron expression must have 5 parts: minute hour day month dow")
        return v


class CustomStrategyUpdateRequest(BaseModel):
    """Request for updating a custom strategy"""
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="Strategy name")
    description: Optional[str] = Field(None, max_length=1000, description="Strategy description")
    code: Optional[str] = Field(None, min_length=10, max_length=50000, description="Strategy code")
    execution_type: Optional[StrategyExecutionType] = Field(None, description="Execution type")
    schedule_type: Optional[StrategyScheduleType] = Field(None, description="Schedule type")
    schedule_value: Optional[str] = Field(None, min_length=1, max_length=100, description="Schedule value")
    is_active: Optional[bool] = Field(None, description="Whether strategy is active")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Strategy parameters")
    environment_vars: Optional[Dict[str, str]] = Field(None, description="Environment variables")
    timeout_seconds: Optional[int] = Field(None, ge=1, le=3600, description="Execution timeout in seconds")
    retry_count: Optional[int] = Field(None, ge=0, le=10, description="Number of retries on failure")
    tags: Optional[List[str]] = Field(None, description="Strategy tags")


class CustomStrategyResponse(BaseModel):
    """Response model for custom strategy data"""
    id: int
    name: str
    description: Optional[str] = None
    code: str
    execution_type: StrategyExecutionType
    schedule_type: StrategyScheduleType
    schedule_value: str
    is_active: bool
    parameters: Optional[Dict[str, Any]] = None
    environment_vars: Optional[Dict[str, str]] = None
    timeout_seconds: int
    retry_count: int
    tags: Optional[List[str]] = None
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Strategy Execution Models
class StrategyExecutionRequest(BaseModel):
    """Request for executing a strategy"""
    strategy_id: int = Field(..., description="Strategy ID")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Override parameters")
    dry_run: bool = Field(False, description="Whether to run in dry-run mode")
    execution_context: Optional[Dict[str, Any]] = Field(None, description="Execution context data")


class StrategyExecutionResponse(BaseModel):
    """Response model for strategy execution results"""
    execution_id: str
    strategy_id: int
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    output: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    logs: List[str] = Field(default=[])
    trades_generated: int = Field(default=0)
    signals_generated: int = Field(default=0)
    dry_run: bool


# Strategy Log Models
class StrategyLogCreateRequest(BaseModel):
    """Request for creating a strategy log entry"""
    strategy_id: int = Field(..., description="Strategy ID")
    execution_id: Optional[str] = Field(None, description="Execution ID")
    log_level: StrategyLogLevel = Field(..., description="Log level")
    message: str = Field(..., min_length=1, max_length=2000, description="Log message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional log details")
    timestamp: Optional[datetime] = Field(None, description="Log timestamp")


class StrategyLogResponse(BaseModel):
    """Response model for strategy log data"""
    id: int
    strategy_id: int
    execution_id: Optional[str] = None
    log_level: StrategyLogLevel
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime
    
    class Config:
        from_attributes = True


# Strategy Performance Models
class StrategyPerformanceResponse(BaseModel):
    """Response model for strategy performance"""
    strategy_id: int
    strategy_name: str
    total_executions: int
    successful_executions: int
    failed_executions: int
    success_rate: float
    avg_execution_time_seconds: float
    total_trades_generated: int
    total_signals_generated: int
    last_execution_at: Optional[datetime] = None
    performance_trend: Dict[str, float] = Field(default={})
    profitability_metrics: Optional[Dict[str, float]] = Field(None)


class StrategyPerformanceUpdateRequest(BaseModel):
    """Request for updating strategy performance"""
    execution_id: str = Field(..., description="Execution ID")
    trades_generated: int = Field(0, description="Number of trades generated")
    signals_generated: int = Field(0, description="Number of signals generated")
    execution_time_seconds: float = Field(..., description="Execution time in seconds")
    success: bool = Field(True, description="Whether execution was successful")
    error_message: Optional[str] = Field(None, description="Error message if failed")


# Strategy Template Models
class StrategyTemplateCreateRequest(BaseModel):
    """Request for creating a strategy template"""
    name: str = Field(..., min_length=1, max_length=200, description="Template name")
    description: Optional[str] = Field(None, max_length=1000, description="Template description")
    category: str = Field(..., min_length=1, max_length=100, description="Template category")
    code_template: str = Field(..., min_length=10, max_length=50000, description="Code template")
    default_parameters: Optional[Dict[str, Any]] = Field(None, description="Default parameters")
    required_parameters: List[str] = Field(default=[], description="Required parameter names")
    optional_parameters: List[str] = Field(default=[], description="Optional parameter names")
    tags: Optional[List[str]] = Field(None, description="Template tags")
    is_public: bool = Field(False, description="Whether template is public")
    version: str = Field("1.0.0", description="Template version")


class StrategyTemplateResponse(BaseModel):
    """Response model for strategy template data"""
    id: int
    name: str
    description: Optional[str] = None
    category: str
    code_template: str
    default_parameters: Optional[Dict[str, Any]] = None
    required_parameters: List[str]
    optional_parameters: List[str]
    tags: Optional[List[str]] = None
    is_public: bool
    version: str
    usage_count: int = Field(default=0)
    rating: Optional[float] = Field(None)
    created_by: Optional[str] = Field(None)
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Strategy Backtest Models
class BacktestRequest(BaseModel):
    """Request for backtesting a strategy"""
    strategy_id: Optional[int] = Field(None, description="Strategy ID to backtest")
    code: Optional[str] = Field(None, min_length=10, max_length=50000, description="Strategy code to backtest")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Strategy parameters")
    start_date: datetime = Field(..., description="Backtest start date")
    end_date: datetime = Field(..., description="Backtest end date")
    initial_capital: float = Field(10000.0, ge=100.0, description="Initial capital for backtest")
    commission_rate: float = Field(0.001, ge=0.0, le=0.1, description="Commission rate")
    slippage_rate: float = Field(0.0001, ge=0.0, le=0.01, description="Slippage rate")
    benchmark_symbol: Optional[str] = Field(None, description="Benchmark symbol for comparison")


class BacktestResponse(BaseModel):
    """Response model for backtest results"""
    backtest_id: str
    strategy_id: Optional[int] = None
    start_date: datetime
    end_date: datetime
    initial_capital: float
    final_capital: float
    total_return: float
    total_return_percentage: float
    annualized_return: float
    max_drawdown: float
    max_drawdown_percentage: float
    sharpe_ratio: Optional[float] = None
    win_rate: float
    profit_factor: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    avg_trade_return: float
    benchmark_return: Optional[float] = None
    benchmark_return_percentage: Optional[float] = None
    equity_curve: List[Dict[str, Any]] = Field(default=[])
    trade_history: List[Dict[str, Any]] = Field(default=[])
    performance_metrics: Dict[str, float] = Field(default={})
    created_at: datetime


# Strategy Signal Models
class StrategySignalCreateRequest(BaseModel):
    """Request for creating a strategy signal"""
    strategy_id: int = Field(..., description="Strategy ID")
    symbol: str = Field(..., min_length=1, max_length=20, description="Symbol")
    signal_type: str = Field(..., min_length=1, max_length=50, description="Signal type")
    action: str = Field(..., regex="^(BUY|SELL|HOLD)$", description="Action (BUY/SELL/HOLD)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence level")
    price: Optional[float] = Field(None, description="Signal price")
    target_price: Optional[float] = Field(None, description="Target price")
    stop_price: Optional[float] = Field(None, description="Stop price")
    quantity: Optional[float] = Field(None, description="Suggested quantity")
    expiration_date: Optional[datetime] = Field(None, description="Signal expiration")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional signal metadata")


class StrategySignalResponse(BaseModel):
    """Response model for strategy signal data"""
    id: int
    strategy_id: int
    symbol: str
    signal_type: str
    action: str
    confidence: float
    price: Optional[float] = None
    target_price: Optional[float] = None
    stop_price: Optional[float] = None
    quantity: Optional[float] = None
    expiration_date: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    is_executed: bool = Field(default=False)
    executed_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# List and Filter Models
class CustomStrategyListRequest(BaseModel):
    """Request for listing custom strategies"""
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    execution_type: Optional[StrategyExecutionType] = Field(None, description="Filter by execution type")
    schedule_type: Optional[StrategyScheduleType] = Field(None, description="Filter by schedule type")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")
    search: Optional[str] = Field(None, min_length=1, max_length=100, description="Search term")
    limit: Optional[int] = Field(None, ge=1, le=1000, description="Limit number of results")
    offset: Optional[int] = Field(None, ge=0, le=10000, description="Offset for pagination")


class StrategyLogListRequest(BaseModel):
    """Request for listing strategy logs"""
    strategy_id: Optional[int] = Field(None, description="Filter by strategy ID")
    execution_id: Optional[str] = Field(None, description="Filter by execution ID")
    log_level: Optional[StrategyLogLevel] = Field(None, description="Filter by log level")
    start_time: Optional[datetime] = Field(None, description="Filter by start time")
    end_time: Optional[datetime] = Field(None, description="Filter by end time")
    search: Optional[str] = Field(None, min_length=1, max_length=100, description="Search term in message")
    limit: Optional[int] = Field(None, ge=1, le=1000, description="Limit number of results")
    offset: Optional[int] = Field(None, ge=0, le=10000, description="Offset for pagination")


class StrategySignalListRequest(BaseModel):
    """Request for listing strategy signals"""
    strategy_id: Optional[int] = Field(None, description="Filter by strategy ID")
    symbol: Optional[str] = Field(None, min_length=1, max_length=20, description="Filter by symbol")
    signal_type: Optional[str] = Field(None, description="Filter by signal type")
    action: Optional[str] = Field(None, regex="^(BUY|SELL|HOLD)$", description="Filter by action")
    is_executed: Optional[bool] = Field(None, description="Filter by execution status")
    start_time: Optional[datetime] = Field(None, description="Filter by start time")
    end_time: Optional[datetime] = Field(None, description="Filter by end time")
    min_confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Filter by minimum confidence")
    limit: Optional[int] = Field(None, ge=1, le=1000, description="Limit number of results")
    offset: Optional[int] = Field(None, ge=0, le=10000, description="Offset for pagination")


class StrategyTemplateListRequest(BaseModel):
    """Request for listing strategy templates"""
    category: Optional[str] = Field(None, description="Filter by category")
    is_public: Optional[bool] = Field(None, description="Filter by public status")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")
    search: Optional[str] = Field(None, min_length=1, max_length=100, description="Search term")
    created_by: Optional[str] = Field(None, description="Filter by creator")
    min_rating: Optional[float] = Field(None, ge=0.0, le=5.0, description="Filter by minimum rating")
    limit: Optional[int] = Field(None, ge=1, le=1000, description="Limit number of results")
    offset: Optional[int] = Field(None, ge=0, le=10000, description="Offset for pagination")


# Batch Operations Models
class StrategyBatchRequest(BaseModel):
    """Request for batch strategy operations"""
    strategy_ids: List[int] = Field(..., min_items=1, max_items=100, description="List of strategy IDs")
    action: str = Field(..., regex="^(activate|deactivate|delete|run)$", description="Batch action")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Parameters for run action")


class StrategyBatchResponse(BaseModel):
    """Response model for batch strategy operations"""
    success_count: int
    error_count: int
    results: List[Dict[str, Any]] = Field(default=[])
    errors: List[str] = Field(default=[])


# Strategy Validation Models
class StrategyValidationRequest(BaseModel):
    """Request for validating strategy code"""
    code: str = Field(..., min_length=10, max_length=50000, description="Strategy code to validate")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Strategy parameters for validation")
    environment_vars: Optional[Dict[str, str]] = Field(None, description="Environment variables for validation")


class StrategyValidationResponse(BaseModel):
    """Response model for strategy validation results"""
    is_valid: bool
    syntax_errors: List[str] = Field(default=[])
    import_errors: List[str] = Field(default=[])
    runtime_errors: List[str] = Field(default=[])
    warnings: List[str] = Field(default=[])
    execution_time_ms: Optional[float] = None
    memory_usage_mb: Optional[float] = None
    security_issues: List[str] = Field(default=[])
    recommendations: List[str] = Field(default=[])
