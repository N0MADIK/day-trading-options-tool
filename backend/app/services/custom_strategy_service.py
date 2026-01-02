from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import asyncio
import uuid
import json

from app.repositories.custom_strategy_repo import (
    CustomStrategyRepository, StrategyExecutionRepository,
    StrategyLogRepository, StrategyPerformanceRepository,
    StrategyTemplateRepository, StrategyBacktestRepository,
    StrategySignalRepository, StrategyValidationRepository,
    StrategySchedulerRepository, CustomStrategyBatchRepository,
    CustomStrategyAnalyticsRepository
)
from app.repositories.sqlalchemy.custom_strategy_repo import (
    SQLAlchemyCustomStrategyRepository, SQLAlchemyStrategyExecutionRepository,
    SQLAlchemyStrategyLogRepository, SQLAlchemyStrategyPerformanceRepository,
    SQLAlchemyStrategyTemplateRepository, SQLAlchemyStrategyBacktestRepository,
    SQLAlchemyStrategySignalRepository, SQLAlchemyStrategyValidationRepository,
    SQLAlchemyStrategySchedulerRepository, SQLAlchemyCustomStrategyBatchRepository,
    SQLAlchemyCustomStrategyAnalyticsRepository
)
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


class CustomStrategyService:
    """Service for custom strategy management operations"""
    
    def __init__(
        self,
        strategy_repo: CustomStrategyRepository,
        execution_repo: StrategyExecutionRepository,
        log_repo: StrategyLogRepository,
        performance_repo: StrategyPerformanceRepository,
        template_repo: StrategyTemplateRepository,
        backtest_repo: StrategyBacktestRepository,
        signal_repo: StrategySignalRepository,
        validation_repo: StrategyValidationRepository,
        scheduler_repo: StrategySchedulerRepository,
        batch_repo: CustomStrategyBatchRepository,
        analytics_repo: CustomStrategyAnalyticsRepository
    ):
        self.strategy_repo = strategy_repo
        self.execution_repo = execution_repo
        self.log_repo = log_repo
        self.performance_repo = performance_repo
        self.template_repo = template_repo
        self.backtest_repo = backtest_repo
        self.signal_repo = signal_repo
        self.validation_repo = validation_repo
        self.scheduler_repo = scheduler_repo
        self.batch_repo = batch_repo
        self.analytics_repo = analytics_repo
    
    # Strategy Management
    async def create_custom_strategy(self, strategy_data: CustomStrategyCreateRequest) -> Dict[str, Any]:
        """Create a new custom strategy"""
        try:
            # Validate strategy code
            validation_result = await self.validation_repo.validate_strategy_code(
                StrategyValidationRequest(
                    code=strategy_data.code,
                    parameters=strategy_data.parameters,
                    environment_vars=strategy_data.environment_vars
                )
            )
            
            if not validation_result.is_valid:
                raise ValidationError(f"Strategy code validation failed: {validation_result.syntax_errors}")
            
            strategy_id = await self.strategy_repo.create_custom_strategy(strategy_data)
            
            # Schedule strategy if active
            if strategy_data.is_active:
                await self.scheduler_repo.schedule_strategy(
                    strategy_id, 
                    strategy_data.schedule_type, 
                    strategy_data.schedule_value
                )
            
            # Get created strategy
            strategy = await self.strategy_repo.get_custom_strategy_by_id(strategy_id)
            
            return {
                "success": True,
                "strategy_id": strategy_id,
                "strategy": strategy,
                "validation_result": validation_result
            }
            
        except Exception as e:
            raise e
    
    async def get_custom_strategy_by_id(self, strategy_id: int) -> Dict[str, Any]:
        """Get a single custom strategy by ID"""
        try:
            strategy = await self.strategy_repo.get_custom_strategy_by_id(strategy_id)
            
            if not strategy:
                raise NotFoundError(f"Custom strategy with ID {strategy_id} not found")
            
            return {
                "success": True,
                "strategy": strategy
            }
            
        except Exception as e:
            raise e
    
    async def list_custom_strategies(self, request: CustomStrategyListRequest) -> Dict[str, Any]:
        """List custom strategies with optional filters"""
        try:
            strategies = await self.strategy_repo.get_all_custom_strategies(request)
            
            return {
                "success": True,
                "strategies": strategies,
                "total_count": len(strategies)
            }
            
        except Exception as e:
            raise e
    
    async def update_custom_strategy(self, strategy_id: int, updates: CustomStrategyUpdateRequest) -> Dict[str, Any]:
        """Update a custom strategy"""
        try:
            # Validate code if provided
            if updates.code:
                validation_result = await self.validation_repo.validate_strategy_code(
                    StrategyValidationRequest(
                        code=updates.code,
                        parameters=updates.parameters,
                        environment_vars=updates.environment_vars
                    )
                )
                
                if not validation_result.is_valid:
                    raise ValidationError(f"Strategy code validation failed: {validation_result.syntax_errors}")
            
            success = await self.strategy_repo.update_custom_strategy(strategy_id, updates)
            
            if not success:
                raise NotFoundError(f"Custom strategy with ID {strategy_id} not found")
            
            # Update schedule if schedule changed
            if updates.schedule_type or updates.schedule_value:
                strategy = await self.strategy_repo.get_custom_strategy_by_id(strategy_id)
                if strategy:
                    await self.scheduler_repo.update_schedule(
                        strategy_id,
                        updates.schedule_type or strategy['schedule_type'],
                        updates.schedule_value or strategy['schedule_value']
                    )
            
            # Get updated strategy
            strategy = await self.strategy_repo.get_custom_strategy_by_id(strategy_id)
            
            return {
                "success": True,
                "strategy": strategy
            }
            
        except Exception as e:
            raise e
    
    async def delete_custom_strategy(self, strategy_id: int) -> Dict[str, Any]:
        """Delete a custom strategy"""
        try:
            success = await self.strategy_repo.delete_custom_strategy(strategy_id)
            
            if not success:
                raise NotFoundError(f"Custom strategy with ID {strategy_id} not found")
            
            # Unschedule strategy
            await self.scheduler_repo.unschedule_strategy(strategy_id)
            
            return {
                "success": True,
                "message": f"Custom strategy {strategy_id} deleted successfully"
            }
            
        except Exception as e:
            raise e
    
    async def toggle_strategy_active(self, strategy_id: int) -> Dict[str, Any]:
        """Toggle strategy active status"""
        try:
            success = await self.strategy_repo.toggle_strategy_active(strategy_id)
            
            if not success:
                raise NotFoundError(f"Custom strategy with ID {strategy_id} not found")
            
            # Get updated strategy
            strategy = await self.strategy_repo.get_custom_strategy_by_id(strategy_id)
            
            # Update schedule based on new active status
            if strategy['is_active']:
                await self.scheduler_repo.schedule_strategy(
                    strategy_id,
                    strategy['schedule_type'],
                    strategy['schedule_value']
                )
            else:
                await self.scheduler_repo.unschedule_strategy(strategy_id)
            
            return {
                "success": True,
                "strategy": strategy
            }
            
        except Exception as e:
            raise e
    
    async def search_custom_strategies(self, query: str) -> Dict[str, Any]:
        """Search custom strategies by name or description"""
        try:
            if not query or len(query.strip()) < 2:
                raise ValidationError("Search query must be at least 2 characters")
            
            strategies = await self.strategy_repo.search_custom_strategies(query.strip())
            
            return {
                "success": True,
                "strategies": strategies,
                "total_count": len(strategies)
            }
            
        except Exception as e:
            raise e
    
    # Strategy Execution
    async def execute_strategy(self, execution_request: StrategyExecutionRequest) -> Dict[str, Any]:
        """Execute a strategy"""
        try:
            # Validate strategy exists
            strategy = await self.strategy_repo.get_custom_strategy_by_id(execution_request.strategy_id)
            if not strategy:
                raise NotFoundError(f"Custom strategy with ID {execution_request.strategy_id} not found")
            
            # Execute strategy
            execution_result = await self.execution_repo.execute_strategy(execution_request)
            
            # Log execution
            await self.log_repo.create_strategy_log(
                StrategyLogCreateRequest(
                    strategy_id=execution_request.strategy_id,
                    execution_id=execution_result.execution_id,
                    log_level=StrategyLogLevel.INFO,
                    message=f"Strategy executed successfully",
                    details={"dry_run": execution_request.dry_run}
                )
            )
            
            # Update performance
            await self.performance_repo.update_strategy_performance(
                StrategyPerformanceUpdateRequest(
                    execution_id=execution_result.execution_id,
                    trades_generated=execution_result.trades_generated,
                    signals_generated=execution_result.signals_generated,
                    execution_time_seconds=execution_result.duration_seconds,
                    success=execution_result.status == "COMPLETED",
                    error_message=execution_result.error_message
                )
            )
            
            return {
                "success": True,
                "execution": execution_result
            }
            
        except Exception as e:
            raise e
    
    async def get_execution_by_id(self, execution_id: str) -> Dict[str, Any]:
        """Get a single strategy execution by ID"""
        try:
            execution = await self.execution_repo.get_execution_by_id(execution_id)
            
            if not execution:
                raise NotFoundError(f"Strategy execution with ID {execution_id} not found")
            
            return {
                "success": True,
                "execution": execution
            }
            
        except Exception as e:
            raise e
    
    async def get_executions_by_strategy(self, strategy_id: int, limit: int = 50) -> Dict[str, Any]:
        """Get all executions for a strategy"""
        try:
            executions = await self.execution_repo.get_executions_by_strategy(strategy_id, limit)
            
            return {
                "success": True,
                "executions": executions,
                "total_count": len(executions)
            }
            
        except Exception as e:
            raise e
    
    async def cancel_execution(self, execution_id: str) -> Dict[str, Any]:
        """Cancel a running execution"""
        try:
            success = await self.execution_repo.cancel_execution(execution_id)
            
            if not success:
                raise NotFoundError(f"Strategy execution with ID {execution_id} not found or not running")
            
            # Log cancellation
            await self.log_repo.create_strategy_log(
                StrategyLogCreateRequest(
                    strategy_id=0,  # We don't know the strategy ID from execution_id alone
                    execution_id=execution_id,
                    log_level=StrategyLogLevel.INFO,
                    message="Execution cancelled by user"
                )
            )
            
            return {
                "success": True,
                "message": f"Execution {execution_id} cancelled successfully"
            }
            
        except Exception as e:
            raise e
    
    # Strategy Templates
    async def create_strategy_template(self, template_data: StrategyTemplateCreateRequest) -> Dict[str, Any]:
        """Create a new strategy template"""
        try:
            template_id = await self.template_repo.create_strategy_template(template_data)
            
            # Get created template
            template = await self.template_repo.get_template_by_id(template_id)
            
            return {
                "success": True,
                "template_id": template_id,
                "template": template
            }
            
        except Exception as e:
            raise e
    
    async def get_template_by_id(self, template_id: int) -> Dict[str, Any]:
        """Get a single strategy template by ID"""
        try:
            template = await self.template_repo.get_template_by_id(template_id)
            
            if not template:
                raise NotFoundError(f"Strategy template with ID {template_id} not found")
            
            return {
                "success": True,
                "template": template
            }
            
        except Exception as e:
            raise e
    
    async def list_strategy_templates(self, request: StrategyTemplateListRequest) -> Dict[str, Any]:
        """List strategy templates with optional filters"""
        try:
            templates = await self.template_repo.get_all_templates(request)
            
            return {
                "success": True,
                "templates": templates,
                "total_count": len(templates)
            }
            
        except Exception as e:
            raise e
    
    async def search_strategy_templates(self, query: str) -> Dict[str, Any]:
        """Search templates by name, description, or tags"""
        try:
            if not query or len(query.strip()) < 2:
                raise ValidationError("Search query must be at least 2 characters")
            
            templates = await self.template_repo.search_templates(query.strip())
            
            return {
                "success": True,
                "templates": templates,
                "total_count": len(templates)
            }
            
        except Exception as e:
            raise e
    
    # Strategy Backtesting
    async def run_backtest(self, backtest_request: BacktestRequest) -> Dict[str, Any]:
        """Run a strategy backtest"""
        try:
            # Validate strategy exists or code provided
            if backtest_request.strategy_id:
                strategy = await self.strategy_repo.get_custom_strategy_by_id(backtest_request.strategy_id)
                if not strategy:
                    raise NotFoundError(f"Custom strategy with ID {backtest_request.strategy_id} not found")
            
            # Run backtest
            backtest_result = await self.backtest_repo.run_backtest(backtest_request)
            
            return {
                "success": True,
                "backtest": backtest_result
            }
            
        except Exception as e:
            raise e
    
    async def get_backtest_by_id(self, backtest_id: str) -> Dict[str, Any]:
        """Get a single backtest result by ID"""
        try:
            backtest = await self.backtest_repo.get_backtest_by_id(backtest_id)
            
            if not backtest:
                raise NotFoundError(f"Backtest with ID {backtest_id} not found")
            
            return {
                "success": True,
                "backtest": backtest
            }
            
        except Exception as e:
            raise e
    
    async def get_backtests_by_strategy(self, strategy_id: int, limit: int = 20) -> Dict[str, Any]:
        """Get all backtests for a strategy"""
        try:
            backtests = await self.backtest_repo.get_backtests_by_strategy(strategy_id, limit)
            
            return {
                "success": True,
                "backtests": backtests,
                "total_count": len(backtests)
            }
            
        except Exception as e:
            raise e
    
    # Strategy Signals
    async def create_strategy_signal(self, signal_data: StrategySignalCreateRequest) -> Dict[str, Any]:
        """Create a new strategy signal"""
        try:
            # Validate strategy exists
            strategy = await self.strategy_repo.get_custom_strategy_by_id(signal_data.strategy_id)
            if not strategy:
                raise NotFoundError(f"Custom strategy with ID {signal_data.strategy_id} not found")
            
            signal_id = await self.signal_repo.create_strategy_signal(signal_data)
            
            # Get created signal
            signal = await self.signal_repo.get_signal_by_id(signal_id)
            
            return {
                "success": True,
                "signal_id": signal_id,
                "signal": signal
            }
            
        except Exception as e:
            raise e
    
    async def get_signals_by_strategy(self, request: StrategySignalListRequest) -> Dict[str, Any]:
        """Get signals for a strategy with filters"""
        try:
            signals = await self.signal_repo.get_signals_by_strategy(request)
            
            return {
                "success": True,
                "signals": signals,
                "total_count": len(signals)
            }
            
        except Exception as e:
            raise e
    
    async def update_signal_executed(self, signal_id: int, executed_at: datetime, execution_details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Mark a signal as executed"""
        try:
            success = await self.signal_repo.update_signal_executed(signal_id, executed_at, execution_details)
            
            if not success:
                raise NotFoundError(f"Strategy signal with ID {signal_id} not found")
            
            return {
                "success": True,
                "message": f"Signal {signal_id} marked as executed"
            }
            
        except Exception as e:
            raise e
    
    # Strategy Validation
    async def validate_strategy_code(self, validation_request: StrategyValidationRequest) -> Dict[str, Any]:
        """Validate strategy code"""
        try:
            validation_result = await self.validation_repo.validate_strategy_code(validation_request)
            
            return {
                "success": True,
                "validation": validation_result
            }
            
        except Exception as e:
            raise e
    
    # Batch Operations
    async def batch_update_strategies(self, strategy_ids: List[int], updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update multiple strategies at once"""
        try:
            result = await self.batch_repo.batch_update_strategies(strategy_ids, updates)
            
            return {
                "success": True,
                "batch_result": result
            }
            
        except Exception as e:
            raise e
    
    async def batch_delete_strategies(self, strategy_ids: List[int]) -> Dict[str, Any]:
        """Delete multiple strategies at once"""
        try:
            result = await self.batch_repo.batch_delete_strategies(strategy_ids)
            
            # Unschedule all deleted strategies
            for strategy_id in strategy_ids:
                await self.scheduler_repo.unschedule_strategy(strategy_id)
            
            return {
                "success": True,
                "batch_result": result
            }
            
        except Exception as e:
            raise e
    
    async def batch_execute_strategies(self, strategy_ids: List[int], parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute multiple strategies at once"""
        try:
            result = await self.batch_repo.batch_execute_strategies(strategy_ids, parameters)
            
            return {
                "success": True,
                "batch_result": result
            }
            
        except Exception as e:
            raise e
    
    async def batch_toggle_strategies(self, strategy_ids: List[int], active: bool) -> Dict[str, Any]:
        """Toggle active status for multiple strategies"""
        try:
            result = await self.batch_repo.batch_toggle_strategies(strategy_ids, active)
            
            # Update schedules based on new active status
            for strategy_id in strategy_ids:
                if active:
                    strategy = await self.strategy_repo.get_custom_strategy_by_id(strategy_id)
                    if strategy:
                        await self.scheduler_repo.schedule_strategy(
                            strategy_id,
                            strategy['schedule_type'],
                            strategy['schedule_value']
                        )
                else:
                    await self.scheduler_repo.unschedule_strategy(strategy_id)
            
            return {
                "success": True,
                "batch_result": result
            }
            
        except Exception as e:
            raise e
    
    # Analytics
    async def get_strategy_performance(self, strategy_id: int, period_days: int = 30) -> Dict[str, Any]:
        """Get strategy performance metrics"""
        try:
            performance = await self.analytics_repo.get_execution_analytics(strategy_id, period_days)
            
            return {
                "success": True,
                "performance": performance
            }
            
        except Exception as e:
            raise e
    
    async def get_strategy_health_metrics(self, strategy_id: int) -> Dict[str, Any]:
        """Get health metrics for a strategy"""
        try:
            health = await self.analytics_repo.get_strategy_health_metrics(strategy_id)
            
            return {
                "success": True,
                "health_metrics": health
            }
            
        except Exception as e:
            raise e
    
    async def get_usage_statistics(self, period_days: int = 30) -> Dict[str, Any]:
        """Get overall strategy usage statistics"""
        try:
            stats = await self.analytics_repo.get_usage_statistics(period_days)
            
            return {
                "success": True,
                "usage_statistics": stats
            }
            
        except Exception as e:
            raise e


class StrategySchedulerService:
    """Service for strategy scheduling operations"""
    
    def __init__(self, scheduler_repo: StrategySchedulerRepository):
        self.scheduler_repo = scheduler_repo
    
    async def get_scheduled_strategies(self) -> Dict[str, Any]:
        """Get all scheduled strategies"""
        try:
            strategies = await self.scheduler_repo.get_scheduled_strategies()
            
            return {
                "success": True,
                "strategies": strategies,
                "total_count": len(strategies)
            }
            
        except Exception as e:
            raise e
    
    async def get_next_run_times(self, strategy_ids: List[int]) -> Dict[str, Any]:
        """Get next run times for multiple strategies"""
        try:
            run_times = {}
            for strategy_id in strategy_ids:
                next_run = await self.scheduler_repo.get_next_run_time(strategy_id)
                run_times[strategy_id] = next_run
            
            return {
                "success": True,
                "next_run_times": run_times
            }
            
        except Exception as e:
            raise e


class StrategyTemplateService:
    """Service for strategy template operations"""
    
    def __init__(self, template_repo: StrategyTemplateRepository):
        self.template_repo = template_repo
    
    async def get_public_templates(self, limit: int = 50) -> Dict[str, Any]:
        """Get all public strategy templates"""
        try:
            templates = await self.template_repo.get_public_templates(limit)
            
            return {
                "success": True,
                "templates": templates,
                "total_count": len(templates)
            }
            
        except Exception as e:
            raise e
    
    async def get_templates_by_category(self, category: str) -> Dict[str, Any]:
        """Get templates by category"""
        try:
            templates = await self.template_repo.get_templates_by_category(category)
            
            return {
                "success": True,
                "templates": templates,
                "total_count": len(templates)
            }
            
        except Exception as e:
            raise e
    
    async def get_popular_templates(self, limit: int = 20) -> Dict[str, Any]:
        """Get most popular templates by usage count"""
        try:
            templates = await self.template_repo.get_popular_templates(limit)
            
            return {
                "success": True,
                "templates": templates,
                "total_count": len(templates)
            }
            
        except Exception as e:
            raise e
    
    async def rate_template(self, template_id: int, user_id: str, rating: float) -> Dict[str, Any]:
        """Rate a strategy template"""
        try:
            success = await self.template_repo.rate_template(template_id, user_id, rating)
            
            if not success:
                raise NotFoundError(f"Strategy template with ID {template_id} not found")
            
            return {
                "success": True,
                "message": f"Template {template_id} rated successfully"
            }
            
        except Exception as e:
            raise e


class StrategyBacktestService:
    """Service for strategy backtesting operations"""
    
    def __init__(self, backtest_repo: StrategyBacktestRepository):
        self.backtest_repo = backtest_repo
    
    async def compare_backtests(self, backtest_ids: List[str]) -> Dict[str, Any]:
        """Compare multiple backtest results"""
        try:
            comparison = await self.backtest_repo.compare_backtests(backtest_ids)
            
            return {
                "success": True,
                "comparison": comparison
            }
            
        except Exception as e:
            raise e
    
    async def delete_backtest(self, backtest_id: str) -> Dict[str, Any]:
        """Delete a backtest result"""
        try:
            success = await self.backtest_repo.delete_backtest(backtest_id)
            
            if not success:
                raise NotFoundError(f"Backtest with ID {backtest_id} not found")
            
            return {
                "success": True,
                "message": f"Backtest {backtest_id} deleted successfully"
            }
            
        except Exception as e:
            raise e
