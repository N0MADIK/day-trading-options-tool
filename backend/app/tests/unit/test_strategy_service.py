import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from app.services.strategy_service import (
    StrategyService, CustomStrategyService, StrategyAnalyticsService
)
from app.repositories.strategy_repo import (
    StrategyRepository, CustomStrategyRepository, StrategyAnalyticsRepository
)
from app.schemas.strategies import (
    StrategyCreateRequest, StrategyUpdateRequest, StrategyType,
    CustomStrategyCreateRequest, CustomStrategyUpdateRequest,
    ScheduleType, ExecutionType, StrategyListRequest,
    StrategyBatchRequest, StrategyRecommendationRequest
)
from app.domain.errors import NotFoundError, ConflictError, ValidationError


class TestStrategyService:
    """Test strategy service operations"""
    
    @pytest.fixture
    def mock_repositories(self):
        """Create mock repositories"""
        return {
            'strategy_repo': AsyncMock(spec=StrategyRepository),
            'custom_strategy_repo': AsyncMock(spec=CustomStrategyRepository),
            'analytics_repo': AsyncMock(spec=StrategyAnalyticsRepository)
        }
    
    @pytest.fixture
    def strategy_service(self, mock_repositories):
        """Create strategy service with mock repositories"""
        return StrategyService(
            mock_repositories['strategy_repo'],
            mock_repositories['custom_strategy_repo'],
            mock_repositories['analytics_repo']
        )
    
    @pytest.mark.asyncio
    async def test_create_strategy_success(self, strategy_service, mock_repositories):
        """Test successful strategy creation"""
        # Setup
        strategy_data = StrategyCreateRequest(
            name="Test Strategy",
            description="A test strategy",
            default_stop_loss_pct=0.15,
            default_take_profit_pct=0.30,
            notifications_enabled=True
        )
        
        mock_repositories['strategy_repo'].create_strategy.return_value = 1
        mock_repositories['strategy_repo'].get_strategy_by_id.return_value = {
            'id': 1,
            'name': 'Test Strategy',
            'strategy_type': 'PREDEFINED'
        }
        
        # Execute
        result = await strategy_service.create_strategy(strategy_data)
        
        # Assert
        assert result["success"] is True
        assert result["strategy_id"] == 1
        mock_repositories['strategy_repo'].create_strategy.assert_called_once_with(strategy_data)
    
    @pytest.mark.asyncio
    async def test_create_strategy_invalid_stop_loss(self, strategy_service, mock_repositories):
        """Test strategy creation with invalid stop loss"""
        strategy_data = StrategyCreateRequest(
            name="Test Strategy",
            default_stop_loss_pct=0.40,  # Invalid: higher than take profit
            default_take_profit_pct=0.30
        )
        
        with pytest.raises(ValidationError) as exc_info:
            await strategy_service.create_strategy(strategy_data)
        
        assert "Stop loss percentage must be less than take profit" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_get_strategy_by_id_success(self, strategy_service, mock_repositories):
        """Test successful strategy retrieval"""
        # Setup
        mock_strategy = {
            'id': 1,
            'name': 'Test Strategy',
            'strategy_type': 'PREDEFINED'
        }
        mock_repositories['strategy_repo'].get_strategy_by_id.return_value = mock_strategy
        
        # Execute
        result = await strategy_service.get_strategy_by_id(1)
        
        # Assert
        assert result == mock_strategy
        mock_repositories['strategy_repo'].get_strategy_by_id.assert_called_once_with(1)
    
    @pytest.mark.asyncio
    async def test_get_strategy_by_id_not_found(self, strategy_service, mock_repositories):
        """Test strategy retrieval when not found"""
        mock_repositories['strategy_repo'].get_strategy_by_id.return_value = None
        
        with pytest.raises(NotFoundError) as exc_info:
            await strategy_service.get_strategy_by_id(999)
        
        assert "Strategy with ID 999 not found" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_list_strategies_success(self, strategy_service, mock_repositories):
        """Test successful strategy listing"""
        # Setup
        request = StrategyListRequest(strategy_type=StrategyType.PREDEFINED, limit=10)
        mock_strategies = [
            {'id': 1, 'name': 'Strategy 1', 'strategy_type': 'PREDEFINED'},
            {'id': 2, 'name': 'Strategy 2', 'strategy_type': 'PREDEFINED'}
        ]
        mock_repositories['strategy_repo'].get_all_strategies.return_value = mock_strategies
        
        # Execute
        result = await strategy_service.list_strategies(request)
        
        # Assert
        assert len(result) == 2
        assert result[0]['strategy_type'] == 'PREDEFINED'
        mock_repositories['strategy_repo'].get_all_strategies.assert_called_once_with(
            strategy_type=StrategyType.PREDEFINED, notifications_enabled=None, limit=10, offset=None
        )
    
    @pytest.mark.asyncio
    async def test_update_strategy_success(self, strategy_service, mock_repositories):
        """Test successful strategy update"""
        # Setup
        updates = StrategyUpdateRequest(
            name="Updated Strategy",
            default_stop_loss_pct=0.20
        )
        existing_strategy = {'id': 1, 'name': 'Test Strategy'}
        updated_strategy = {'id': 1, 'name': 'Updated Strategy'}
        
        mock_repositories['strategy_repo'].get_strategy_by_id.return_value = existing_strategy
        mock_repositories['strategy_repo'].update_strategy.return_value = True
        mock_repositories['strategy_repo'].get_strategy_by_id.return_value = updated_strategy
        
        # Execute
        result = await strategy_service.update_strategy(1, updates)
        
        # Assert
        assert result["success"] is True
        assert result["strategy"]["name"] == "Updated Strategy"
        mock_repositories['strategy_repo'].update_strategy.assert_called_once_with(1, updates)
    
    @pytest.mark.asyncio
    async def test_delete_strategy_success(self, strategy_service, mock_repositories):
        """Test successful strategy deletion"""
        # Setup
        existing_strategy = {'id': 1, 'name': 'Test Strategy', 'trade_count': 0}
        mock_repositories['strategy_repo'].get_strategy_by_id.return_value = existing_strategy
        mock_repositories['strategy_repo'].delete_strategy.return_value = True
        
        # Execute
        result = await strategy_service.delete_strategy(1)
        
        # Assert
        assert result["success"] is True
        assert "deleted successfully" in result["message"]
        mock_repositories['strategy_repo'].delete_strategy.assert_called_once_with(1)
    
    @pytest.mark.asyncio
    async def test_delete_strategy_with_trades_forbidden(self, strategy_service, mock_repositories):
        """Test deleting strategy with associated trades (should be forbidden)"""
        # Setup
        existing_strategy = {'id': 1, 'name': 'Test Strategy', 'trade_count': 5}
        mock_repositories['strategy_repo'].get_strategy_by_id.return_value = existing_strategy
        
        # Execute & Assert
        with pytest.raises(ValidationError) as exc_info:
            await strategy_service.delete_strategy(1)
        
        assert "Cannot delete strategy with associated trades" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_search_strategies_success(self, strategy_service, mock_repositories):
        """Test successful strategy search"""
        # Setup
        search_results = [
            {'id': 1, 'name': 'Momentum Strategy', 'description': 'Momentum-based'},
            {'id': 2, 'name': 'Mean Reversion', 'description': 'Mean reversion'}
        ]
        mock_repositories['strategy_repo'].search_strategies.return_value = search_results
        
        # Execute
        result = await strategy_service.search_strategies("Momentum")
        
        # Assert
        assert len(result) == 2
        assert "Momentum" in result[0]["name"]
        mock_repositories['strategy_repo'].search_strategies.assert_called_once_with("Momentum")
    
    @pytest.mark.asyncio
    async def test_search_strategies_invalid_query(self, strategy_service, mock_repositories):
        """Test strategy search with invalid query"""
        # Execute & Assert
        with pytest.raises(ValidationError) as exc_info:
            await strategy_service.search_strategies("A")
        
        assert "at least 2 characters" in str(exc_info.value)


