import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from app.main import app


client = TestClient(app)


class TestStrategiesAPI:
    """Test strategies API endpoints"""
    
    @patch("app.api.v1.routers.strategies.get_strategy_service")
    def test_create_strategy_success(self, mock_get_service):
        """Test creating a strategy successfully"""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.create_strategy.return_value = {
            "success": True,
            "strategy_id": 1,
            "strategy": {
                "id": 1,
                "name": "Test Strategy",
                "strategy_type": "PREDEFINED"
            }
        }
        mock_get_service.return_value = mock_service
        
        # Execute
        response = client.post("/api/v1/strategies/", json={
            "name": "Test Strategy",
            "description": "A test strategy",
            "default_stop_loss_pct": 0.15,
            "default_take_profit_pct": 0.30,
            "notifications_enabled": True
        })
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["strategy_id"] == 1
    
    @patch("app.api.v1.routers.strategies.get_strategy_service")
    def test_create_strategy_validation_error(self, mock_get_service):
        """Test creating a strategy with validation error"""
        # Setup mock
        mock_service = AsyncMock()
        from app.domain.errors import ValidationError
        mock_service.create_strategy.side_effect = ValidationError("Stop loss must be less than take profit")
        mock_get_service.return_value = mock_service
        
        # Execute
        response = client.post("/api/v1/strategies/", json={
            "name": "Test Strategy",
            "default_stop_loss_pct": 0.40,  # Invalid
            "default_take_profit_pct": 0.30
        })
        
        # Assert
        assert response.status_code == 400
        assert "Stop loss must be less than take profit" in response.json()["detail"]
    
    @patch("app.api.v1.routers.strategies.get_strategy_service")
    def test_list_strategies_success(self, mock_get_service):
        """Test listing strategies successfully"""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.list_strategies.return_value = [
            {
                "id": 1,
                "name": "Strategy 1",
                "strategy_type": "PREDEFINED"
            },
            {
                "id": 2,
                "name": "Strategy 2",
                "strategy_type": "CUSTOM"
            }
        ]
        mock_get_service.return_value = mock_service
        
        # Execute
        response = client.get("/api/v1/strategies/")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["strategy_type"] == "PREDEFINED"
    
    @patch("app.api.v1.routers.strategies.get_strategy_service")
    def test_list_strategies_with_filters(self, mock_get_service):
        """Test listing strategies with filters"""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.list_strategies.return_value = [
            {
                "id": 1,
                "name": "Strategy 1",
                "strategy_type": "PREDEFINED"
            }
        ]
        mock_get_service.return_value = mock_service
        
        # Execute
        response = client.get("/api/v1/strategies/?strategy_type=PREDEFINED&limit=10")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["strategy_type"] == "PREDEFINED"
    
    @patch("app.api.v1.routers.strategies.get_strategy_service")
    def test_get_strategy_by_id_success(self, mock_get_service):
        """Test getting a single strategy by ID"""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.get_strategy_by_id.return_value = {
            "id": 1,
            "name": "Test Strategy",
            "strategy_type": "PREDEFINED"
        }
        mock_get_service.return_value = mock_service
        
        # Execute
        response = client.get("/api/v1/strategies/1")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["name"] == "Test Strategy"
    
    @patch("app.api.v1.routers.strategies.get_strategy_service")
    def test_get_strategy_by_id_not_found(self, mock_get_service):
        """Test getting a non-existent strategy"""
        # Setup mock
        mock_service = AsyncMock()
        from app.domain.errors import NotFoundError
        mock_service.get_strategy_by_id.side_effect = NotFoundError("Strategy with ID 999 not found")
        mock_get_service.return_value = mock_service
        
        # Execute
        response = client.get("/api/v1/strategies/999")
        
        # Assert
        assert response.status_code == 404
        assert "Strategy with ID 999 not found" in response.json()["detail"]
    
    @patch("app.api.v1.routers.strategies.get_strategy_service")
    def test_update_strategy_success(self, mock_get_service):
        """Test updating a strategy successfully"""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.update_strategy.return_value = {
            "success": True,
            "strategy": {
                "id": 1,
                "name": "Updated Strategy"
            }
        }
        mock_get_service.return_value = mock_service
        
        # Execute
        response = client.put("/api/v1/strategies/1", json={
            "name": "Updated Strategy",
            "default_stop_loss_pct": 0.20
        })
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["strategy"]["name"] == "Updated Strategy"
    
    @patch("app.api.v1.routers.strategies.get_strategy_service")
    def test_delete_strategy_success(self, mock_get_service):
        """Test deleting a strategy successfully"""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.delete_strategy.return_value = {
            "success": True,
            "message": "Strategy 1 deleted successfully"
        }
        mock_get_service.return_value = mock_service
        
        # Execute
        response = client.delete("/api/v1/strategies/1")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "deleted successfully" in data["message"]
    
    @patch("app.api.v1.routers.strategies.get_strategy_service")
    def test_get_strategy_statistics(self, mock_get_service):
        """Test getting strategy statistics"""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.get_strategy_statistics.return_value = type('Stats', (), {
            'total_strategies': 10,
            'active_strategies': 3,
            'custom_strategies': 4,
            'predefined_strategies': 6,
            'strategies_with_trades': 5,
            'dict': lambda: {
                'total_strategies': 10,
                'active_strategies': 3,
                'custom_strategies': 4,
                'predefined_strategies': 6,
                'strategies_with_trades': 5
            }
        })()
        mock_get_service.return_value = mock_service
        
        # Execute
        response = client.get("/api/v1/strategies/stats/summary")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total_strategies"] == 10
        assert data["custom_strategies"] == 4
    
    @patch("app.api.v1.routers.strategies.get_strategy_service")
    def test_search_strategies(self, mock_get_service):
        """Test searching strategies"""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.search_strategies.return_value = [
            {
                "id": 1,
                "name": "Momentum Strategy",
                "description": "Momentum-based trading"
            }
        ]
        mock_get_service.return_value = mock_service
        
        # Execute
        response = client.get("/api/v1/strategies/search?q=Momentum")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert "Momentum" in data[0]["name"]


