import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
import uuid

from app.services.custom_strategy_service import (
    CustomStrategyService, StrategySchedulerService, StrategyTemplateService,
    StrategyBacktestService
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


class TestCustomStrategyService:
    """Test custom strategy service operations"""
    
    @pytest.fixture
    def mock_repositories(self):
        """Create mock repositories"""
        return {
            'strategy_repo': AsyncMock(spec=SQLAlchemyCustomStrategyRepository),
            'execution_repo': AsyncMock(spec=SQLAlchemyStrategyExecutionRepository),
            'log_repo': AsyncMock(spec=SQLAlchemyStrategyLogRepository),
            'performance_repo': AsyncMock(spec=SQLAlchemyStrategyPerformanceRepository),
            'template_repo': AsyncMock(spec=SQLAlchemyStrategyTemplateRepository),
            'backtest_repo': AsyncMock(spec=SQLAlchemyStrategyBacktestRepository),
            'signal_repo': AsyncMock(spec=SQLAlchemyStrategySignalRepository),
            'validation_repo': AsyncMock(spec=SQLAlchemyStrategyValidationRepository),
            'scheduler_repo': AsyncMock(spec=SQLAlchemyStrategySchedulerRepository),
            'batch_repo': AsyncMock(spec=SQLAlchemyCustomStrategyBatchRepository),
            'analytics_repo': AsyncMock(spec=SQLAlchemyCustomStrategyAnalyticsRepository)
        }
    
    @pytest.fixture
    def custom_strategy_service(self, mock_repositories):
        """Create custom strategy service with mock repositories"""
        return CustomStrategyService(
            mock_repositories['strategy_repo'],
            mock_repositories['execution_repo'],
            mock_repositories['log_repo'],
            mock_repositories['performance_repo'],
            mock_repositories['template_repo'],
            mock_repositories['backtest_repo'],
            mock_repositories['signal_repo'],
            mock_repositories['validation_repo'],
            mock_repositories['scheduler_repo'],
            mock_repositories['batch_repo'],
            mock_repositories['analytics_repo']
        )
    
    @pytest.mark.asyncio
    async def test_create_custom_strategy_success(self, custom_strategy_service, mock_repositories):
        """Test successful custom strategy creation"""
        # Setup
        strategy_data = CustomStrategyCreateRequest(
            name="Test Strategy",
            description="A test strategy",
            code="def execute():\n    return []",
            execution_type=StrategyExecutionType.PYTHON,
            schedule_type=StrategyScheduleType.DAILY,
            schedule_value="09:30",
            is_active=True,
            tags=["test", "python"]
        )
        
        mock_validation_result = StrategyValidationResponse(
            is_valid=True,
            syntax_errors=[],
            validation_warnings=[],
            execution_time_ms=50
        )
        mock_repositories['validation_repo'].validate_strategy_code.return_value(mock_validation_result)
        mock_repositories['strategy_repo'].create_custom_strategy.return_value(1)
        mock_strategy = {
            'id': 1,
            'name': 'Test Strategy',
            'description': 'A test strategy',
            'execution_type': StrategyExecutionType.PYTHON,
            'schedule_type': StrategyScheduleType.DAILY,
            'is_active': True,
            'tags': ['test', 'python'],
            'created_at': datetime.utcnow()
        }
        mock_repositories['strategy_repo'].get_custom_strategy_by_id.return_value(mock_strategy)
        
        # Execute
        result = await custom_strategy_service.create_custom_strategy(strategy_data)
        
        # Assert
        assert result["success"] is True
        assert result["strategy_id"] == 1
        assert "strategy" in result
        assert "validation_result" in result
        mock_repositories['validation_repo'].validate_strategy_code.assert_called_once()
        mock_repositories['strategy_repo'].create_custom_strategy.assert_called_once_with(strategy_data)
        mock_repositories['scheduler_repo'].schedule_strategy.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_custom_strategy_validation_failure(self, custom_strategy_service, mock_repositories):
        """Test custom strategy creation with validation failure"""
        # Setup
        strategy_data = CustomStrategyCreateRequest(
            name="Test Strategy",
            code="invalid python code",
            execution_type=StrategyExecutionType.PYTHON
        )
        
        mock_validation_result = StrategyValidationResponse(
            is_valid=False,
            syntax_errors=["Syntax error at line 1"],
            validation_warnings=[],
            execution_time_ms=10
        )
        mock_repositories['validation_repo'].validate_strategy_code.return_value(mock_validation_result)
        
        # Execute & Assert
        with pytest.raises(ValidationError) as exc_info:
            await custom_strategy_service.create_custom_strategy(strategy_data)
        assert "validation failed" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_get_custom_strategy_by_id_success(self, custom_strategy_service, mock_repositories):
        """Test successful custom strategy retrieval by ID"""
        # Setup
        mock_strategy = {
            'id': 1,
            'name': 'Test Strategy',
            'description': 'A test strategy',
            'execution_type': StrategyExecutionType.PYTHON,
            'schedule_type': StrategyScheduleType.DAILY,
            'is_active': True,
            'tags': ['test', 'python'],
            'created_at': datetime.utcnow()
        }
        mock_repositories['strategy_repo'].get_custom_strategy_by_id.return_value(mock_strategy)
        
        # Execute
        result = await custom_strategy_service.get_custom_strategy_by_id(1)
        
        # Assert
        assert result["success"] is True
        assert result["strategy"] == mock_strategy
        mock_repositories['strategy_repo'].get_custom_strategy_by_id.assert_called_once_with(1)
    
    @pytest.mark.asyncio
    async def test_get_custom_strategy_by_id_not_found(self, custom_strategy_service, mock_repositories):
        """Test custom strategy retrieval when not found"""
        # Setup
        mock_repositories['strategy_repo'].get_custom_strategy_by_id.return_value(None)
        
        # Execute & Assert
        with pytest.raises(NotFoundError) as exc_info:
            await custom_strategy_service.get_custom_strategy_by_id(999)
        assert "not found" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_list_custom_strategies_success(self, custom_strategy_service, mock_repositories):
        """Test successful custom strategy listing"""
        # Setup
        mock_strategies = [
            {
                'id': 1,
                'name': 'Strategy A',
                'execution_type': StrategyExecutionType.PYTHON,
                'is_active': True
            },
            {
                'id': 2,
                'name': 'Strategy B',
                'execution_type': StrategyExecutionType.JAVASCRIPT,
                'is_active': False
            }
        ]
        mock_repositories['strategy_repo'].get_all_custom_strategies.return_value(mock_strategies)
        
        # Execute
        result = await custom_strategy_service.list_custom_strategies(CustomStrategyListRequest())
        
        # Assert
        assert result["success"] is True
        assert len(result["strategies"]) == 2
        assert result["total_count"] == 2
    
    @pytest.mark.asyncio
    async def test_update_custom_strategy_success(self, custom_strategy_service, mock_repositories):
        """Test successful custom strategy update"""
        # Setup
        updates = CustomStrategyUpdateRequest(
            name="Updated Strategy",
            description="Updated description"
        )
        
        mock_repositories['strategy_repo'].update_custom_strategy.return_value(True)
        mock_strategy = {
            'id': 1,
            'name': 'Updated Strategy',
            'description': 'Updated description',
            'execution_type': StrategyExecutionType.PYTHON,
            'schedule_type': StrategyScheduleType.DAILY,
            'is_active': True
        }
        mock_repositories['strategy_repo'].get_custom_strategy_by_id.return_value(mock_strategy)
        
        # Execute
        result = await custom_strategy_service.update_custom_strategy(1, updates)
        
        # Assert
        assert result["success"] is True
        assert "strategy" in result
        assert result["strategy"]["name"] == "Updated Strategy"
        mock_repositories['strategy_repo'].update_custom_strategy.assert_called_once_with(1, updates)
    
    @pytest.mark.asyncio
    async def test_update_custom_strategy_not_found(self, custom_strategy_service, mock_repositories):
        """Test custom strategy update when not found"""
        # Setup
        updates = CustomStrategyUpdateRequest(name="Updated Strategy")
        mock_repositories['strategy_repo'].update_custom_strategy.return_value(False)
        
        # Execute & Assert
        with pytest.raises(NotFoundError) as exc_info:
            await custom_strategy_service.update_custom_strategy(999, updates)
        assert "not found" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_delete_custom_strategy_success(self, custom_strategy_service, mock_repositories):
        """Test successful custom strategy deletion"""
        # Setup
        mock_repositories['strategy_repo'].delete_custom_strategy.return_value(True)
        
        # Execute
        result = await custom_strategy_service.delete_custom_strategy(1)
        
        # Assert
        assert result["success"] is True
        assert "deleted successfully" in result["message"].lower()
        mock_repositories['strategy_repo'].delete_custom_strategy.assert_called_once_with(1)
        mock_repositories['scheduler_repo'].unschedule_strategy.assert_called_once_with(1)
    
    @pytest.mark.asyncio
    async def test_delete_custom_strategy_not_found(self, custom_strategy_service, mock_repositories):
        """Test custom strategy deletion when not found"""
        # Setup
        mock_repositories['strategy_repo'].delete_custom_strategy.return_value(False)
        
        # Execute & Assert
        with pytest.raises(NotFoundError) as exc_info:
            await custom_strategy_service.delete_custom_strategy(999)
        assert "not found" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_toggle_strategy_active_success(self, custom_strategy_service, mock_repositories):
        """Test successful strategy active status toggle"""
        # Setup
        mock_repositories['strategy_repo'].toggle_strategy_active.return_value(True)
        mock_strategy = {
            'id': 1,
            'name': 'Test Strategy',
            'is_active': True,
            'schedule_type': StrategyScheduleType.DAILY,
            'schedule_value': '09:30'
        }
        mock_repositories['strategy_repo'].get_custom_strategy_by_id.return_value(mock_strategy)
        
        # Execute
        result = await custom_strategy_service.toggle_strategy_active(1)
        
        # Assert
        assert result["success"] is True
        assert "strategy" in result
        mock_repositories['strategy_repo'].toggle_strategy_active.assert_called_once_with(1)
        mock_repositories['scheduler_repo'].schedule_strategy.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_toggle_strategy_active_not_found(self, custom_strategy_service, mock_repositories):
        """Test strategy active status toggle when not found"""
        # Setup
        mock_repositories['strategy_repo'].toggle_strategy_active.return_value(False)
        
        # Execute & Assert
        with pytest.raises(NotFoundError) as exc_info:
            await custom_strategy_service.toggle_strategy_active(999)
        assert "not found" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_execute_strategy_success(self, custom_strategy_service, mock_repositories):
        """Test successful strategy execution"""
        # Setup
        execution_request = StrategyExecutionRequest(
            strategy_id=1,
            dry_run=False,
            parameters={"test_param": "value"}
        )
        
        mock_strategy = {'id': 1, 'name': 'Test Strategy'}
        mock_repositories['strategy_repo'].get_custom_strategy_by_id.return_value(mock_strategy)
        
        mock_execution_result = StrategyExecutionResponse(
            execution_id=str(uuid.uuid4()),
            strategy_id=1,
            status="COMPLETED",
            start_time=datetime.utcnow(),
            end_time=datetime.utcnow() + timedelta(seconds=5),
            duration_seconds=5.0,
            trades_generated=2,
            signals_generated=5,
            error_message=None,
            execution_details={"test": "details"}
        )
        mock_repositories['execution_repo'].execute_strategy.return_value(mock_execution_result)
        
        # Execute
        result = await custom_strategy_service.execute_strategy(execution_request)
        
        # Assert
        assert result["success"] is True
        assert "execution" in result
        mock_repositories['strategy_repo'].get_custom_strategy_by_id.assert_called_once_with(1)
        mock_repositories['execution_repo'].execute_strategy.assert_called_once_with(execution_request)
        mock_repositories['log_repo'].create_strategy_log.assert_called_once()
        mock_repositories['performance_repo'].update_strategy_performance.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_strategy_not_found(self, custom_strategy_service, mock_repositories):
        """Test strategy execution when strategy not found"""
        # Setup
        execution_request = StrategyExecutionRequest(strategy_id=999)
        mock_repositories['strategy_repo'].get_custom_strategy_by_id.return_value(None)
        
        # Execute & Assert
        with pytest.raises(NotFoundError) as exc_info:
            await custom_strategy_service.execute_strategy(execution_request)
        assert "not found" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_create_strategy_template_success(self, custom_strategy_service, mock_repositories):
        """Test successful strategy template creation"""
        # Setup
        template_data = StrategyTemplateCreateRequest(
            name="Test Template",
            description="A test template",
            category="momentum",
            code="def execute():\n    return []",
            parameters={"param1": "value1"},
            tags=["template", "test"],
            is_public=True
        )
        
        mock_repositories['template_repo'].create_strategy_template.return_value(1)
        mock_template = {
            'id': 1,
            'name': 'Test Template',
            'description': 'A test template',
            'category': 'momentum',
            'is_public': True,
            'tags': ['template', 'test'],
            'created_at': datetime.utcnow()
        }
        mock_repositories['template_repo'].get_template_by_id.return_value(mock_template)
        
        # Execute
        result = await custom_strategy_service.create_strategy_template(template_data)
        
        # Assert
        assert result["success"] is True
        assert result["template_id"] == 1
        assert "template" in result
        mock_repositories['template_repo'].create_strategy_template.assert_called_once_with(template_data)
    
    @pytest.mark.asyncio
    async def test_run_backtest_success(self, custom_strategy_service, mock_repositories):
        """Test successful backtest execution"""
        # Setup
        backtest_request = BacktestRequest(
            strategy_id=1,
            start_date=datetime.utcnow() - timedelta(days=365),
            end_date=datetime.utcnow(),
            initial_capital=10000.0,
            parameters={"test_param": "value"}
        )
        
        mock_strategy = {'id': 1, 'name': 'Test Strategy'}
        mock_repositories['strategy_repo'].get_custom_strategy_by_id.return_value(mock_strategy)
        
        mock_backtest_result = BacktestResponse(
            backtest_id=str(uuid.uuid4()),
            strategy_id=1,
            start_date=datetime.utcnow() - timedelta(days=365),
            end_date=datetime.utcnow(),
            initial_capital=10000.0,
            final_capital=12000.0,
            total_return=0.20,
            sharpe_ratio=1.5,
            max_drawdown=0.10,
            win_rate=0.60,
            total_trades=50,
            profitable_trades=30,
            execution_time_seconds=30.0,
            status="COMPLETED",
            error_message=None
        )
        mock_repositories['backtest_repo'].run_backtest.return_value(mock_backtest_result)
        
        # Execute
        result = await custom_strategy_service.run_backtest(backtest_request)
        
        # Assert
        assert result["success"] is True
        assert "backtest" in result
        mock_repositories['strategy_repo'].get_custom_strategy_by_id.assert_called_once_with(1)
        mock_repositories['backtest_repo'].run_backtest.assert_called_once_with(backtest_request)
    
    @pytest.mark.asyncio
    async def test_run_backtest_strategy_not_found(self, custom_strategy_service, mock_repositories):
        """Test backtest execution when strategy not found"""
        # Setup
        backtest_request = BacktestRequest(
            strategy_id=999,
            start_date=datetime.utcnow() - timedelta(days=365),
            end_date=datetime.utcnow()
        )
        mock_repositories['strategy_repo'].get_custom_strategy_by_id.return_value(None)
        
        # Execute & Assert
        with pytest.raises(NotFoundError) as exc_info:
            await custom_strategy_service.run_backtest(backtest_request)
        assert "not found" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_create_strategy_signal_success(self, custom_strategy_service, mock_repositories):
        """Test successful strategy signal creation"""
        # Setup
        signal_data = StrategySignalCreateRequest(
            strategy_id=1,
            symbol="AAPL",
            signal_type="BUY",
            action="BUY",
            confidence=0.85,
            price=150.0,
            quantity=100,
            expiration_time=datetime.utcnow() + timedelta(hours=24),
            metadata={"reason": "RSI oversold"}
        )
        
        mock_strategy = {'id': 1, 'name': 'Test Strategy'}
        mock_repositories['strategy_repo'].get_custom_strategy_by_id.return_value(mock_strategy)
        mock_repositories['signal_repo'].create_strategy_signal.return_value(1)
        mock_signal = {
            'id': 1,
            'strategy_id': 1,
            'symbol': 'AAPL',
            'signal_type': 'BUY',
            'action': 'BUY',
            'confidence': 0.85,
            'price': 150.0,
            'quantity': 100,
            'is_executed': False,
            'created_at': datetime.utcnow()
        }
        mock_repositories['signal_repo'].get_signal_by_id.return_value(mock_signal)
        
        # Execute
        result = await custom_strategy_service.create_strategy_signal(signal_data)
        
        # Assert
        assert result["success"] is True
        assert result["signal_id"] == 1
        assert "signal" in result
        mock_repositories['strategy_repo'].get_custom_strategy_by_id.assert_called_once_with(1)
        mock_repositories['signal_repo'].create_strategy_signal.assert_called_once_with(signal_data)
    
    @pytest.mark.asyncio
    async def test_validate_strategy_code_success(self, custom_strategy_service, mock_repositories):
        """Test successful strategy code validation"""
        # Setup
        validation_request = StrategyValidationRequest(
            code="def execute():\n    return []",
            parameters={"param1": "value1"},
            environment_vars={"ENV": "test"}
        )
        
        mock_validation_result = StrategyValidationResponse(
            is_valid=True,
            syntax_errors=[],
            validation_warnings=["Consider adding error handling"],
            execution_time_ms=25
        )
        mock_repositories['validation_repo'].validate_strategy_code.return_value(mock_validation_result)
        
        # Execute
        result = await custom_strategy_service.validate_strategy_code(validation_request)
        
        # Assert
        assert result["success"] is True
        assert "validation" in result
        assert result["validation"].is_valid is True
        mock_repositories['validation_repo'].validate_strategy_code.assert_called_once_with(validation_request)
    
    @pytest.mark.asyncio
    async def test_batch_update_strategies_success(self, custom_strategy_service, mock_repositories):
        """Test successful batch strategy update"""
        # Setup
        strategy_ids = [1, 2, 3]
        updates = {"is_active": False}
        
        mock_batch_result = {
            "success": True,
            "total_updated": 3,
            "failed_updates": [],
            "errors": []
        }
        mock_repositories['batch_repo'].batch_update_strategies.return_value(mock_batch_result)
        
        # Execute
        result = await custom_strategy_service.batch_update_strategies(strategy_ids, updates)
        
        # Assert
        assert result["success"] is True
        assert "batch_result" in result
        mock_repositories['batch_repo'].batch_update_strategies.assert_called_once_with(strategy_ids, updates)
    
    @pytest.mark.asyncio
    async def test_batch_delete_strategies_success(self, custom_strategy_service, mock_repositories):
        """Test successful batch strategy deletion"""
        # Setup
        strategy_ids = [1, 2, 3]
        
        mock_batch_result = {
            "success": True,
            "total_deleted": 3,
            "failed_deletions": [],
            "errors": []
        }
        mock_repositories['batch_repo'].batch_delete_strategies.return_value(mock_batch_result)
        
        # Execute
        result = await custom_strategy_service.batch_delete_strategies(strategy_ids)
        
        # Assert
        assert result["success"] is True
        assert "batch_result" in result
        mock_repositories['batch_repo'].batch_delete_strategies.assert_called_once_with(strategy_ids)
        # Verify unschedule was called for each strategy
        assert mock_repositories['scheduler_repo'].unschedule_strategy.call_count == 3
    
    @pytest.mark.asyncio
    async def test_get_strategy_performance_success(self, custom_strategy_service, mock_repositories):
        """Test successful strategy performance retrieval"""
        # Setup
        mock_performance = {
            "strategy_id": 1,
            "period_days": 30,
            "total_executions": 25,
            "successful_executions": 23,
            "success_rate": 0.92,
            "average_execution_time_seconds": 2.5,
            "total_trades_generated": 50,
            "total_signals_generated": 125,
            "profit_loss": 1500.0,
            "win_rate": 0.68,
            "sharpe_ratio": 1.8,
            "max_drawdown": 0.05
        }
        mock_repositories['analytics_repo'].get_execution_analytics.return_value(mock_performance)
        
        # Execute
        result = await custom_strategy_service.get_strategy_performance(1, 30)
        
        # Assert
        assert result["success"] is True
        assert "performance" in result
        assert result["performance"]["strategy_id"] == 1
        mock_repositories['analytics_repo'].get_execution_analytics.assert_called_once_with(1, 30)
    
    @pytest.mark.asyncio
    async def test_get_strategy_health_metrics_success(self, custom_strategy_service, mock_repositories):
        """Test successful strategy health metrics retrieval"""
        # Setup
        mock_health = {
            "strategy_id": 1,
            "health_score": 0.85,
            "last_execution_status": "SUCCESS",
            "last_execution_time": datetime.utcnow(),
            "consecutive_failures": 0,
            "average_execution_time": 2.1,
            "error_rate": 0.08,
            "performance_trend": "IMPROVING",
            "recommendations": ["Consider optimizing for faster execution"]
        }
        mock_repositories['analytics_repo'].get_strategy_health_metrics.return_value(mock_health)
        
        # Execute
        result = await custom_strategy_service.get_strategy_health_metrics(1)
        
        # Assert
        assert result["success"] is True
        assert "health_metrics" in result
        assert result["health_metrics"]["health_score"] == 0.85
        mock_repositories['analytics_repo'].get_strategy_health_metrics.assert_called_once_with(1)
    
    @pytest.mark.asyncio
    async def test_get_usage_statistics_success(self, custom_strategy_service, mock_repositories):
        """Test successful usage statistics retrieval"""
        # Setup
        mock_stats = {
            "period_days": 30,
            "total_strategies": 15,
            "active_strategies": 8,
            "total_executions": 1250,
            "successful_executions": 1180,
            "total_trades": 2500,
            "total_signals": 6250,
            "average_execution_time": 3.2,
            "most_used_execution_type": "PYTHON",
            "most_common_schedule_type": "DAILY",
            "top_performing_strategies": [
                {"strategy_id": 1, "name": "Strategy A", "return": 0.15},
                {"strategy_id": 2, "name": "Strategy B", "return": 0.12}
            ]
        }
        mock_repositories['analytics_repo'].get_usage_statistics.return_value(mock_stats)
        
        # Execute
        result = await custom_strategy_service.get_usage_statistics(30)
        
        # Assert
        assert result["success"] is True
        assert "usage_statistics" in result
        assert result["usage_statistics"]["total_strategies"] == 15
        mock_repositories['analytics_repo'].get_usage_statistics.assert_called_once_with(30)


class TestStrategySchedulerService:
    """Test strategy scheduler service operations"""
    
    @pytest.fixture
    def mock_scheduler_repo(self):
        """Create mock scheduler repository"""
        return AsyncMock(spec=SQLAlchemyStrategySchedulerRepository)
    
    @pytest.fixture
    def scheduler_service(self, mock_scheduler_repo):
        """Create scheduler service with mock repository"""
        return StrategySchedulerService(mock_scheduler_repo)
    
    @pytest.mark.asyncio
    async def test_get_scheduled_strategies_success(self, scheduler_service, mock_scheduler_repo):
        """Test successful scheduled strategies retrieval"""
        # Setup
        mock_strategies = [
            {
                'id': 1,
                'name': 'Strategy A',
                'schedule_type': StrategyScheduleType.DAILY,
                'schedule_value': '09:30',
                'next_run': datetime.utcnow() + timedelta(hours=1)
            },
            {
                'id': 2,
                'name': 'Strategy B',
                'schedule_type': StrategyScheduleType.HOURLY,
                'schedule_value': '00:00',
                'next_run': datetime.utcnow() + timedelta(minutes=30)
            }
        ]
        mock_scheduler_repo.get_scheduled_strategies.return_value(mock_strategies)
        
        # Execute
        result = await scheduler_service.get_scheduled_strategies()
        
        # Assert
        assert result["success"] is True
        assert len(result["strategies"]) == 2
        assert result["total_count"] == 2
        mock_scheduler_repo.get_scheduled_strategies.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_next_run_times_success(self, scheduler_service, mock_scheduler_repo):
        """Test successful next run times retrieval"""
        # Setup
        strategy_ids = [1, 2]
        mock_scheduler_repo.get_next_run_time.side_effect = [
            datetime.utcnow() + timedelta(hours=1),
            datetime.utcnow() + timedelta(minutes=30)
        ]
        
        # Execute
        result = await scheduler_service.get_next_run_times(strategy_ids)
        
        # Assert
        assert result["success"] is True
        assert "next_run_times" in result
        assert len(result["next_run_times"]) == 2
        assert 1 in result["next_run_times"]
        assert 2 in result["next_run_times"]
        assert mock_scheduler_repo.get_next_run_time.call_count == 2


class TestStrategyTemplateService:
    """Test strategy template service operations"""
    
    @pytest.fixture
    def mock_template_repo(self):
        """Create mock template repository"""
        return AsyncMock(spec=SQLAlchemyStrategyTemplateRepository)
    
    @pytest.fixture
    def template_service(self, mock_template_repo):
        """Create template service with mock repository"""
        return StrategyTemplateService(mock_template_repo)
    
    @pytest.mark.asyncio
    async def test_get_public_templates_success(self, template_service, mock_template_repo):
        """Test successful public templates retrieval"""
        # Setup
        mock_templates = [
            {
                'id': 1,
                'name': 'Momentum Strategy',
                'category': 'momentum',
                'is_public': True,
                'rating': 4.5,
                'usage_count': 150
            },
            {
                'id': 2,
                'name': 'Mean Reversion',
                'category': 'reversal',
                'is_public': True,
                'rating': 4.2,
                'usage_count': 120
            }
        ]
        mock_template_repo.get_public_templates.return_value(mock_templates)
        
        # Execute
        result = await template_service.get_public_templates(50)
        
        # Assert
        assert result["success"] is True
        assert len(result["templates"]) == 2
        assert result["total_count"] == 2
        mock_template_repo.get_public_templates.assert_called_once_with(50)
    
    @pytest.mark.asyncio
    async def test_get_templates_by_category_success(self, template_service, mock_template_repo):
        """Test successful templates by category retrieval"""
        # Setup
        category = "momentum"
        mock_templates = [
            {
                'id': 1,
                'name': 'RSI Momentum',
                'category': 'momentum',
                'is_public': True,
                'rating': 4.5
            }
        ]
        mock_template_repo.get_templates_by_category.return_value(mock_templates)
        
        # Execute
        result = await template_service.get_templates_by_category(category)
        
        # Assert
        assert result["success"] is True
        assert len(result["templates"]) == 1
        assert result["templates"][0]["category"] == "momentum"
        mock_template_repo.get_templates_by_category.assert_called_once_with(category)
    
    @pytest.mark.asyncio
    async def test_get_popular_templates_success(self, template_service, mock_template_repo):
        """Test successful popular templates retrieval"""
        # Setup
        mock_templates = [
            {
                'id': 1,
                'name': 'Popular Strategy',
                'category': 'trend',
                'is_public': True,
                'rating': 4.8,
                'usage_count': 500
            }
        ]
        mock_template_repo.get_popular_templates.return_value(mock_templates)
        
        # Execute
        result = await template_service.get_popular_templates(20)
        
        # Assert
        assert result["success"] is True
        assert len(result["templates"]) == 1
        assert result["templates"][0]["usage_count"] == 500
        mock_template_repo.get_popular_templates.assert_called_once_with(20)
    
    @pytest.mark.asyncio
    async def test_rate_template_success(self, template_service, mock_template_repo):
        """Test successful template rating"""
        # Setup
        template_id = 1
        user_id = "user123"
        rating = 4.5
        mock_template_repo.rate_template.return_value(True)
        
        # Execute
        result = await template_service.rate_template(template_id, user_id, rating)
        
        # Assert
        assert result["success"] is True
        assert "rated successfully" in result["message"].lower()
        mock_template_repo.rate_template.assert_called_once_with(template_id, user_id, rating)
    
    @pytest.mark.asyncio
    async def test_rate_template_not_found(self, template_service, mock_template_repo):
        """Test template rating when template not found"""
        # Setup
        template_id = 999
        user_id = "user123"
        rating = 4.5
        mock_template_repo.rate_template.return_value(False)
        
        # Execute & Assert
        with pytest.raises(NotFoundError) as exc_info:
            await template_service.rate_template(template_id, user_id, rating)
        assert "not found" in str(exc_info.value)


class TestStrategyBacktestService:
    """Test strategy backtest service operations"""
    
    @pytest.fixture
    def mock_backtest_repo(self):
        """Create mock backtest repository"""
        return AsyncMock(spec=SQLAlchemyStrategyBacktestRepository)
    
    @pytest.fixture
    def backtest_service(self, mock_backtest_repo):
        """Create backtest service with mock repository"""
        return StrategyBacktestService(mock_backtest_repo)
    
    @pytest.mark.asyncio
    async def test_compare_backtests_success(self, backtest_service, mock_backtest_repo):
        """Test successful backtest comparison"""
        # Setup
        backtest_ids = ["backtest1", "backtest2"]
        mock_comparison = {
            "backtest_ids": backtest_ids,
            "comparison_metrics": {
                "total_return": {"backtest1": 0.15, "backtest2": 0.12},
                "sharpe_ratio": {"backtest1": 1.8, "backtest2": 1.5},
                "max_drawdown": {"backtest1": 0.08, "backtest2": 0.10},
                "win_rate": {"backtest1": 0.65, "backtest2": 0.60}
            },
            "winner": "backtest1",
            "recommendation": "Backtest1 shows better risk-adjusted returns"
        }
        mock_backtest_repo.compare_backtests.return_value(mock_comparison)
        
        # Execute
        result = await backtest_service.compare_backtests(backtest_ids)
        
        # Assert
        assert result["success"] is True
        assert "comparison" in result
        assert result["comparison"]["winner"] == "backtest1"
        mock_backtest_repo.compare_backtests.assert_called_once_with(backtest_ids)
    
    @pytest.mark.asyncio
    async def test_delete_backtest_success(self, backtest_service, mock_backtest_repo):
        """Test successful backtest deletion"""
        # Setup
        backtest_id = "backtest123"
        mock_backtest_repo.delete_backtest.return_value(True)
        
        # Execute
        result = await backtest_service.delete_backtest(backtest_id)
        
        # Assert
        assert result["success"] is True
        assert "deleted successfully" in result["message"].lower()
        mock_backtest_repo.delete_backtest.assert_called_once_with(backtest_id)
    
    @pytest.mark.asyncio
    async def test_delete_backtest_not_found(self, backtest_service, mock_backtest_repo):
        """Test backtest deletion when not found"""
        # Setup
        backtest_id = "nonexistent"
        mock_backtest_repo.delete_backtest.return_value(False)
        
        # Execute & Assert
        with pytest.raises(NotFoundError) as exc_info:
            await backtest_service.delete_backtest(backtest_id)
        assert "not found" in str(exc_info.value)
