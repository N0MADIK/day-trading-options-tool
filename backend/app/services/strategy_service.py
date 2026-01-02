from typing import List, Dict, Any, Optional
from datetime import datetime

from app.repositories.strategy_repo import (
    StrategyRepository, CustomStrategyRepository, StrategyAnalyticsRepository
)
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


class StrategyService:
    """Service for strategy management operations"""
    
    def __init__(
        self, 
        strategy_repository: StrategyRepository,
        custom_strategy_repository: CustomStrategyRepository,
        analytics_repository: StrategyAnalyticsRepository
    ):
        self.strategy_repo = strategy_repository
        self.custom_strategy_repo = custom_strategy_repository
        self.analytics_repo = analytics_repository
    
    async def create_strategy(self, strategy_data: StrategyCreateRequest) -> Dict[str, Any]:
        """Create a new strategy"""
        try:
            # Validate strategy data
            if strategy_data.default_stop_loss_pct >= strategy_data.default_take_profit_pct:
                raise ValidationError("Stop loss percentage must be less than take profit percentage")
            
            # Create strategy
            strategy_id = await self.strategy_repo.create_strategy(strategy_data)
            
            # Return created strategy
            created_strategy = await self.strategy_repo.get_strategy_by_id(strategy_id)
            
            return {
                "success": True,
                "strategy_id": strategy_id,
                "strategy": created_strategy
            }
            
        except Exception as e:
            raise e
    
    async def get_strategy_by_id(self, strategy_id: int) -> Dict[str, Any]:
        """Get a single strategy by ID"""
        strategy = await self.strategy_repo.get_strategy_by_id(strategy_id)
        
        if not strategy:
            raise NotFoundError(f"Strategy with ID {strategy_id} not found")
        
        return strategy
    
    async def list_strategies(self, request: StrategyListRequest) -> List[Dict[str, Any]]:
        """List strategies with optional filters"""
        try:
            strategies = await self.strategy_repo.get_all_strategies(
                strategy_type=request.strategy_type,
                notifications_enabled=request.notifications_enabled,
                limit=request.limit,
                offset=request.offset
            )
            
            return strategies
            
        except Exception as e:
            raise e
    
    async def update_strategy(self, strategy_id: int, updates: StrategyUpdateRequest) -> Dict[str, Any]:
        """Update a strategy"""
        try:
            # Check if strategy exists
            existing_strategy = await self.strategy_repo.get_strategy_by_id(strategy_id)
            if not existing_strategy:
                raise NotFoundError(f"Strategy with ID {strategy_id} not found")
            
            # Validate updates
            update_data = updates.dict(exclude_unset=True)
            if ('default_stop_loss_pct' in update_data and 
                'default_take_profit_pct' in update_data):
                if (update_data['default_stop_loss_pct'] >= 
                    update_data['default_take_profit_pct']):
                    raise ValidationError("Stop loss must be less than take profit")
            
            # Update strategy
            success = await self.strategy_repo.update_strategy(strategy_id, updates)
            
            if not success:
                raise NotFoundError(f"Strategy with ID {strategy_id} not found")
            
            # Return updated strategy
            updated_strategy = await self.strategy_repo.get_strategy_by_id(strategy_id)
            
            return {
                "success": True,
                "strategy": updated_strategy
            }
            
        except Exception as e:
            raise e
    
    async def delete_strategy(self, strategy_id: int) -> Dict[str, Any]:
        """Delete a strategy"""
        try:
            # Check if strategy exists
            existing_strategy = await self.strategy_repo.get_strategy_by_id(strategy_id)
            if not existing_strategy:
                raise NotFoundError(f"Strategy with ID {strategy_id} not found")
            
            # Check if strategy has associated trades
            if existing_strategy.get('trade_count', 0) > 0:
                raise ValidationError("Cannot delete strategy with associated trades")
            
            # Delete strategy
            success = await self.strategy_repo.delete_strategy(strategy_id)
            
            if not success:
                raise NotFoundError(f"Strategy with ID {strategy_id} not found")
            
            return {
                "success": True,
                "message": f"Strategy {strategy_id} deleted successfully"
            }
            
        except Exception as e:
            raise e
    
    async def get_strategy_statistics(self) -> StrategyStatsResponse:
        """Get comprehensive strategy statistics"""
        try:
            stats = await self.strategy_repo.get_strategy_stats()
            
            # Calculate additional metrics
            custom_stats = await self.custom_strategy_repo.get_custom_strategy_stats()
            
            return StrategyStatsResponse(
                total_strategies=stats["total_strategies"],
                active_strategies=custom_stats["active_strategies"],
                custom_strategies=stats["custom_strategies"],
                predefined_strategies=stats["predefined_strategies"],
                strategies_with_trades=stats["strategies_with_trades"]
            )
            
        except Exception as e:
            raise e
    
    async def search_strategies(self, query: str) -> List[Dict[str, Any]]:
        """Search strategies by name or description"""
        try:
            if not query or len(query.strip()) < 2:
                raise ValidationError("Search query must be at least 2 characters")
            
            return await self.strategy_repo.search_strategies(query.strip())
            
        except Exception as e:
            raise e


