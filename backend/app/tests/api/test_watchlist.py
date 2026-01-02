import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from app.main import app
from app.schemas.watchlist import TickerWatchlistResponse, OptionWatchlistResponse


client = TestClient(app)


class TestWatchlistAPI:
    """Test watchlist API endpoints"""
    
    @patch("app.core.deps.get_watchlist_service")
    def test_get_tickers_success(self, mock_get_service):
        """Test getting all tickers successfully"""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.get_all_tickers.return_value = [
            TickerWatchlistResponse(
                id=1,
                symbol="AAPL",
                category="Tech",
                added_at="2024-01-01T00:00:00"
            )
        ]
        mock_get_service.return_value = mock_service
        
        # Execute
        response = client.get("/api/v1/watchlist/tickers")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "tickers" in data
        assert len(data["tickers"]) == 1
        assert data["tickers"][0]["symbol"] == "AAPL"
    
    @patch("app.core.deps.get_watchlist_service")
    def test_add_ticker_success(self, mock_get_service):
        """Test adding a ticker successfully"""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.add_ticker.return_value = TickerWatchlistResponse(
            id=1,
            symbol="AAPL",
            category="Tech",
            added_at="2024-01-01T00:00:00"
        )
        mock_get_service.return_value = mock_service
        
        # Execute
        response = client.post(
            "/api/v1/watchlist/tickers",
            json={"symbol": "AAPL", "category": "Tech"}
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "AAPL"
        assert data["category"] == "Tech"
    
    @patch("app.core.deps.get_watchlist_service")
    def test_add_ticker_conflict(self, mock_get_service):
        """Test adding a ticker that already exists"""
        # Setup mock
        mock_service = AsyncMock()
        from app.domain.errors import ConflictError
        mock_service.add_ticker.side_effect = ConflictError("Ticker AAPL already exists")
        mock_get_service.return_value = mock_service
        
        # Execute
        response = client.post(
            "/api/v1/watchlist/tickers",
            json={"symbol": "AAPL", "category": "Tech"}
        )
        
        # Assert
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]
    
    @patch("app.core.deps.get_watchlist_service")
    def test_remove_ticker_success(self, mock_get_service):
        """Test removing a ticker successfully"""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.remove_ticker.return_value = True
        mock_get_service.return_value = mock_service
        
        # Execute
        response = client.delete("/api/v1/watchlist/tickers/AAPL")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "removed from watchlist" in data["message"]
    
    @patch("app.core.deps.get_watchlist_service")
    def test_remove_ticker_not_found(self, mock_get_service):
        """Test removing a ticker that doesn't exist"""
        # Setup mock
        mock_service = AsyncMock()
        from app.domain.errors import NotFoundError
        mock_service.remove_ticker.side_effect = NotFoundError("Ticker AAPL not found")
        mock_get_service.return_value = mock_service
        
        # Execute
        response = client.delete("/api/v1/watchlist/tickers/AAPL")
        
        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    @patch("app.core.deps.get_watchlist_service")
    def test_get_options_success(self, mock_get_service):
        """Test getting all options successfully"""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.get_all_options.return_value = [
            OptionWatchlistResponse(
                id=1,
                contract_symbol="AAPL240119C00150000",
                ticker="AAPL",
                strike=150.0,
                expiry="2024-01-19",
                option_type="CALL",
                notes="Test option",
                added_at="2024-01-01T00:00:00"
            )
        ]
        mock_get_service.return_value = mock_service
        
        # Execute
        response = client.get("/api/v1/watchlist/options")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "options" in data
        assert len(data["options"]) == 1
        assert data["options"][0]["contract_symbol"] == "AAPL240119C00150000"
    
    @patch("app.core.deps.get_watchlist_service")
    def test_add_option_success(self, mock_get_service):
        """Test adding an option successfully"""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.add_option.return_value = OptionWatchlistResponse(
            id=1,
            contract_symbol="AAPL240119C00150000",
            ticker="AAPL",
            strike=150.0,
            expiry="2024-01-19",
            option_type="CALL",
            notes="Test option",
            added_at="2024-01-01T00:00:00"
        )
        mock_get_service.return_value = mock_service
        
        # Execute
        response = client.post(
            "/api/v1/watchlist/options",
            json={
                "contract_symbol": "AAPL240119C00150000",
                "ticker": "AAPL",
                "strike": 150.0,
                "expiry": "2024-01-19",
                "option_type": "CALL",
                "notes": "Test option"
            }
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["contract_symbol"] == "AAPL240119C00150000"
        assert data["ticker"] == "AAPL"
        assert data["strike"] == 150.0
    
    @patch("app.core.deps.get_watchlist_service")
    def test_check_option_in_watchlist(self, mock_get_service):
        """Test checking if option exists in watchlist"""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.check_option_in_watchlist.return_value = type('obj', (object,), {'in_watchlist': True})()
        mock_get_service.return_value = mock_service
        
        # Execute
        response = client.get("/api/v1/watchlist/options/check/AAPL240119C00150000")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "in_watchlist" in data
        assert data["in_watchlist"] is True


class TestHealthAPI:
    """Test health check endpoints"""
    
    def test_health_check(self):
        """Test basic health check"""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data
        assert "version" in data
    
    def test_root_endpoint(self):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "status" in data