class TestCustomStrategiesAPI:
    """Test custom strategies API endpoints"""
    
    @patch("app.api.v1.routers.strategies.get_custom_strategy_service")
    def test_create_custom_strategy_success(self, mock_get_service):
        """Test creating a custom strategy successfully"""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.create_custom_strategy.return_value = {
            "success": True,
            "strategy_id": 1,
            "strategy": {
                "id": 1,
                "name": "Custom Test Strategy",
                "code": "def execute(): pass"
            }
        }
        mock_get_service.return_value = mock_service
        
        # Execute
        response = client.post("/api/v1/strategies/custom/", json={
            "name": "Custom Test Strategy",
            "code": "def execute():\n    return 'test'",
            "schedule_type": "INTERVAL",
            "schedule_value": "300",
            "execution_type": "HOST"
        })
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["strategy_id"] == 1
    
    @patch("app.api.v1.routers.strategies.get_custom_strategy_service")
    def test_execute_custom_strategy(self, mock_get_service):
        """Test executing a custom strategy"""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.execute_custom_strategy.return_value = {
            "execution_id": 1,
            "strategy_id": 1,
            "status": "SUCCESS",
            "trades_generated": 0
        }
        mock_get_service.return_value = mock_service
        
        # Execute
        response = client.post("/api/v1/strategies/custom/1/execute", json={
            "dry_run": True,
            "parameters": {"test_param": "value"}
        })
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "SUCCESS"
        assert data["dry_run"] is True
    
    @patch("app.api.v1.routers.strategies.get_custom_strategy_service")
    def test_toggle_strategy_activation(self, mock_get_service):
        """Test toggling strategy activation"""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.toggle_strategy_activation.return_value = {
            "success": True,
            "message": "Custom strategy 1 activated successfully"
        }
        mock_get_service.return_value = mock_service
        
        # Execute
        response = client.post("/api/v1/strategies/custom/1/toggle", json=True)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "activated" in data["message"]
    
    @patch("app.api.v1.routers.strategies.get_custom_strategy_service")
    def test_batch_update_custom_strategies(self, mock_get_service):
        """Test batch updating custom strategies"""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.batch_update_custom_strategies.return_value = {
            "success": True,
            "updated_count": 3,
            "message": "Activated 3 strategies"
        }
        mock_get_service.return_value = mock_service
        
        # Execute
        response = client.put("/api/v1/strategies/custom/batch/update", json={
            "strategy_ids": [1, 2, 3],
            "action": "activate"
        })
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["updated_count"] == 3


