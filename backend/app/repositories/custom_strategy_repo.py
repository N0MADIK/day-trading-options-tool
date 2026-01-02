from typing import Protocol, List, Optional, Dict, Any
from datetime import datetime

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


class CustomStrategyRepository(Protocol):
    """Repository interface for custom strategy operations"""
    
    async def create_custom_strategy(self, strategy_data: CustomStrategyCreateRequest) -> int:
        """Create a new custom strategy and return its ID"""
        ...
    
    async def get_custom_strategy_by_id(self, strategy_id: int) -> Optional[Dict[str, Any]]:
        """Get a single custom strategy by ID"""
        ...
    
    async def get_all_custom_strategies(self, request: CustomStrategyListRequest) -> List[Dict[str, Any]]:
        """Get all custom strategies with optional filters"""
        ...
    
    async def update_custom_strategy(self, strategy_id: int, updates: CustomStrategyUpdateRequest) -> bool:
        """Update a custom strategy"""
        ...
    
    async def delete_custom_strategy(self, strategy_id: int) -> bool:
        """Delete a custom strategy"""
        ...
    
    async def toggle_strategy_active(self, strategy_id: int) -> bool:
        """Toggle strategy active status"""
        ...
    
    async def search_custom_strategies(self, query: str) -> List[Dict[str, Any]]:
        """Search custom strategies by name or description"""
        ...
    
    async def get_strategies_by_execution_type(self, execution_type: StrategyExecutionType) -> List[Dict[str, Any]]:
        """Get strategies by execution type"""
        ...
    
    async def get_strategies_by_schedule_type(self, schedule_type: StrategyScheduleType) -> List[Dict[str, Any]]:
        """Get strategies by schedule type"""
        ...
    
    async def get_strategies_by_tags(self, tags: List[str]) -> List[Dict[str, Any]]:
        """Get strategies by tags"""
        ...


