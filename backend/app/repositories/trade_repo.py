from typing import Protocol, List, Optional, Dict, Any
from datetime import datetime

from app.schemas.trades import TradeStatus, TradeCreateRequest, TradeUpdateRequest


class TradeRepository(Protocol):
    """Repository interface for trade operations"""
    
    async def create_trade(self, trade_data: TradeCreateRequest) -> int:
        """Create a new trade and return its ID"""
        ...
    
    async def get_trade_by_id(self, trade_id: int) -> Optional[Dict[str, Any]]:
        """Get a single trade by ID"""
        ...
    
    async def get_all_trades(
        self, 
        status: Optional[TradeStatus] = None,
        strategy_id: Optional[int] = None,
        ticker: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get all trades with optional filters"""
        ...
    
    async def get_open_trades(self) -> List[Dict[str, Any]]:
        """Get all open trades"""
        ...
    
    async def update_trade(self, trade_id: int, updates: TradeUpdateRequest) -> bool:
        """Update a trade"""
        ...
    
    async def close_trade(self, trade_id: int, exit_price: float) -> Optional[Dict[str, Any]]:
        """Close a trade and calculate P&L"""
        ...
    
    async def delete_trade(self, trade_id: int) -> bool:
        """Delete a trade"""
        ...
    
    async def get_trade_stats(self) -> Dict[str, Any]:
        """Get aggregate trade statistics"""
        ...
    
    async def get_trades_by_ticker(self, ticker: str) -> List[Dict[str, Any]]:
        """Get all trades for a specific ticker"""
        ...
    
    async def get_trades_by_strategy(self, strategy_id: int) -> List[Dict[str, Any]]:
        """Get all trades for a specific strategy"""
        ...
    
    async def batch_update_trades(self, trade_ids: List[int], updates: Dict[str, Any]) -> int:
        """Update multiple trades at once"""
        ...
    
    async def batch_delete_trades(self, trade_ids: List[int]) -> int:
        """Delete multiple trades at once"""
        ...
    
    async def get_trade_performance_analysis(
        self, 
        period: str = "3mo",
        group_by: str = "month"
    ) -> Dict[str, Any]:
        """Get detailed trade performance analysis"""
        ...
    
    async def search_trades(self, query: str) -> List[Dict[str, Any]]:
        """Search trades by contract symbol or notes"""
        ...
