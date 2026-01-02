from typing import Protocol, List, Optional, Dict, Any
from datetime import datetime

from app.schemas.strategies import (
    StrategyCreateRequest, StrategyUpdateRequest, StrategyType,
    CustomStrategyCreateRequest, CustomStrategyUpdateRequest,
    ScheduleType, ExecutionType
)


class StrategyRepository(Protocol):
    """Repository interface for strategy operations"""
    
    async def create_strategy(self, strategy_data: StrategyCreateRequest) -> int:
        """Create a new strategy and return its ID"""
        ...
    
    async def get_strategy_by_id(self, strategy_id: int) -> Optional[Dict[str, Any]]:
        """Get a single strategy by ID"""
        ...
    
    async def get_all_strategies(
        self, 
        strategy_type: Optional[StrategyType] = None,
        notifications_enabled: Optional[bool] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get all strategies with optional filters"""
        ...
    
    async def update_strategy(self, strategy_id: int, updates: StrategyUpdateRequest) -> bool:
        """Update a strategy"""
        ...
    
    async def delete_strategy(self, strategy_id: int) -> bool:
        """Delete a strategy"""
        ...
    
    async def get_strategy_stats(self) -> Dict[str, Any]:
        """Get aggregate strategy statistics"""
        ...
    
    async def get_strategies_with_performance(self) -> List[Dict[str, Any]]:
        """Get strategies with their performance metrics"""
        ...
    
    async def search_strategies(self, query: str) -> List[Dict[str, Any]]:
        """Search strategies by name or description"""
        ...


class CustomStrategyRepository(Protocol):
    """Repository interface for custom strategy operations"""
    
    async def create_custom_strategy(self, strategy_data: CustomStrategyCreateRequest) -> int:
        """Create a new custom strategy and return its ID"""
        ...
    
    async def get_custom_strategy_by_id(self, strategy_id: int) -> Optional[Dict[str, Any]]:
        """Get a single custom strategy by ID"""
        ...
    
    async def get_all_custom_strategies(
        self,
        is_active: Optional[bool] = None,
        execution_type: Optional[ExecutionType] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get all custom strategies with optional filters"""
        ...
    
    async def update_custom_strategy(self, strategy_id: int, updates: CustomStrategyUpdateRequest) -> bool:
        """Update a custom strategy"""
        ...
    
    async def delete_custom_strategy(self, strategy_id: int) -> bool:
        """Delete a custom strategy"""
        ...
    
    async def execute_custom_strategy(
        self, 
        strategy_id: int, 
        dry_run: bool = False,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute a custom strategy"""
        ...
    
    async def get_strategy_logs(
        self,
        strategy_id: Optional[int] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get strategy execution logs"""
        ...
    
    async def get_custom_strategy_stats(self) -> Dict[str, Any]:
        """Get aggregate custom strategy statistics"""
        ...
    
    async def batch_update_custom_strategies(
        self, 
        strategy_ids: List[int], 
        updates: Dict[str, Any]
    ) -> int:
        """Update multiple custom strategies at once"""
        ...
    
    async def batch_delete_custom_strategies(self, strategy_ids: List[int]) -> int:
        """Delete multiple custom strategies at once"""
        ...
    
    async def toggle_strategy_activation(self, strategy_id: int, is_active: bool) -> bool:
        """Activate or deactivate a custom strategy"""
        ...
    
    async def get_scheduled_strategies(self) -> List[Dict[str, Any]]:
        """Get all active scheduled strategies"""
        ...
    
    async def update_last_run(self, strategy_id: int, execution_result: Dict[str, Any]) -> bool:
        """Update the last run time and result for a strategy"""
        ...


class StrategyAnalyticsRepository(Protocol):
    """Repository interface for strategy analytics and performance"""
    
    async def get_strategy_performance(
        self, 
        strategy_id: int, 
        period: str = "3mo"
    ) -> Dict[str, Any]:
        """Get performance metrics for a specific strategy"""
        ...
    
    async def backtest_strategy(
        self,
        strategy_id: int,
        start_date: datetime,
        end_date: datetime,
        initial_capital: float = 10000,
        commission: float = 1.0,
        slippage: float = 0.1
    ) -> Dict[str, Any]:
        """Run backtest for a strategy"""
        ...
    
    async def compare_strategies(
        self, 
        strategy_ids: List[int],
        period: str = "3mo"
    ) -> Dict[str, Any]:
        """Compare performance of multiple strategies"""
        ...
    
    async def get_strategy_correlation_matrix(self, strategy_ids: List[int]) -> Dict[str, Any]:
        """Get correlation matrix between strategies"""
        ...
    
    async def get_strategy_recommendations(
        self,
        risk_tolerance: str = "medium",
        time_horizon: str = "medium",
        preferred_sectors: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Get AI-powered strategy recommendations"""
        ...