class TestCustomStrategyService:
    """Test custom strategy service operations"""
    
    @pytest.fixture
    def mock_repository(self):
        """Create mock custom strategy repository"""
        return AsyncMock(spec=CustomStrategyRepository)
    
    @pytest.fixture
    def custom_strategy_service(self, mock_repository):
        """Create custom strategy service with mock repository"""
        return CustomStrategyService(mock_repository)
    
    @pytest.mark.asyncio
    async def test_create_custom_strategy_success(self, custom_strategy_service, mock_repository):
        """Test successful custom strategy creation"""
        # Setup
        strategy_data = CustomStrategyCreateRequest(
            name="Custom Test Strategy",
            code="def execute():\n    return 'test'",
            schedule_type=ScheduleType.INTERVAL,
            schedule_value="300",
            execution_type=ExecutionType.HOST
        )
        
        mock_repository.create_custom_strategy.return_value = 1
        mock_repository.get_custom_strategy_by_id.return_value = {
            'id': 1,
            'name': 'Custom Test Strategy',
            'code': "def execute():\n    return 'test'"
        }
        
        # Execute
        result = await custom_strategy_service.create_custom_strategy(strategy_data)
        
        # Assert
        assert result["success"] is True
        assert result["strategy_id"] == 1
        mock_repository.create_custom_strategy.assert_called_once_with(strategy_data)
    
    @pytest.mark.asyncio
    async def test_create_custom_strategy_invalid_code(self, custom_strategy_service, mock_repository):
        """Test custom strategy creation with invalid Python code"""
        strategy_data = CustomStrategyCreateRequest(
            name="Invalid Strategy",
            code="invalid python code {"
        )
        
        with pytest.raises(ValidationError) as exc_info:
            await custom_strategy_service.create_custom_strategy(strategy_data)
        
        assert "Invalid Python code" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_execute_custom_strategy_success(self, custom_strategy_service, mock_repository):
        """Test successful custom strategy execution"""
        # Setup
        mock_repository.execute_custom_strategy.return_value = {
            "execution_id": 1,
            "strategy_id": 1,
            "status": "SUCCESS",
            "trades_generated": 0
        }
        
        # Execute
        from app.schemas.strategies import StrategyExecutionRequest
        request = StrategyExecutionRequest(strategy_id=1, dry_run=True)
        result = await custom_strategy_service.execute_custom_strategy(request)
        
        # Assert
        assert result["status"] == "SUCCESS"
        assert result["strategy_id"] == 1
        mock_repository.execute_custom_strategy.assert_called_once_with(1, True, None)
    
    @pytest.mark.asyncio
    async def test_toggle_strategy_activation(self, custom_strategy_service, mock_repository):
        """Test strategy activation toggle"""
        # Setup
        mock_repository.toggle_strategy_activation.return_value = True
        
        # Execute
        result = await custom_strategy_service.toggle_strategy_activation(1, True)
        
        # Assert
        assert result["success"] is True
        assert "activated" in result["message"]
        mock_repository.toggle_strategy_activation.assert_called_once_with(1, True)
    
    @pytest.mark.asyncio
    async def test_batch_update_custom_strategies(self, custom_strategy_service, mock_repository):
        """Test batch updating custom strategies"""
        # Setup
        batch_request = StrategyBatchRequest(
            strategy_ids=[1, 2, 3],
            action="activate"
        )
        mock_repository.batch_update_custom_strategies.return_value = 3
        
        # Execute
        result = await custom_strategy_service.batch_update_custom_strategies(batch_request)
        
        # Assert
        assert result["success"] is True
        assert result["updated_count"] == 3
        assert "Activated" in result["message"]
    
    @pytest.mark.asyncio
    async def test_batch_update_invalid_action(self, custom_strategy_service, mock_repository):
        """Test batch update with invalid action"""
        batch_request = StrategyBatchRequest(
            strategy_ids=[1, 2],
            action="invalid"
        )
        
        with pytest.raises(ValidationError) as exc_info:
            await custom_strategy_service.batch_update_custom_strategies(batch_request)
        
        assert "Invalid batch action" in str(exc_info.value)


