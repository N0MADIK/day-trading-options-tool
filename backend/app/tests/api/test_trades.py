import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from app.main import app


client = TestClient(app)


class TestTradesAPI:
    """Test trades API endpoints"""
    
    @patch("app.api.v1.routers.trades.get_trade_service")
    def test_create_trade_success(self, mock_get_service):
        """Test creating a trade successfully"""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.create_trade.return_value = {
            "success": True,
            "trade_id": 1,
            "trade": {
                "id": 1,
                "contract_symbol": "AAPL240119C00150000",
                "ticker": "AAPL",
                "entry_price": 5.25,
                "status": "OPEN"
            }
        }
        mock_get_service.return_value = mock_service
        
        # Execute
        response = client.post("/api/v1/trades/", json={
            "contract_symbol": "AAPL240119C00150000",
            "ticker": "AAPL",
            "entry_price": 5.25,
            "quantity": 2,
            "stop_loss": 4.50,
            "take_profit": 6.00
        })
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["trade_id"] == 1
        assert data["trade"]["contract_symbol"] == "AAPL240119C00150000"
    
    @patch("app.api.v1.routers.trades.get_trade_service")
    def test_create_trade_validation_error(self, mock_get_service):
        """Test creating a trade with validation error"""
        # Setup mock
        mock_service = AsyncMock()
        from app.domain.errors import ValidationError
        mock_service.create_trade.side_effect = ValidationError("Stop loss must be less than take profit")
        mock_get_service.return_value = mock_service
        
        # Execute
        response = client.post("/api/v1/trades/", json={
            "contract_symbol": "AAPL240119C00150000",
            "ticker": "AAPL",
            "entry_price": 5.25,
            "stop_loss": 6.00,  # Invalid: higher than take profit
            "take_profit": 5.50
        })
        
        # Assert
        assert response.status_code == 400
        assert "Stop loss must be less than take profit" in response.json()["detail"]
    
    @patch("app.api.v1.routers.trades.get_trade_service")
    def test_list_trades_success(self, mock_get_service):
        """Test listing trades successfully"""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.list_trades.return_value = [
            {
                "id": 1,
                "contract_symbol": "AAPL240119C00150000",
                "ticker": "AAPL",
                "entry_price": 5.25,
                "status": "OPEN"
            },
            {
                "id": 2,
                "contract_symbol": "MSFT240119C00150000",
                "ticker": "MSFT",
                "entry_price": 3.75,
                "status": "OPEN"
            }
        ]
        mock_get_service.return_value = mock_service
        
        # Execute
        response = client.get("/api/v1/trades/")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["contract_symbol"] == "AAPL240119C00150000"
    
    @patch("app.api.v1.routers.trades.get_trade_service")
    def test_list_trades_with_filters(self, mock_get_service):
        """Test listing trades with filters"""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.list_trades.return_value = [
            {
                "id": 1,
                "contract_symbol": "AAPL240119C00150000",
                "status": "OPEN"
            }
        ]
        mock_get_service.return_value = mock_service
        
        # Execute
        response = client.get("/api/v1/trades/?status=OPEN&ticker=AAPL&limit=10")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["status"] == "OPEN"
    
    @patch("app.api.v1.routers.trades.get_trade_service")
    def test_get_open_trades_success(self, mock_get_service):
        """Test getting open trades successfully"""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.get_open_trades.return_value = [
            {
                "id": 1,
                "contract_symbol": "AAPL240119C00150000",
                "status": "OPEN"
            }
        ]
        mock_get_service.return_value = mock_service
        
        # Execute
        response = client.get("/api/v1/trades/open")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["status"] == "OPEN"
    
    @patch("app.api.v1.routers.trades.get_trade_service")
    def test_get_trade_by_id_success(self, mock_get_service):
        """Test getting a single trade by ID"""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.get_trade_by_id.return_value = {
            "id": 1,
            "contract_symbol": "AAPL240119C00150000",
            "ticker": "AAPL",
            "entry_price": 5.25,
            "status": "OPEN"
        }
        mock_get_service.return_value = mock_service
        
        # Execute
        response = client.get("/api/v1/trades/1")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["contract_symbol"] == "AAPL240119C00150000"
    
    @patch("app.api.v1.routers.trades.get_trade_service")
    def test_get_trade_by_id_not_found(self, mock_get_service):
        """Test getting a non-existent trade"""
        # Setup mock
        mock_service = AsyncMock()
        from app.domain.errors import NotFoundError
        mock_service.get_trade_by_id.side_effect = NotFoundError("Trade with ID 999 not found")
        mock_get_service.return_value = mock_service
        
        # Execute
        response = client.get("/api/v1/trades/999")
        
        # Assert
        assert response.status_code == 404
        assert "Trade with ID 999 not found" in response.json()["detail"]
    
    @patch("app.api.v1.routers.trades.get_trade_service")
    def test_update_trade_success(self, mock_get_service):
        """Test updating a trade successfully"""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.update_trade.return_value = {
            "success": True,
            "trade": {
                "id": 1,
                "contract_symbol": "AAPL240119C00150000",
                "stop_loss": 4.25,
                "take_profit": 6.50
            }
        }
        mock_get_service.return_value = mock_service
        
        # Execute
        response = client.put("/api/v1/trades/1", json={
            "stop_loss": 4.25,
            "take_profit": 6.50
        })
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["trade"]["stop_loss"] == 4.25
    
    @patch("app.api.v1.routers.trades.get_trade_service")
    def test_close_trade_success(self, mock_get_service):
        """Test closing a trade successfully"""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.close_trade.return_value = {
            "success": True,
            "trade": {
                "id": 1,
                "status": "CLOSED_WIN",
                "pnl": 200.0,
                "exit_price": 6.25
            },
            "pnl": 200.0,
            "status": "CLOSED_WIN"
        }
        mock_get_service.return_value = mock_service
        
        # Execute
        response = client.post("/api/v1/trades/1/close", json={
            "exit_price": 6.25
        })
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["status"] == "CLOSED_WIN"
        assert data["pnl"] == 200.0
    
    @patch("app.api.v1.routers.trades.get_trade_service")
    def test_close_trade_already_closed(self, mock_get_service):
        """Test closing an already closed trade"""
        # Setup mock
        mock_service = AsyncMock()
        from app.domain.errors import ConflictError
        mock_service.close_trade.side_effect = ConflictError("Trade is already closed")
        mock_get_service.return_value = mock_service
        
        # Execute
        response = client.post("/api/v1/trades/1/close", json={
            "exit_price": 6.25
        })
        
        # Assert
        assert response.status_code == 409
        assert "Trade is already closed" in response.json()["detail"]
    
    @patch("app.api.v1.routers.trades.get_trade_service")
    def test_delete_trade_success(self, mock_get_service):
        """Test deleting a trade successfully"""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.delete_trade.return_value = {
            "success": True,
            "message": "Trade 1 deleted successfully"
        }
        mock_get_service.return_value = mock_service
        
        # Execute
        response = client.delete("/api/v1/trades/1")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "deleted successfully" in data["message"]
    
    @patch("app.api.v1.routers.trades.get_trade_service")
    def test_get_trade_statistics(self, mock_get_service):
        """Test getting trade statistics"""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.get_trade_statistics.return_value = type('Stats', (), {
            'total_trades': 100,
            'open_trades': 5,
            'closed_trades': 95,
            'wins': 60,
            'losses': 35,
            'win_rate': 63.2,
            'total_pnl': 2500.50,
            'dict': lambda: {
                'total_trades': 100,
                'open_trades': 5,
                'closed_trades': 95,
                'wins': 60,
                'losses': 35,
                'win_rate': 63.2,
                'total_pnl': 2500.50
            }
        })()
        mock_get_service.return_value = mock_service
        
        # Execute
        response = client.get("/api/v1/trades/stats/summary")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total_trades"] == 100
        assert data["win_rate"] == 63.2
    
    @patch("app.api.v1.routers.trades.get_trade_service")
    def test_batch_update_trades(self, mock_get_service):
        """Test batch updating trades"""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.batch_update_trades.return_value = {
            "success": True,
            "updated_count": 3,
            "message": "Updated 3 trades"
        }
        mock_get_service.return_value = mock_service
        
        # Execute
        response = client.put("/api/v1/trades/batch/update", json={
            "trade_ids": [1, 2, 3],
            "updates": {
                "stop_loss": 4.00,
                "take_profit": 6.00
            }
        })
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["updated_count"] == 3
    
    @patch("app.api.v1.routers.trades.get_trade_service")
    def test_batch_close_trades(self, mock_get_service):
        """Test batch closing trades"""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.batch_close_trades.return_value = {
            "success": True,
            "total_count": 2,
            "successful_count": 2,
            "failed_count": 0,
            "results": [
                {"trade_id": 1, "success": True},
                {"trade_id": 2, "success": True}
            ]
        }
        mock_get_service.return_value = mock_service
        
        # Execute
        response = client.post("/api/v1/trades/batch/close", json={
            "trade_ids": [1, 2],
            "exit_prices": [6.25, 4.75]
        })
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["successful_count"] == 2
    
    @patch("app.api.v1.routers.trades.get_trade_service")
    def test_search_trades(self, mock_get_service):
        """Test searching trades"""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.search_trades.return_value = [
            {
                "id": 1,
                "contract_symbol": "AAPL240119C00150000",
                "notes": "Good entry point"
            }
        ]
        mock_get_service.return_value = mock_service
        
        # Execute
        response = client.get("/api/v1/trades/search?q=AAPL")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert "AAPL" in data[0]["contract_symbol"]
    
    @patch("app.api.v1.routers.trades.get_trade_service")
    def test_search_trades_invalid_query(self, mock_get_service):
        """Test searching trades with invalid query"""
        # Execute
        response = client.get("/api/v1/trades/search?q=A")
        
        # Assert
        assert response.status_code == 422  # Validation error
    
    @patch("app.api.v1.routers.trades.get_trade_service")
    def test_get_risk_metrics(self, mock_get_service):
        """Test getting risk metrics"""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.get_risk_metrics.return_value = {
            "open_positions": 5,
            "trades_at_risk": 3,
            "total_risk_exposure": 1500.00,
            "risk_percentage": 60.0
        }
        mock_get_service.return_value = mock_service
        
        # Execute
        response = client.get("/api/v1/trades/risk/metrics")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["open_positions"] == 5
        assert data["risk_percentage"] == 60.0
    
    @patch("app.api.v1.routers.trades.get_trade_service")
    def test_get_trades_by_ticker(self, mock_get_service):
        """Test getting trades by ticker"""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.get_trades_by_ticker.return_value = [
            {
                "id": 1,
                "contract_symbol": "AAPL240119C00150000",
                "ticker": "AAPL"
            }
        ]
        mock_get_service.return_value = mock_service
        
        # Execute
        response = client.get("/api/v1/trades/ticker/AAPL")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["ticker"] == "AAPL"
    
    @patch("app.api.v1.routers.trades.get_trade_service")
    def test_get_performance_analysis(self, mock_get_service):
        """Test getting performance analysis"""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.get_trade_performance_analysis.return_value = type('Analysis', (), {
            'period': '3mo',
            'group_by': 'month',
            'data_points': [
                {'period': '2024-01', 'trades': 10, 'win_rate': 60.0}
            ],
            'dict': lambda: {
                'period': '3mo',
                'group_by': 'month',
                'data_points': [
                    {'period': '2024-01', 'trades': 10, 'win_rate': 60.0}
                ]
            }
        })()
        mock_get_service.return_value = mock_service
        
        # Execute
        response = client.get("/api/v1/trades/analysis/performance?period=3mo&group_by=month")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["period"] == "3mo"
        assert data["group_by"] == "month"
        assert len(data["data_points"]) == 1