class TestStrategyAnalyticsAPI:
    """Test strategy analytics API endpoints"""
    
    @patch("app.api.v1.routers.strategies.get_analytics_service")
    def test_get_strategy_performance(self, mock_get_service):
        """Test getting strategy performance"""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.get_strategy_performance.return_value = type('Performance', (), {
            'strategy_id': 1,
            'period': '3mo',
            'total_trades': 50,
            'win_rate': 65.0,
            'total_pnl': 2500.0,
            'dict': lambda: {
                'strategy_id': 1,
                'period': '3mo',
                'total_trades': 50,
                'win_rate': 65.0,
                'total_pnl': 2500.0
            }
        })()
        mock_get_service.return_value = mock_service
        
        # Execute
        response = client.get("/api/v1/strategies/analytics/performance/1?period=3mo")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["strategy_id"] == 1
        assert data["win_rate"] == 65.0
    
    @patch("app.api.v1.routers.strategies.get_analytics_service")
    def test_backtest_strategy(self, mock_get_service):
        """Test strategy backtesting"""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.backtest_strategy.return_value = type('Backtest', (), {
            'strategy_id': 1,
            'strategy_name': 'Test Strategy',
            'initial_capital': 10000,
            'final_capital': 12000,
            'total_return_pct': 20.0,
            'dict': lambda: {
                'strategy_id': 1,
                'strategy_name': 'Test Strategy',
                'initial_capital': 10000,
                'final_capital': 12000,
                'total_return_pct': 20.0
            }
        })()
        mock_get_service.return_value = mock_service
        
        # Execute
        response = client.post("/api/v1/strategies/analytics/backtest", json={
            "strategy_id": 1,
            "start_date": "2024-01-01T00:00:00",
            "end_date": "2024-12-31T00:00:00",
            "initial_capital": 10000
        })
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["strategy_id"] == 1
        assert data["total_return_pct"] == 20.0
    
    @patch("app.api.v1.routers.strategies.get_analytics_service")
    def test_compare_strategies(self, mock_get_service):
        """Test strategy comparison"""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.compare_strategies.return_value = {
            "period": "3mo",
            "strategies_compared": 2,
            "results": [
                {"strategy_id": 1, "total_pnl": 1000},
                {"strategy_id": 2, "total_pnl": 2000}
            ]
        }
        mock_get_service.return_value = mock_service
        
        # Execute
        response = client.post("/api/v1/strategies/analytics/compare", json={
            "strategy_ids": [1, 2]
        })
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["strategies_compared"] == 2
        assert len(data["results"]) == 2
    
    @patch("app.api.v1.routers.strategies.get_analytics_service")
    def test_get_strategy_recommendations(self, mock_get_service):
        """Test getting strategy recommendations"""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.get_strategy_recommendations.return_value = type('Recommendations', (), {
            'recommendations': [
                {
                    'name': 'Momentum Scalping',
                    'risk_level': 'medium',
                    'confidence': 0.85
                }
            ],
            'analysis_summary': 'Generated strategy recommendations',
            'confidence_score': 0.85,
            'generated_at': '2024-01-01T00:00:00',
            'dict': lambda: {
                'recommendations': [
                    {
                        'name': 'Momentum Scalping',
                        'risk_level': 'medium',
                        'confidence': 0.85
                    }
                ],
                'analysis_summary': 'Generated strategy recommendations',
                'confidence_score': 0.85,
                'generated_at': '2024-01-01T00:00:00'
            }
        })()
        mock_get_service.return_value = mock_service
        
        # Execute
        response = client.post("/api/v1/strategies/analytics/recommendations", json={
            "risk_tolerance": "medium",
            "time_horizon": "medium",
            "max_strategies": 5
        })
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["recommendations"]) == 1
        assert data["confidence_score"] == 0.85
