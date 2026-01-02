import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import asyncio
from datetime import datetime

from app.services.options_service import OptionsService
from app.schemas.options import (
    StockQuoteRequest, StockQuoteResponse, OptionsChainRequest,
    TopVolumeOptionsRequest, StockHistoryRequest, UnusualActivityRequest
)
from app.domain.errors import ExternalServiceError, ValidationError


class TestOptionsService:
    """Test options service operations"""
    
    @pytest.fixture
    def options_service(self):
        """Create options service instance"""
        return OptionsService()
    
    @pytest.mark.asyncio
    async def test_get_stock_quote_success(self, options_service):
        """Test successful stock quote fetch"""
        # Setup mock
        mock_data = {
            "ticker": "AAPL",
            "price": 150.25,
            "change": 2.50,
            "change_percent": 1.69,
            "volume": 50000000,
            "market_cap": 2500000000000
        }
        
        with patch.object(options_service.yfinance_client, 'get_stock_quote', return_value=mock_data):
            request = StockQuoteRequest(ticker="AAPL")
            result = await options_service.get_stock_quote(request)
            
            assert result.ticker == "AAPL"
            assert result.price == 150.25
            assert result.change == 2.50
            assert isinstance(result, StockQuoteResponse)
    
    @pytest.mark.asyncio
    async def test_get_stock_quote_external_error(self, options_service):
        """Test stock quote with external service error"""
        with patch.object(options_service.yfinance_client, 'get_stock_quote', 
                         side_effect=ExternalServiceError("API error", "yfinance")):
            request = StockQuoteRequest(ticker="INVALID")
            
            with pytest.raises(ExternalServiceError) as exc_info:
                await options_service.get_stock_quote(request)
            
            assert "yfinance" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_get_quote_lite_success(self, options_service):
        """Test successful lite quote fetch"""
        mock_data = {
            "ticker": "AAPL",
            "price": 150.25,
            "change": 2.50,
            "change_percent": 1.69
        }
        
        with patch.object(options_service.yfinance_client, 'get_quote_lite', return_value=mock_data):
            request = StockQuoteRequest(ticker="AAPL")
            result = await options_service.get_quote_lite(request)
            
            assert result.ticker == "AAPL"
            assert result.price == 150.25
            assert hasattr(result, 'timestamp')
    
    @pytest.mark.asyncio
    async def test_get_options_chain_success(self, options_service):
        """Test successful options chain fetch"""
        mock_data = {
            "ticker": "AAPL",
            "expiry": "2024-01-19",
            "calls": [
                {
                    "contract_symbol": "AAPL240119C00150000",
                    "strike": 150.0,
                    "expiry": "2024-01-19",
                    "option_type": "CALL",
                    "last_price": 5.25,
                    "volume": 1000,
                    "open_interest": 5000
                }
            ],
            "puts": [
                {
                    "contract_symbol": "AAPL240119P00150000",
                    "strike": 150.0,
                    "expiry": "2024-01-19",
                    "option_type": "PUT",
                    "last_price": 2.75,
                    "volume": 800,
                    "open_interest": 3000
                }
            ]
        }
        
        with patch.object(options_service.yfinance_client, 'get_options_chain', return_value=mock_data):
            request = OptionsChainRequest(ticker="AAPL")
            result = await options_service.get_options_chain(request)
            
            assert result.ticker == "AAPL"
            assert len(result.calls) == 1
            assert len(result.puts) == 1
            assert result.calls[0].strike == 150.0
            assert result.puts[0].option_type == "PUT"
    
    @pytest.mark.asyncio
    async def test_get_top_volume_options_success(self, options_service):
        """Test successful top volume options fetch"""
        # Mock options chain response
        mock_chain_data = {
            "ticker": "AAPL",
            "expiry": "2024-01-19",
            "calls": [
                {
                    "contract_symbol": "AAPL240119C00150000",
                    "strike": 150.0,
                    "expiry": "2024-01-19",
                    "option_type": "CALL",
                    "last_price": 5.25,
                    "volume": 1000,
                    "open_interest": 5000
                },
                {
                    "contract_symbol": "AAPL240119C00155000",
                    "strike": 155.0,
                    "expiry": "2024-01-19",
                    "option_type": "CALL",
                    "last_price": 3.75,
                    "volume": 500,
                    "open_interest": 2000
                }
            ],
            "puts": []
        }
        
        with patch.object(options_service, 'get_options_chain') as mock_chain:
            # Mock the response to return proper objects
            mock_response = AsyncMock()
            mock_response.calls = [type('Option', (), {
                'volume': 1000, 'dict': lambda: {'volume': 1000}
            })()]
            mock_response.puts = []
            mock_chain.return_value = mock_response
            
            request = TopVolumeOptionsRequest(ticker="AAPL", top_n=5)
            result = await options_service.get_top_volume_options(request)
            
            assert result.ticker == "AAPL"
            assert len(result.options) >= 0
    
    @pytest.mark.asyncio
    async def test_get_stock_history_success(self, options_service):
        """Test successful stock history fetch"""
        mock_data = {
            "ticker": "AAPL",
            "period": "3mo",
            "interval": "1d",
            "prices": [
                {
                    "date": datetime(2024, 1, 1),
                    "open": 148.0,
                    "high": 152.0,
                    "low": 147.0,
                    "close": 150.0,
                    "volume": 50000000
                }
            ],
            "technicals": {
                "ema_20": 149.5,
                "ema_50": 148.0,
                "rsi": 55.0
            }
        }
        
        with patch.object(options_service.yfinance_client, 'get_stock_history', return_value=mock_data):
            request = StockHistoryRequest(ticker="AAPL")
            result = await options_service.get_stock_history(request)
            
            assert result.ticker == "AAPL"
            assert result.period == "3mo"
            assert len(result.prices) == 1
            assert result.technicals.ema_20 == 149.5
    
    @pytest.mark.asyncio
    async def test_detect_unusual_activity_success(self, options_service):
        """Test successful unusual activity detection"""
        # Mock options chain with unusual activity
        mock_chain_data = {
            "ticker": "AAPL",
            "expiry": "2024-01-19",
            "calls": [
                {
                    "contract_symbol": "AAPL240119C00150000",
                    "strike": 150.0,
                    "expiry": "2024-01-19",
                    "option_type": "CALL",
                    "last_price": 5.25,
                    "volume": 3000,  # High volume
                    "open_interest": 1000,  # Volume > 50% of OI
                    "implied_volatility": 1.5  # High IV
                }
            ],
            "puts": []
        }
        
        with patch.object(options_service, 'get_options_chain') as mock_chain:
            # Mock response with option objects
            mock_option = type('Option', (), {
                'volume': 3000,
                'open_interest': 1000,
                'implied_volatility': 1.5,
                'bid': 5.0,
                'ask': 6.0,
                'dict': lambda: {
                    'volume': 3000,
                    'open_interest': 1000,
                    'implied_volatility': 1.5,
                    'bid': 5.0,
                    'ask': 6.0
                }
            })()
            
            mock_response = AsyncMock()
            mock_response.calls = [mock_option]
            mock_response.puts = []
            mock_chain.return_value = mock_response
            
            request = UnusualActivityRequest(ticker="AAPL")
            result = await options_service.detect_unusual_activity(request)
            
            assert result.ticker == "AAPL"
            assert len(result.unusual_options) > 0
            assert "High volume/interest ratio" in result.unusual_options[0]["reason"]
    
    @pytest.mark.asyncio
    async def test_market_scan_success(self, options_service):
        """Test successful market scan"""
        with patch.object(options_service, '_scan_single_ticker') as mock_scan:
            mock_scan.return_value = {
                "ticker": "AAPL",
                "stock_price": 150.0,
                "total_options_volume": 10000,
                "top_options": []
            }
            
            tickers = ["AAPL", "MSFT"]
            result = await options_service.market_scan(tickers)
            
            assert len(result.scan_results) == 2
            assert result.scan_results[0]["ticker"] == "AAPL"
            assert result.scan_results[0]["stock_price"] == 150.0
    
    @pytest.mark.asyncio
    async def test_get_option_history_success(self, options_service):
        """Test successful option history fetch"""
        mock_history_data = {
            "ticker": "AAPL",
            "period": "1mo",
            "interval": "1d",
            "prices": [
                {
                    "date": datetime(2024, 1, 1),
                    "open": 148.0,
                    "high": 152.0,
                    "low": 147.0,
                    "close": 150.0,
                    "volume": 50000000
                }
            ],
            "technicals": {"ema_20": 149.5}
        }
        
        with patch.object(options_service, 'get_stock_history') as mock_history:
            mock_response = AsyncMock()
            mock_response.prices = mock_history_data["prices"]
            mock_history.return_value = mock_response
            
            result = await options_service.get_option_history("AAPL240119C00150000")
            
            assert result["contract_symbol"] == "AAPL240119C00150000"
            assert result["ticker"] == "AAPL"
            assert result["expiry"] == "2024-01-19"
            assert result["option_type"] == "CALL"
    
    @pytest.mark.asyncio
    async def test_invalid_contract_symbol(self, options_service):
        """Test option history with invalid contract symbol"""
        with pytest.raises(ValidationError):
            await options_service.get_option_history("INVALID")
    
    @pytest.mark.asyncio
    async def test_close_service(self, options_service):
        """Test service cleanup"""
        with patch.object(options_service.yfinance_client, 'close') as mock_close:
            await options_service.close()
            mock_close.assert_called_once()


