from typing import Protocol, List, Optional
from abc import ABC, abstractmethod

from app.domain.models import TickerWatchlist, OptionWatchlist


class TickerWatchlistRepository(Protocol):
    """Repository interface for ticker watchlist operations"""
    
    async def get_all(self) -> List[TickerWatchlist]:
        """Get all ticker watchlist entries"""
        ...
    
    async def get_by_symbol(self, symbol: str) -> Optional[TickerWatchlist]:
        """Get ticker watchlist entry by symbol"""
        ...
    
    async def create(self, symbol: str, category: str = "Other") -> TickerWatchlist:
        """Create a new ticker watchlist entry"""
        ...
    
    async def delete(self, symbol: str) -> bool:
        """Delete a ticker watchlist entry by symbol"""
        ...
    
    async def get_symbols_only(self) -> List[str]:
        """Get just the ticker symbols for scanning"""
        ...


class OptionWatchlistRepository(Protocol):
    """Repository interface for option watchlist operations"""
    
    async def get_all(self) -> List[OptionWatchlist]:
        """Get all option watchlist entries"""
        ...
    
    async def get_by_contract_symbol(self, contract_symbol: str) -> Optional[OptionWatchlist]:
        """Get option watchlist entry by contract symbol"""
        ...
    
    async def create(
        self,
        contract_symbol: str,
        ticker: str,
        strike: float,
        expiry: str,
        option_type: str,
        notes: str = ""
    ) -> OptionWatchlist:
        """Create a new option watchlist entry"""
        ...
    
    async def delete(self, contract_symbol: str) -> bool:
        """Delete an option watchlist entry by contract symbol"""
        ...
    
    async def exists(self, contract_symbol: str) -> bool:
        """Check if option exists in watchlist"""
        ...