class CustomStrategyService:
    """Service for custom strategy operations"""
    
    def __init__(self, custom_strategy_repository: CustomStrategyRepository):
        self.custom_strategy_repo = custom_strategy_repository
    
    async def create_custom_strategy(self, strategy_data: CustomStrategyCreateRequest) -> Dict[str, Any]:
        """Create a new custom strategy"""
        try:
            # Validate Python code (basic validation)
            if not self._validate_python_code(strategy_data.code):
                raise ValidationError("Invalid Python code in strategy")
            
            # Create custom strategy
            strategy_id = await self.custom_strategy_repo.create_custom_strategy(strategy_data)
            
            # Return created strategy
            created_strategy = await self.custom_strategy_repo.get_custom_strategy_by_id(strategy_id)
            
            return {
                "success": True,
                "strategy_id": strategy_id,
                "strategy": created_strategy
            }
            
        except Exception as e:
            raise e
    
    async def get_custom_strategy_by_id(self, strategy_id: int) -> Dict[str, Any]:
        """Get a single custom strategy by ID"""
        strategy = await self.custom_strategy_repo.get_custom_strategy_by_id(strategy_id)
        
        if not strategy:
            raise NotFoundError(f"Custom strategy with ID {strategy_id} not found")
        
        return strategy
    
    async def list_custom_strategies(
        self,
        is_active: Optional[bool] = None,
        execution_type: Optional[ExecutionType] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """List custom strategies with optional filters"""
        try:
            return await self.custom_strategy_repo.get_all_custom_strategies(
                is_active=is_active,
                execution_type=execution_type,
                limit=limit,
                offset=offset
            )
            
        except Exception as e:
            raise e
    
    async def update_custom_strategy(self, strategy_id: int, updates: CustomStrategyUpdateRequest) -> Dict[str, Any]:
        """Update a custom strategy"""
        try:
            # Check if strategy exists
            existing_strategy = await self.custom_strategy_repo.get_custom_strategy_by_id(strategy_id)
            if not existing_strategy:
                raise NotFoundError(f"Custom strategy with ID {strategy_id} not found")
            
            # Validate Python code if provided
            if updates.code and not self._validate_python_code(updates.code):
                raise ValidationError("Invalid Python code in strategy")
            
            # Update strategy
            success = await self.custom_strategy_repo.update_custom_strategy(strategy_id, updates)
            
            if not success:
                raise NotFoundError(f"Custom strategy with ID {strategy_id} not found")
            
            # Return updated strategy
            updated_strategy = await self.custom_strategy_repo.get_custom_strategy_by_id(strategy_id)
            
            return {
                "success": True,
                "strategy": updated_strategy
            }
            
        except Exception as e:
            raise e
    
    async def delete_custom_strategy(self, strategy_id: int) -> Dict[str, Any]:
        """Delete a custom strategy"""
        try:
            # Check if strategy exists
            existing_strategy = await self.custom_strategy_repo.get_custom_strategy_by_id(strategy_id)
            if not existing_strategy:
                raise NotFoundError(f"Custom strategy with ID {strategy_id} not found")
            
            # Delete strategy
            success = await self.custom_strategy_repo.delete_custom_strategy(strategy_id)
            
            if not success:
                raise NotFoundError(f"Custom strategy with ID {strategy_id} not found")
            
            return {
                "success": True,
                "message": f"Custom strategy {strategy_id} deleted successfully"
            }
            
        except Exception as e:
            raise e
    
    async def execute_custom_strategy(self, request: StrategyExecutionRequest) -> Dict[str, Any]:
        """Execute a custom strategy"""
        try:
            return await self.custom_strategy_repo.execute_custom_strategy(
                request.strategy_id,
                request.dry_run,
                request.parameters
            )
            
        except Exception as e:
            raise e
    
    async def get_strategy_logs(
        self,
        strategy_id: Optional[int] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get strategy execution logs"""
        try:
            return await self.custom_strategy_repo.get_strategy_logs(
                strategy_id=strategy_id,
                limit=limit,
                offset=offset
            )
            
        except Exception as e:
            raise e
    
    async def toggle_strategy_activation(self, strategy_id: int, is_active: bool) -> Dict[str, Any]:
        """Activate or deactivate a custom strategy"""
        try:
            success = await self.custom_strategy_repo.toggle_strategy_activation(strategy_id, is_active)
            
            if not success:
                raise NotFoundError(f"Custom strategy with ID {strategy_id} not found")
            
            action = "activated" if is_active else "deactivated"
            
            return {
                "success": True,
                "message": f"Custom strategy {strategy_id} {action} successfully"
            }
            
        except Exception as e:
            raise e
    
    async def get_scheduled_strategies(self) -> List[Dict[str, Any]]:
        """Get all active scheduled strategies"""
        try:
            return await self.custom_strategy_repo.get_scheduled_strategies()
            
        except Exception as e:
            raise e
    
    async def batch_update_custom_strategies(self, request: StrategyBatchRequest) -> Dict[str, Any]:
        """Update multiple custom strategies at once"""
        try:
            # Validate action
            if request.action not in ["activate", "deactivate"]:
                raise ValidationError("Invalid batch action")
            
            # Prepare updates based on action
            updates = {"is_active": request.action == "activate"}
            
            # Batch update
            updated_count = await self.custom_strategy_repo.batch_update_custom_strategies(
                request.strategy_ids, updates
            )
            
            return {
                "success": True,
                "updated_count": updated_count,
                "message": f"{request.action.capitalize()}d {updated_count} strategies"
            }
            
        except Exception as e:
            raise e
    
    async def batch_delete_custom_strategies(self, request: StrategyBatchRequest) -> Dict[str, Any]:
        """Delete multiple custom strategies at once"""
        try:
            if request.action != "delete":
                raise ValidationError("Invalid batch action for delete operation")
            
            # Batch delete
            deleted_count = await self.custom_strategy_repo.batch_delete_custom_strategies(request.strategy_ids)
            
            return {
                "success": True,
                "deleted_count": deleted_count,
                "message": f"Deleted {deleted_count} strategies"
            }
            
        except Exception as e:
            raise e
    
    def _validate_python_code(self, code: str) -> bool:
        """Basic validation of Python code"""
        try:
            # Check for basic syntax
            compile(code, '<string>', 'exec')
            
            # Check for dangerous functions (basic security)
            dangerous_functions = ['exec', 'eval', 'open', 'file', 'import os']
            for func in dangerous_functions:
                if func in code:
                    return False
            
            return True
            
        except SyntaxError:
            return False


class StrategyAnalyticsService:
    """Service for strategy analytics and performance"""
    
    def __init__(self, analytics_repository: StrategyAnalyticsRepository):
        self.analytics_repo = analytics_repository
    
    async def get_strategy_performance(
        self, 
        strategy_id: int, 
        period: str = "3mo"
    ) -> StrategyPerformanceResponse:
        """Get performance metrics for a specific strategy"""
        try:
            performance = await self.analytics_repo.get_strategy_performance(strategy_id, period)
            
            return StrategyPerformanceResponse(
                strategy_id=performance["strategy_id"],
                strategy_name=f"Strategy {strategy_id}",  # Would get from DB
                period=performance["period"],
                total_trades=performance["total_trades"],
                win_rate=performance["win_rate"],
                total_pnl=performance["total_pnl"],
                avg_trade_pnl=performance.get("avg_win"),
                max_consecutive_wins=performance.get("max_consecutive_wins", 0),
                max_consecutive_losses=performance.get("max_consecutive_losses", 0)
            )
            
        except Exception as e:
            raise e
    
    async def backtest_strategy(self, request: StrategyBacktestRequest) -> StrategyBacktestResponse:
        """Run backtest for a strategy"""
        try:
            backtest_result = await self.analytics_repo.backtest_strategy(
                request.strategy_id,
                request.start_date,
                request.end_date,
                request.initial_capital,
                request.commission,
                request.slippage
            )
            
            return StrategyBacktestResponse(**backtest_result)
            
        except Exception as e:
            raise e
    
    async def compare_strategies(
        self, 
        strategy_ids: List[int],
        period: str = "3mo"
    ) -> Dict[str, Any]:
        """Compare performance of multiple strategies"""
        try:
            return await self.analytics_repo.compare_strategies(strategy_ids, period)
            
        except Exception as e:
            raise e
    
    async def get_strategy_recommendations(
        self, 
        request: StrategyRecommendationRequest
    ) -> StrategyRecommendationResponse:
        """Get AI-powered strategy recommendations"""
        try:
            recommendations = await self.analytics_repo.get_strategy_recommendations(
                request.risk_tolerance,
                request.time_horizon,
                request.preferred_sectors
            )
            
            return StrategyRecommendationResponse(
                recommendations=recommendations[:request.max_strategies],
                analysis_summary=f"Generated {len(recommendations)} strategy recommendations based on {request.risk_tolerance} risk tolerance",
                confidence_score=0.85,
                generated_at=datetime.utcnow()
            )
            
        except Exception as e:
            raise e
