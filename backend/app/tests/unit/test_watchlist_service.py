import pytest
from unittest.mock import AsyncMock, Mock
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.watchlist_service import WatchlistService
from app.schemas.watchlist import TickerWatchlistCreate, OptionWatchlistCreate
from app.domain.models import TickerWatchlist, OptionWatchlist
from app.domain.errors import NotFoundError, ConflictError


@pytest.fixture
def mock_session():
    """Create a mock AsyncSession"""
    session = AsyncMock(spec=AsyncSession)
    return session


@pytest.fixture
def watchlist_service(mock_session):
    """Create watchlist service with mock session"""
    return WatchlistService(mock_session)


class TestTickerWatchlistService:
    """Test ticker watchlist service operations"""
    
    @pytest.mark.asyncio
    async def test_get_all_tickers(self, watchlist_service, mock_session):
        """Test getting all tickers"""
        # Setup mock
        mock_ticker = Mock(spec=TickerWatchlist)
        mock_ticker.id = 1
        mock_ticker.symbol = "AAPL"
        mock_ticker.category = "Tech"
        mock_ticker.added_at = "2024-01-01"
        
        mock_repo = AsyncMock()
        mock_repo.get_all.return_value = [mock_ticker]
        watchlist_service.ticker_repo = mock_repo
        
        # Execute
        result = await watchlist_service.get_all_tickers()
        
        # Assert
        assert len(result) == 1
        assert result[0].symbol == "AAPL"
        assert result[0].category == "Tech"
        mock_repo.get_all.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_add_ticker_success(self, watchlist_service, mock_session):
        """Test successfully adding a ticker"""
        # Setup
        ticker_data = TickerWatchlistCreate(symbol="AAPL", category="Tech")
        
        mock_ticker = Mock(spec=TickerWatchlist)
        mock_ticker.id = 1
        mock_ticker.symbol = "AAPL"
        mock_ticker.category = "Tech"
        mock_ticker.added_at = "2024-01-01"
        
        mock_repo = AsyncMock()
        mock_repo.create.return_value = mock_ticker
        watchlist_service.ticker_repo = mock_repo
        
        # Execute
        result = await watchlist_service.add_ticker(ticker_data)
        
        # Assert
        assert result.symbol == "AAPL"
        assert result.category == "Tech"
        mock_repo.create.assert_called_once_with(symbol="AAPL", category="Tech")
    
    @pytest.mark.asyncio
    async def test_add_ticker_conflict(self, watchlist_service, mock_session):
        """Test adding a ticker that already exists"""
        # Setup
        ticker_data = TickerWatchlistCreate(symbol="AAPL", category="Tech")
        
        mock_repo = AsyncMock()
        mock_repo.create.side_effect = ConflictError("Ticker AAPL already exists")
        watchlist_service.ticker_repo = mock_repo
        
        # Execute & Assert
        with pytest.raises(ConflictError) as exc_info:
            await watchlist_service.add_ticker(ticker_data)
        
        assert "already exists" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_remove_ticker_success(self, watchlist_service, mock_session):
        """Test successfully removing a ticker"""
        # Setup
        mock_repo = AsyncMock()
        mock_repo.delete.return_value = True
        watchlist_service.ticker_repo = mock_repo
        
        # Execute
        result = await watchlist_service.remove_ticker("AAPL")
        
        # Assert
        assert result is True
        mock_repo.delete.assert_called_once_with("AAPL")
    
    @pytest.mark.asyncio
    async def test_remove_ticker_not_found(self, watchlist_service, mock_session):
        """Test removing a ticker that doesn't exist"""
        # Setup
        mock_repo = AsyncMock()
        mock_repo.delete.return_value = False
        watchlist_service.ticker_repo = mock_repo
        
        # Execute & Assert
        with pytest.raises(NotFoundError) as exc_info:
            await watchlist_service.remove_ticker("AAPL")
        
        assert "not found" in str(exc_info.value)


class TestOptionWatchlistService:
    """Test option watchlist service operations"""
    
    @pytest.mark.asyncio
    async def test_add_option_success(self, watchlist_service, mock_session):
        """Test successfully adding an option"""
        # Setup
        option_data = OptionWatchlistCreate(
            contract_symbol="AAPL240119C00150000",
            ticker="AAPL",
            strike=150.0,
            expiry="2024-01-19",
            option_type="CALL",
            notes="Test option"
        )
        
        mock_option = Mock(spec=OptionWatchlist)
        mock_option.id = 1
        mock_option.contract_symbol = "AAPL240119C00150000"
        mock_option.ticker = "AAPL"
        mock_option.strike = 150.0
        mock_option.expiry = "2024-01-19"
        mock_option.option_type = "CALL"
        mock_option.notes = "Test option"
        mock_option.added_at = "2024-01-01"
        
        mock_repo = AsyncMock()
        mock_repo.create.return_value = mock_option
        watchlist_service.option_repo = mock_repo
        
        # Execute
        result = await watchlist_service.add_option(option_data)
        
        # Assert
        assert result.contract_symbol == "AAPL240119C00150000"
        assert result.ticker == "AAPL"
        assert result.strike == 150.0
        mock_repo.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_check_option_in_watchlist(self, watchlist_service, mock_session):
        """Test checking if option exists in watchlist"""
        # Setup
        mock_repo = AsyncMock()
        mock_repo.exists.return_value = True
        watchlist_service.option_repo = mock_repo
        
        # Execute
        result = await watchlist_service.check_option_in_watchlist("AAPL240119C00150000")
        
        # Assert
        assert result.in_watchlist is True
        mock_repo.exists.assert_called_once_with("AAPL240119C00150000")