class TestStrategyAnalyticsService:
    """Test strategy analytics service operations"""
    
    @pytest.fixture
    def mock_repository(self):
        """Create mock analytics repository"""
        return AsyncMock(spec=StrategyAnalyticsRepository)
    
    @pytest.fixture
    def analytics_service(self, mock_repository):
        """Create analytics service with mock repository"""
        return StrategyAnalyticsService(mock_repository)
    
    @pytest.mark.asyncio
    async def test_get_strategy_performance(self, analytics_service, mock_repository):
        """Test getting strategy performance"""
        # Setup
        mock_performance = {
            "strategy_id": 1,
            "period": "3mo",
            "total_trades": 50,
            "win_rate": 65.0,
            "total_pnl": 2500.0
        }
        mock_repository.get_strategy_performance.return_value = mock_performance
        
        # Execute
        result = await analytics_service.get_strategy_performance(1, "3mo")
        
        # Assert
        assert result.strategy_id == 1
        assert result.period == "3mo"
        assert result.total_trades == 50
        assert result.win_rate == 65.0
        mock_repository.get_strategy_performance.assert_called_once_with(1, "3mo")
    
    @pytest.mark.asyncio
    async def test_backtest_strategy(self, analytics_service, mock_repository):
        """Test strategy backtesting"""
        # Setup
        from app.schemas.strategies import StrategyBacktestRequest
        request = StrategyBacktestRequest(
            strategy_id=1,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 12, 31),
            initial_capital=10000
        )
        
        mock_backtest = {
            "strategy_id": 1,
            "strategy_name": "Test Strategy",
            "initial_capital": 10000,
            "final_capital": 12000,
            "total_return_pct": 20.0
        }
        mock_repository.backtest_strategy.return_value = mock_backtest
        
        # Execute
        result = await analytics_service.backtest_strategy(request)
        
        # Assert
        assert result.strategy_id == 1
        assert result.total_return_pct == 20.0
        mock_repository.backtest_strategy.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_compare_strategies(self, analytics_service, mock_repository):
        """Test strategy comparison"""
        # Setup
        strategy_ids = [1, 2, 3]
        mock_comparison = {
            "period": "3mo",
            "strategies_compared": 3,
            "results": [
                {"strategy_id": 1, "total_pnl": 1000},
                {"strategy_id": 2, "total_pnl": 2000},
                {"strategy_id": 3, "total_pnl": 500}
            ]
        }
        mock_repository.compare_strategies.return_value = mock_comparison
        
        # Execute
        result = await analytics_service.compare_strategies(strategy_ids, "3mo")
        
        # Assert
        assert result["strategies_compared"] == 3
        assert len(result["results"]) == 3
        mock_repository.compare_strategies.assert_called_once_with(strategy_ids, "3mo")
    
    @pytest.mark.asyncio
    async def test_get_strategy_recommendations(self, analytics_service, mock_repository):
        """Test getting strategy recommendations"""
        # Setup
        from app.schemas.strategies import StrategyRecommendationRequest
        request = StrategyRecommendationRequest(
            risk_tolerance="medium",
            time_horizon="medium"
        )
        
        mock_recommendations = [
            {
                "name": "Momentum Scalping",
                "risk_level": "medium",
                "confidence": 0.85
            }
        ]
        mock_repository.get_strategy_recommendations.return_value = mock_recommendations
        
        # Execute
        result = await analytics_service.get_strategy_recommendations(request)
        
        # Assert
        assert len(result.recommendations) == 1
        assert result.confidence_score == 0.85
        mock_repository.get_strategy_recommendations.assert_called_once_with("medium", "medium", None)
