from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.watchlist_repo import TickerWatchlistRepository, OptionWatchlistRepository
from app.repositories.sqlalchemy.watchlist_repo import (
    SqlAlchemyTickerWatchlistRepository,
    SqlAlchemyOptionWatchlistRepository
)
from app.schemas.watchlist import (
    TickerWatchlistCreate,
    TickerWatchlistResponse,
    OptionWatchlistCreate,
    OptionWatchlistResponse,
    WatchlistCheckResponse
)
from app.domain.errors import NotFoundError, ConflictError


class WatchlistService:
    """Service layer for watchlist operations"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.ticker_repo: TickerWatchlistRepository = SqlAlchemyTickerWatchlistRepository(session)
        self.option_repo: OptionWatchlistRepository = SqlAlchemyOptionWatchlistRepository(session)
    
    # ========== TICKER WATCHLIST OPERATIONS ==========
    
    async def get_all_tickers(self) -> List[TickerWatchlistResponse]:
        """Get all ticker watchlist entries"""
        tickers = await self.ticker_repo.get_all()
        return [TickerWatchlistResponse.model_validate(ticker) for ticker in tickers]
    
    async def add_ticker(self, ticker_data: TickerWatchlistCreate) -> TickerWatchlistResponse:
        """Add a ticker to the watchlist"""
        try:
            ticker = await self.ticker_repo.create(
                symbol=ticker_data.symbol,
                category=ticker_data.category
            )
            return TickerWatchlistResponse.model_validate(ticker)
        except ConflictError as e:
            raise ConflictError(f"Ticker {ticker_data.symbol} already exists in watchlist")
    
    async def remove_ticker(self, symbol: str) -> bool:
        """Remove a ticker from the watchlist"""
        success = await self.ticker_repo.delete(symbol)
        if not success:
            raise NotFoundError(f"Ticker {symbol} not found in watchlist")
        return True
    
    async def get_ticker_symbols(self) -> List[str]:
        """Get ticker symbols for scanning"""
        return await self.ticker_repo.get_symbols_only()
    
    # ========== OPTION WATCHLIST OPERATIONS ==========
    
    async def get_all_options(self) -> List[OptionWatchlistResponse]:
        """Get all option watchlist entries"""
        options = await self.option_repo.get_all()
        return [OptionWatchlistResponse.model_validate(option) for option in options]
    
    async def add_option(self, option_data: OptionWatchlistCreate) -> OptionWatchlistResponse:
        """Add an option to the watchlist"""
        try:
            option = await self.option_repo.create(
                contract_symbol=option_data.contract_symbol,
                ticker=option_data.ticker,
                strike=option_data.strike,
                expiry=option_data.expiry,
                option_type=option_data.option_type,
                notes=option_data.notes
            )
            return OptionWatchlistResponse.model_validate(option)
        except ConflictError as e:
            raise ConflictError(f"Option {option_data.contract_symbol} already exists in watchlist")
    
    async def remove_option(self, contract_symbol: str) -> bool:
        """Remove an option from the watchlist"""
        success = await self.option_repo.delete(contract_symbol)
        if not success:
            raise NotFoundError(f"Option {contract_symbol} not found in watchlist")
        return True
    
    async def check_option_in_watchlist(self, contract_symbol: str) -> WatchlistCheckResponse:
        """Check if an option is in the watchlist"""
        exists = await self.option_repo.exists(contract_symbol)
        return WatchlistCheckResponse(in_watchlist=exists)
