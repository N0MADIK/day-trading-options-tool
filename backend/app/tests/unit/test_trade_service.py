import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from app.services.trade_service import TradeService
from app.repositories.trade_repo import TradeRepository
from app.schemas.trades import (
    TradeCreateRequest, TradeUpdateRequest, TradeCloseRequest,
    TradeListRequest, TradeStatsResponse, TradeBatchRequest,
    TradeBatchUpdateRequest, TradeAnalysisRequest
)
from app.domain.errors import NotFoundError, ConflictError, ValidationError


class TestTradeService:
    """Test trade service operations"""
    
    @pytest.fixture
    def mock_repository(self):
        """Create mock trade repository"""
        return AsyncMock(spec=TradeRepository)
    
    @pytest.fixture
    def trade_service(self, mock_repository):
        """Create trade service with mock repository"""
        return TradeService(mock_repository)
    
    @pytest.mark.asyncio
    async def test_create_trade_success(self, trade_service, mock_repository):
        """Test successful trade creation"""
        # Setup
        trade_data = TradeCreateRequest(
            contract_symbol="AAPL240119C00150000",
            ticker="AAPL",
            entry_price=5.25,
            quantity=2,
            stop_loss=4.50,
            take_profit=6.00
        )
        
        mock_repository.create_trade.return_value = 1
        mock_repository.get_trade_by_id.return_value = {
            'id': 1,
            'contract_symbol': 'AAPL240119C00150000',
            'ticker': 'AAPL',
            'entry_price': 5.25,
            'quantity': 2,
            'status': 'OPEN'
        }
        
        # Execute
        result = await trade_service.create_trade(trade_data)
        
        # Assert
        assert result["success"] is True
        assert result["trade_id"] == 1
        assert result["trade"]["contract_symbol"] == "AAPL240119C00150000"
        mock_repository.create_trade.assert_called_once_with(trade_data)
    
    @pytest.mark.asyncio
    async def test_create_trade_invalid_stop_loss(self, trade_service, mock_repository):
        """Test trade creation with invalid stop loss"""
        trade_data = TradeCreateRequest(
            contract_symbol="AAPL240119C00150000",
            ticker="AAPL",
            entry_price=5.25,
            stop_loss=6.00,  # Higher than take profit
            take_profit=5.50
        )
        
        with pytest.raises(ValidationError) as exc_info:
            await trade_service.create_trade(trade_data)
        
        assert "Stop loss must be less than take profit" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_get_trade_by_id_success(self, trade_service, mock_repository):
        """Test successful trade retrieval"""
        # Setup
        mock_trade = {
            'id': 1,
            'contract_symbol': 'AAPL240119C00150000',
            'ticker': 'AAPL',
            'entry_price': 5.25,
            'status': 'OPEN'
        }
        mock_repository.get_trade_by_id.return_value = mock_trade
        
        # Execute
        result = await trade_service.get_trade_by_id(1)
        
        # Assert
        assert result == mock_trade
        mock_repository.get_trade_by_id.assert_called_once_with(1)
    
    @pytest.mark.asyncio
    async def test_get_trade_by_id_not_found(self, trade_service, mock_repository):
        """Test trade retrieval when not found"""
        mock_repository.get_trade_by_id.return_value = None
        
        with pytest.raises(NotFoundError) as exc_info:
            await trade_service.get_trade_by_id(999)
        
        assert "Trade with ID 999 not found" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_list_trades_success(self, trade_service, mock_repository):
        """Test successful trade listing"""
        # Setup
        request = TradeListRequest(status="OPEN", limit=10)
        mock_trades = [
            {'id': 1, 'contract_symbol': 'AAPL240119C00150000', 'status': 'OPEN'},
            {'id': 2, 'contract_symbol': 'MSFT240119C00150000', 'status': 'OPEN'}
        ]
        mock_repository.get_all_trades.return_value = mock_trades
        
        # Execute
        result = await trade_service.list_trades(request)
        
        # Assert
        assert len(result) == 2
        assert result[0]['contract_symbol'] == 'AAPL240119C00150000'
        mock_repository.get_all_trades.assert_called_once_with(
            status="OPEN", strategy_id=None, ticker=None, limit=10, offset=None
        )
    
    @pytest.mark.asyncio
    async def test_update_trade_success(self, trade_service, mock_repository):
        """Test successful trade update"""
        # Setup
        updates = TradeUpdateRequest(stop_loss=4.25, take_profit=6.50)
        existing_trade = {'id': 1, 'status': 'OPEN'}
        updated_trade = {'id': 1, 'stop_loss': 4.25, 'take_profit': 6.50}
        
        mock_repository.get_trade_by_id.return_value = existing_trade
        mock_repository.update_trade.return_value = True
        mock_repository.get_trade_by_id.return_value = updated_trade
        
        # Execute
        result = await trade_service.update_trade(1, updates)
        
        # Assert
        assert result["success"] is True
        assert result["trade"]["stop_loss"] == 4.25
        mock_repository.update_trade.assert_called_once_with(1, updates)
    
    @pytest.mark.asyncio
    async def test_close_trade_success(self, trade_service, mock_repository):
        """Test successful trade closing"""
        # Setup
        close_request = TradeCloseRequest(exit_price=6.25)
        existing_trade = {'id': 1, 'status': 'OPEN', 'fill_price': 5.25, 'quantity': 2}
        closed_trade = {
            'id': 1, 'status': 'CLOSED_WIN', 'pnl': 200.0,
            'exit_price': 6.25, 'exit_date': datetime.utcnow()
        }
        
        mock_repository.get_trade_by_id.return_value = existing_trade
        mock_repository.close_trade.return_value = closed_trade
        
        # Execute
        result = await trade_service.close_trade(1, close_request)
        
        # Assert
        assert result["success"] is True
        assert result["status"] == "CLOSED_WIN"
        assert result["pnl"] == 200.0
        mock_repository.close_trade.assert_called_once_with(1, 6.25)
    
    @pytest.mark.asyncio
    async def test_close_trade_already_closed(self, trade_service, mock_repository):
        """Test closing an already closed trade"""
        # Setup
        close_request = TradeCloseRequest(exit_price=6.25)
        existing_trade = {'id': 1, 'status': 'CLOSED_WIN'}
        
        mock_repository.get_trade_by_id.return_value = existing_trade
        
        # Execute & Assert
        with pytest.raises(ConflictError) as exc_info:
            await trade_service.close_trade(1, close_request)
        
        assert "Trade is already closed" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_delete_trade_success(self, trade_service, mock_repository):
        """Test successful trade deletion"""
        # Setup
        existing_trade = {'id': 1, 'status': 'CLOSED_WIN'}
        mock_repository.get_trade_by_id.return_value = existing_trade
        mock_repository.delete_trade.return_value = True
        
        # Execute
        result = await trade_service.delete_trade(1)
        
        # Assert
        assert result["success"] is True
        assert "deleted successfully" in result["message"]
        mock_repository.delete_trade.assert_called_once_with(1)
    
    @pytest.mark.asyncio
    async def test_delete_open_trade_forbidden(self, trade_service, mock_repository):
        """Test deleting an open trade (should be forbidden)"""
        # Setup
        existing_trade = {'id': 1, 'status': 'OPEN'}
        mock_repository.get_trade_by_id.return_value = existing_trade
        
        # Execute & Assert
        with pytest.raises(ValidationError) as exc_info:
            await trade_service.delete_trade(1)
        
        assert "Cannot delete open trades" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_get_trade_statistics(self, trade_service, mock_repository):
        """Test getting trade statistics"""
        # Setup
        mock_stats = {
            "total_trades": 100,
            "open_trades": 5,
            "closed_trades": 95,
            "wins": 60,
            "losses": 35,
            "win_rate": 63.2,
            "total_pnl": 2500.50,
            "avg_win": 125.25,
            "avg_loss": -45.75,
            "largest_win": 500.00,
            "largest_loss": -150.00,
            "profit_factor": 2.15
        }
        mock_repository.get_trade_stats.return_value = mock_stats
        
        # Execute
        result = await trade_service.get_trade_statistics()
        
        # Assert
        assert isinstance(result, TradeStatsResponse)
        assert result.total_trades == 100
        assert result.win_rate == 63.2
        assert result.profit_factor == 2.15
    
    @pytest.mark.asyncio
    async def test_batch_update_trades_success(self, trade_service, mock_repository):
        """Test successful batch update of trades"""
        # Setup
        request = TradeBatchUpdateRequest(
            trade_ids=[1, 2, 3],
            updates=TradeUpdateRequest(stop_loss=4.00)
        )
        
        existing_trades = [
            {'id': 1, 'status': 'OPEN'},
            {'id': 2, 'status': 'OPEN'},
            {'id': 3, 'status': 'OPEN'}
        ]
        
        mock_repository.get_trade_by_id.side_effect = existing_trades
        mock_repository.batch_update_trades.return_value = 3
        
        # Execute
        result = await trade_service.batch_update_trades(request)
        
        # Assert
        assert result["success"] is True
        assert result["updated_count"] == 3
        mock_repository.batch_update_trades.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_batch_close_trades_success(self, trade_service, mock_repository):
        """Test successful batch closing of trades"""
        # Setup
        trade_ids = [1, 2]
        exit_prices = [6.25, 4.75]
        
        closed_trades = [
            {'id': 1, 'status': 'CLOSED_WIN', 'pnl': 200.0},
            {'id': 2, 'status': 'CLOSED_LOSS', 'pnl': -100.0}
        ]
        
        mock_repository.close_trade.side_effect = closed_trades
        
        # Execute
        result = await trade_service.batch_close_trades(trade_ids, exit_prices)
        
        # Assert
        assert result["success"] is True
        assert result["successful_count"] == 2
        assert result["failed_count"] == 0
        assert len(result["results"]) == 2
    
    @pytest.mark.asyncio
    async def test_search_trades_success(self, trade_service, mock_repository):
        """Test successful trade search"""
        # Setup
        search_results = [
            {'id': 1, 'contract_symbol': 'AAPL240119C00150000', 'notes': 'Good entry'},
            {'id': 2, 'contract_symbol': 'AAPL240119C00155000', 'notes': 'Test trade'}
        ]
        mock_repository.search_trades.return_value = search_results
        
        # Execute
        result = await trade_service.search_trades("AAPL")
        
        # Assert
        assert len(result) == 2
        assert "AAPL" in result[0]["contract_symbol"]
        mock_repository.search_trades.assert_called_once_with("AAPL")
    
    @pytest.mark.asyncio
    async def test_search_trades_invalid_query(self, trade_service, mock_repository):
        """Test trade search with invalid query"""
        # Execute & Assert
        with pytest.raises(ValidationError) as exc_info:
            await trade_service.search_trades("A")
        
        assert "at least 2 characters" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_get_risk_metrics(self, trade_service, mock_repository):
        """Test getting risk metrics"""
        # Setup
        open_trades = [
            {
                'id': 1,
                'fill_price': 5.25,
                'entry_price': 5.25,
                'quantity': 2,
                'stop_loss': 4.50
            },
            {
                'id': 2,
                'fill_price': 3.75,
                'entry_price': 3.75,
                'quantity': 1,
                'stop_loss': 3.25
            }
        ]
        mock_repository.get_open_trades.return_value = open_trades
        
        # Execute
        result = await trade_service.get_risk_metrics()
        
        # Assert
        assert result["open_positions"] == 2
        assert result["trades_at_risk"] == 2
        assert result["total_risk_exposure"] > 0
        assert "risk_percentage" in result
    
    @pytest.mark.asyncio
    async def test_get_trade_performance_details(self, trade_service, mock_repository):
        """Test getting detailed trade performance"""
        # Setup
        trade_data = {
            'id': 1,
            'contract_symbol': 'AAPL240119C00150000',
            'ticker': 'AAPL',
            'entry_price': 5.25,
            'fill_price': 5.25,
            'quantity': 2,
            'exit_price': 6.25,
            'pnl': 200.0,
            'exit_date': datetime.utcnow(),
            'entry_date': datetime.utcnow(),
            'status': 'CLOSED_WIN',
            'strategy_name': 'Test Strategy'
        }
        mock_repository.get_trade_by_id.return_value = trade_data
        
        # Execute
        result = await trade_service.get_trade_performance_details(1)
        
        # Assert
        assert result.trade_id == 1
        assert result.contract_symbol == 'AAPL240119C00150000'
        assert result.pnl == 200.0
        assert result.pnl_percent is not None
        assert result.days_held is not None
        assert result.strategy_name == 'Test Strategy'