class StrategyExecutionRepository(Protocol):
    """Repository interface for strategy execution operations"""
    
    async def execute_strategy(self, execution_request: StrategyExecutionRequest) -> StrategyExecutionResponse:
        """Execute a strategy"""
        ...
    
    async def get_execution_by_id(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get a single strategy execution by ID"""
        ...
    
    async def get_executions_by_strategy(self, strategy_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """Get all executions for a strategy"""
        ...
    
    async def get_all_executions(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Get all strategy executions with pagination"""
        ...
    
    async def update_execution_result(self, execution_id: str, result: StrategyPerformanceUpdateRequest) -> bool:
        """Update execution results"""
        ...
    
    async def cancel_execution(self, execution_id: str) -> bool:
        """Cancel a running execution"""
        ...
    
    async def get_running_executions(self) -> List[Dict[str, Any]]:
        """Get all currently running executions"""
        ...
    
    async def cleanup_old_executions(self, days_old: int = 30) -> int:
        """Clean up old execution records"""
        ...


class StrategyLogRepository(Protocol):
    """Repository interface for strategy log operations"""
    
    async def create_strategy_log(self, log_data: StrategyLogCreateRequest) -> int:
        """Create a new strategy log entry"""
        ...
    
    async def get_strategy_logs(self, request: StrategyLogListRequest) -> List[Dict[str, Any]]:
        """Get strategy logs with optional filters"""
        ...
    
    async def get_logs_by_execution(self, execution_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all logs for a specific execution"""
        ...
    
    async def cleanup_old_logs(self, days_old: int = 90) -> int:
        """Clean up old log entries"""
        ...
    
    async def get_log_statistics(self, strategy_id: int, days: int = 30) -> Dict[str, Any]:
        """Get log statistics for a strategy"""
        ...


class StrategyPerformanceRepository(Protocol):
    """Repository interface for strategy performance operations"""
    
    async def get_strategy_performance(self, strategy_id: int, period_days: int = 30) -> Optional[StrategyPerformanceResponse]:
        """Get strategy performance metrics"""
        ...
    
    async def update_strategy_performance(self, performance_data: StrategyPerformanceUpdateRequest) -> bool:
        """Update strategy performance data"""
        ...
    
    async def get_all_strategy_performance(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get performance data for all strategies"""
        ...
    
    async def get_performance_trends(self, strategy_id: int, days: int = 90) -> Dict[str, Any]:
        """Get performance trends over time"""
        ...
    
    async def get_strategy_rankings(self, metric: str = "total_return", period_days: int = 30) -> List[Dict[str, Any]]:
        """Get strategy rankings by performance metric"""
        ...


class StrategyTemplateRepository(Protocol):
    """Repository interface for strategy template operations"""
    
    async def create_strategy_template(self, template_data: StrategyTemplateCreateRequest) -> int:
        """Create a new strategy template and return its ID"""
        ...
    
    async def get_template_by_id(self, template_id: int) -> Optional[Dict[str, Any]]:
        """Get a single strategy template by ID"""
        ...
    
    async def get_all_templates(self, request: StrategyTemplateListRequest) -> List[Dict[str, Any]]:
        """Get all strategy templates with optional filters"""
        ...
    
    async def update_template(self, template_id: int, updates: Dict[str, Any]) -> bool:
        """Update a strategy template"""
        ...
    
    async def delete_template(self, template_id: int) -> bool:
        """Delete a strategy template"""
        ...
    
    async def get_public_templates(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get all public strategy templates"""
        ...
    
    async def get_templates_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get templates by category"""
        ...
    
    async def search_templates(self, query: str) -> List[Dict[str, Any]]:
        """Search templates by name, description, or tags"""
        ...
    
    async def get_popular_templates(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get most popular templates by usage count"""
        ...
    
    async def rate_template(self, template_id: int, user_id: str, rating: float) -> bool:
        """Rate a strategy template"""
        ...


class StrategyBacktestRepository(Protocol):
    """Repository interface for strategy backtesting operations"""
    
    async def run_backtest(self, backtest_request: BacktestRequest) -> BacktestResponse:
        """Run a strategy backtest"""
        ...
    
    async def get_backtest_by_id(self, backtest_id: str) -> Optional[Dict[str, Any]]:
        """Get a single backtest result by ID"""
        ...
    
    async def get_backtests_by_strategy(self, strategy_id: int, limit: int = 20) -> List[Dict[str, Any]]:
        """Get all backtests for a strategy"""
        ...
    
    async def get_all_backtests(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Get all backtest results with pagination"""
        ...
    
    async def compare_backtests(self, backtest_ids: List[str]) -> Dict[str, Any]:
        """Compare multiple backtest results"""
        ...
    
    async def delete_backtest(self, backtest_id: str) -> bool:
        """Delete a backtest result"""
        ...


class StrategySignalRepository(Protocol):
    """Repository interface for strategy signal operations"""
    
    async def create_strategy_signal(self, signal_data: StrategySignalCreateRequest) -> int:
        """Create a new strategy signal"""
        ...
    
    async def get_signal_by_id(self, signal_id: int) -> Optional[Dict[str, Any]]:
        """Get a single strategy signal by ID"""
        ...
    
    async def get_signals_by_strategy(self, request: StrategySignalListRequest) -> List[Dict[str, Any]]:
        """Get signals for a strategy with filters"""
        ...
    
    async def get_signals_by_symbol(self, symbol: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get all signals for a symbol"""
        ...
    
    async def get_all_signals(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Get all strategy signals with pagination"""
        ...
    
    async def update_signal_executed(self, signal_id: int, executed_at: datetime, execution_details: Optional[Dict[str, Any]] = None) -> bool:
        """Mark a signal as executed"""
        ...
    
    async def cleanup_old_signals(self, days_old: int = 30) -> int:
        """Clean up old signals"""
        ...
    
    async def get_signal_statistics(self, strategy_id: int, days: int = 30) -> Dict[str, Any]:
        """Get signal statistics for a strategy"""
        ...


class StrategyValidationRepository(Protocol):
    """Repository interface for strategy validation operations"""
    
    async def validate_strategy_code(self, validation_request: StrategyValidationRequest) -> StrategyValidationResponse:
        """Validate strategy code"""
        ...
    
    async def validate_strategy_syntax(self, code: str) -> Dict[str, Any]:
        """Validate Python syntax only"""
        ...
    
    async def validate_strategy_security(self, code: str) -> Dict[str, Any]:
        """Validate code for security issues"""
        ...
    
    async def validate_strategy_dependencies(self, code: str) -> Dict[str, Any]:
        """Validate strategy dependencies"""
        ...
    
    async def simulate_strategy_execution(self, code: str, parameters: Dict[str, Any], duration_seconds: int = 30) -> Dict[str, Any]:
        """Simulate strategy execution for validation"""
        ...


class StrategySchedulerRepository(Protocol):
    """Repository interface for strategy scheduling operations"""
    
    async def schedule_strategy(self, strategy_id: int, schedule_type: StrategyScheduleType, schedule_value: str) -> bool:
        """Schedule a strategy for execution"""
        ...
    
    async def unschedule_strategy(self, strategy_id: int) -> bool:
        """Unschedule a strategy"""
        ...
    
    async def get_scheduled_strategies(self) -> List[Dict[str, Any]]:
        """Get all scheduled strategies"""
        ...
    
    async def get_next_run_time(self, strategy_id: int) -> Optional[datetime]:
        """Get next scheduled run time for a strategy"""
        ...
    
    async def update_schedule(self, strategy_id: int, schedule_type: StrategyScheduleType, schedule_value: str) -> bool:
        """Update strategy schedule"""
        ...
    
    async def get_schedule_history(self, strategy_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """Get schedule history for a strategy"""
        ...


class CustomStrategyBatchRepository(Protocol):
    """Repository interface for batch strategy operations"""
    
    async def batch_update_strategies(self, strategy_ids: List[int], updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update multiple strategies at once"""
        ...
    
    async def batch_delete_strategies(self, strategy_ids: List[int]) -> Dict[str, Any]:
        """Delete multiple strategies at once"""
        ...
    
    async def batch_execute_strategies(self, strategy_ids: List[int], parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute multiple strategies at once"""
        ...
    
    async def batch_toggle_strategies(self, strategy_ids: List[int], active: bool) -> Dict[str, Any]:
        """Toggle active status for multiple strategies"""
        ...
    
    async def get_strategies_summary(self, strategy_ids: List[int]) -> Dict[str, Any]:
        """Get summary information for multiple strategies"""
        ...


class CustomStrategyAnalyticsRepository(Protocol):
    """Repository interface for custom strategy analytics"""
    
    async def get_execution_analytics(self, strategy_id: int, period_days: int = 30) -> Dict[str, Any]:
        """Get execution analytics for a strategy"""
        ...
    
    async def get_signal_analytics(self, strategy_id: int, period_days: int = 30) -> Dict[str, Any]:
        """Get signal analytics for a strategy"""
        ...
    
    async def get_performance_comparison(self, strategy_ids: List[int], period_days: int = 30) -> Dict[str, Any]:
        """Compare performance of multiple strategies"""
        ...
    
    async def get_strategy_health_metrics(self, strategy_id: int) -> Dict[str, Any]:
        """Get health metrics for a strategy"""
        ...
    
    async def get_usage_statistics(self, period_days: int = 30) -> Dict[str, Any]:
        """Get overall strategy usage statistics"""
        ...
    
    async def get_error_analysis(self, strategy_id: int, period_days: int = 30) -> Dict[str, Any]:
        """Get error analysis for a strategy"""
        ...
    
    async def get_optimization_suggestions(self, strategy_id: int) -> Dict[str, Any]:
        """Get optimization suggestions for a strategy"""
        ...
