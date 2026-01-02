import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from app.main import app
from app.schemas.options import StockQuoteResponse, OptionsChainResponse


client = TestClient(app)


class TestOptionsAPI:
    """Test options API endpoints"""
    
    @patch("app.api.v1.routers.options.get_options_service")
    def test_get_stock_quote_success(self, mock_get_service):
        """Test getting stock quote successfully"""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.get_stock_quote.return_value = StockQuoteResponse(
            ticker="AAPL",
            price=150.25,
            change=2.50,
            change_percent=1.69,
            volume=50000000
        )
        mock_get_service.return_value = mock_service
        
        # Execute
        response = client.get("/api/v1/options/quote/AAPL")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["ticker"] == "AAPL"
        assert data["price"] == 150.25
        assert data["change"] == 2.50
    
    @patch("app.api.v1.routers.options.get_options_service")
    def test_get_quote_lite_success(self, mock_get_service):
        """Test getting lite quote successfully"""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.get_quote_lite.return_value = type('Response', (), {
            'ticker': 'AAPL',
            'price': 150.25,
            'change': 2.50,
            'dict': lambda: {
                'ticker': 'AAPL',
                'price': 150.25,
                'change': 2.50,
                'change_percent': 1.69
            }
        })()
        mock_get_service.return_value = mock_service
        
        # Execute
        response = client.get("/api/v1/options/quote-lite/AAPL")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["ticker"] == "AAPL"
        assert data["price"] == 150.25
    
    @patch("app.api.v1.routers.options.get_options_service")
    def test_get_options_chain_success(self, mock_get_service):
        """Test getting options chain successfully"""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.get_options_chain.return_value = OptionsChainResponse(
            ticker="AAPL",
            expiry="2024-01-19",
            calls=[
                {
                    "contract_symbol": "AAPL240119C00150000",
                    "strike": 150.0,
                    "expiry": "2024-01-19",
                    "option_type": "CALL",
                    "last_price": 5.25,
                    "volume": 1000
                }
            ],
            puts=[]
        )
        mock_get_service.return_value = mock_service
        
        # Execute
        response = client.get("/api/v1/options/options/AAPL")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["ticker"] == "AAPL"
        assert "calls" in data
        assert "puts" in data
        assert len(data["calls"]) == 1
        assert data["calls"][0]["strike"] == 150.0
    
    @patch("app.api.v1.routers.options.get_options_service")
    def test_get_options_chain_with_expiry(self, mock_get_service):
        """Test getting options chain with specific expiry"""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.get_options_chain.return_value = OptionsChainResponse(
            ticker="AAPL",
            expiry="2024-01-19",
            calls=[],
            puts=[]
        )
        mock_get_service.return_value = mock_service
        
        # Execute
        response = client.get("/api/v1/options/options/AAPL?expiry=2024-01-19")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["expiry"] == "2024-01-19"
    
    @patch("app.api.v1.routers.options.get_options_service")
    def test_get_top_volume_options_success(self, mock_get_service):
        """Test getting top volume options successfully"""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.get_top_volume_options.return_value = type('Response', (), {
            'ticker': 'AAPL',
            'options': [
                {
                    'contract_symbol': 'AAPL240119C00150000',
                    'strike': 150.0,
                    'volume': 1000
                }
            ],
            'dict': lambda: {
                'ticker': 'AAPL',
                'options': [
                    {
                        'contract_symbol': 'AAPL240119C00150000',
                        'strike': 150.0,
                        'volume': 1000
                    }
                ]
            }
        })()
        mock_get_service.return_value = mock_service
        
        # Execute
        response = client.get("/api/v1/options/top-volume/AAPL")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["ticker"] == "AAPL"
        assert "options" in data
        assert len(data["options"]) == 1
    
    @patch("app.api.v1.routers.options.get_options_service")
    def test_get_top_volume_options_with_custom_limit(self, mock_get_service):
        """Test getting top volume options with custom limit"""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.get_top_volume_options.return_value = type('Response', (), {
            'ticker': 'AAPL',
            'options': [],
            'dict': lambda: {'ticker': 'AAPL', 'options': []}
        })()
        mock_get_service.return_value = mock_service
        
        # Execute
        response = client.get("/api/v1/options/top-volume/AAPL?top_n=5")
        
        # Assert
        assert response.status_code == 200
    
    @patch("app.api.v1.routers.options.get_options_service")
    def test_get_stock_history_success(self, mock_get_service):
        """Test getting stock history successfully"""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.get_stock_history.return_value = type('Response', (), {
            'ticker': 'AAPL',
            'period': '3mo',
            'interval': '1d',
            'prices': [
                {
                    'date': '2024-01-01T00:00:00',
                    'open': 148.0,
                    'high': 152.0,
                    'low': 147.0,
                    'close': 150.0,
                    'volume': 50000000
                }
            ],
            'technicals': {'ema_20': 149.5},
            'dict': lambda: {
                'ticker': 'AAPL',
                'period': '3mo',
                'interval': '1d',
                'prices': [
                    {
                        'date': '2024-01-01T00:00:00',
                        'open': 148.0,
                        'high': 152.0,
                        'low': 147.0,
                        'close': 150.0,
                        'volume': 50000000
                    }
                ],
                'technicals': {'ema_20': 149.5}
            }
        })()
        mock_get_service.return_value = mock_service
        
        # Execute
        response = client.get("/api/v1/options/history/AAPL")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["ticker"] == "AAPL"
        assert data["period"] == "3mo"
        assert "prices" in data
        assert len(data["prices"]) == 1
    
    @patch("app.api.v1.routers.options.get_options_service")
    def test_get_stock_history_custom_params(self, mock_get_service):
        """Test getting stock history with custom parameters"""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.get_stock_history.return_value = type('Response', (), {
            'ticker': 'AAPL',
            'period': '1mo',
            'interval': '1h',
            'prices': [],
            'dict': lambda: {'ticker': 'AAPL', 'period': '1mo', 'interval': '1h', 'prices': []}
        })()
        mock_get_service.return_value = mock_service
        
        # Execute
        response = client.get("/api/v1/options/history/AAPL?period=1mo&interval=1h")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["period"] == "1mo"
        assert data["interval"] == "1h"
    
    @patch("app.api.v1.routers.options.get_options_service")
    def test_detect_unusual_activity_success(self, mock_get_service):
        """Test detecting unusual activity successfully"""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.detect_unusual_activity.return_value = type('Response', (), {
            'ticker': 'AAPL',
            'unusual_options': [
                {
                    'contract': {'contract_symbol': 'AAPL240119C00150000'},
                    'reason': 'High volume/interest ratio'
                }
            ],
            'analysis': 'Found 1 contracts with unusual activity',
            'dict': lambda: {
                'ticker': 'AAPL',
                'unusual_options': [
                    {
                        'contract': {'contract_symbol': 'AAPL240119C00150000'},
                        'reason': 'High volume/interest ratio'
                    }
                ],
                'analysis': 'Found 1 contracts with unusual activity'
            }
        })()
        mock_get_service.return_value = mock_service
        
        # Execute
        response = client.get("/api/v1/options/unusual/AAPL")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["ticker"] == "AAPL"
        assert "unusual_options" in data
        assert "analysis" in data
    
    @patch("app.api.v1.routers.options.get_options_service")
    def test_get_option_history_success(self, mock_get_service):
        """Test getting option history successfully"""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.get_option_history.return_value = {
            'contract_symbol': 'AAPL240119C00150000',
            'ticker': 'AAPL',
            'expiry': '2024-01-19',
            'option_type': 'CALL',
            'period': '1mo',
            'interval': '1d',
            'prices': [],
            'note': 'Option historical data approximated using underlying stock prices'
        }
        mock_get_service.return_value = mock_service
        
        # Execute
        response = client.get("/api/v1/options/option-history/AAPL240119C00150000")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["contract_symbol"] == "AAPL240119C00150000"
        assert data["ticker"] == "AAPL"
        assert data["option_type"] == "CALL"
    
    @patch("app.api.v1.routers.options.get_options_service")
    def test_market_scan_success(self, mock_get_service):
        """Test market scan successfully"""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.market_scan.return_value = type('Response', (), {
            'scan_results': [
                {
                    'ticker': 'AAPL',
                    'stock_price': 150.0,
                    'total_options_volume': 10000
                }
            ],
            'dict': lambda: {
                'scan_results': [
                    {
                        'ticker': 'AAPL',
                        'stock_price': 150.0,
                        'total_options_volume': 10000
                    }
                ]
            }
        })()
        mock_get_service.return_value = mock_service
        
        # Execute
        response = client.get("/api/v1/options/scan")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "scan_results" in data
        assert len(data["scan_results"]) > 0
        assert data["scan_results"][0]["ticker"] == "AAPL"
    
    @patch("app.api.v1.routers.options.get_options_service")
    def test_external_service_error_handling(self, mock_get_service):
        """Test external service error handling"""
        # Setup mock
        mock_service = AsyncMock()
        from app.domain.errors import ExternalServiceError
        mock_service.get_stock_quote.side_effect = ExternalServiceError("API error", "yfinance")
        mock_get_service.return_value = mock_service
        
        # Execute
        response = client.get("/api/v1/options/quote/AAPL")
        
        # Assert
        assert response.status_code == 502
        assert "API error" in response.json()["detail"]
    
    @patch("app.api.v1.routers.options.get_options_service")
    def test_validation_error_handling(self, mock_get_service):
        """Test validation error handling"""
        # Setup mock
        mock_service = AsyncMock()
        from app.domain.errors import ValidationError
        mock_service.get_stock_quote.side_effect = ValidationError("Invalid ticker")
        mock_get_service.return_value = mock_service
        
        # Execute
        response = client.get("/api/v1/options/quote/AAPL")
        
        # Assert
        assert response.status_code == 400
        assert "Invalid ticker" in response.json()["detail"]
    
    def test_top_volume_options_validation(self):
        """Test top volume options parameter validation"""
        # Test invalid top_n (too low)
        response = client.get("/api/v1/options/top-volume/AAPL?top_n=0")
        assert response.status_code == 422  # Validation error
        
        # Test invalid top_n (too high)
        response = client.get("/api/v1/options/top-volume/AAPL?top_n=100")
        assert response.status_code == 422  # Validation error
        
        # Test valid top_n
        response = client.get("/api/v1/options/top-volume/AAPL?top_n=25")
        # Should not be validation error (might be service error)
        assert response.status_code != 422