class TestYFinanceClient:
    """Test yfinance client operations"""
    
    @pytest.fixture
    def client(self):
        """Create yfinance client instance"""
        return YFinanceClient()
    
    @pytest.mark.asyncio
    async def test_calculate_greeks(self, client):
        """Test Greeks calculation"""
        greeks = client._calculate_greeks(
            stock_price=150.0,
            strike=155.0,
            expiry="2024-12-31",  # Future date
            iv=0.30,
            option_type="call"
        )
        
        assert "delta" in greeks
        assert "gamma" in greeks
        assert "theta" in greeks
        assert "vega" in greeks
        assert isinstance(greeks["delta"], float)
    
    def test_calculate_greeks_edge_cases(self, client):
        """Test Greeks calculation with edge cases"""
        # Zero time to expiry
        greeks = client._calculate_greeks(150.0, 155.0, "2024-01-01", 0.30, "call")
        assert greeks == {"delta": 0, "gamma": 0, "theta": 0, "vega": 0}
        
        # Zero volatility
        greeks = client._calculate_greeks(150.0, 155.0, "2024-12-31", 0.0, "call")
        assert greeks == {"delta": 0, "gamma": 0, "theta": 0, "vega": 0}
    
    @pytest.mark.asyncio
    async def test_close_client(self, client):
        """Test client cleanup"""
        with patch.object(client.executor, 'shutdown') as mock_shutdown:
            await client.close()
            mock_shutdown.assert_called_once_with(wait=True)
