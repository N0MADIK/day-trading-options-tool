"""Market Data schemas for stock quotes and options"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Any


class StockQuoteRequest(BaseModel):
    """Request for stock quote"""
    symbol: str
    provider: Optional[str] = "yfinance"  # yfinance, alpaca, polygon


class StockQuoteResponse(BaseModel):
    """Stock quote response"""
    symbol: str
    price: float
    change: float
    change_percent: float
    volume: int
    name: Optional[str] = None
    market_cap: Optional[float] = None
    pe_ratio: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    open: Optional[float] = None
    previous_close: Optional[float] = None
    timestamp: datetime
    error: Optional[str] = None


class OptionsChainRequest(BaseModel):
    """Request for options chain"""
    symbol: str
    expiration: Optional[str] = None  # Format: YYYY-MM-DD
    provider: Optional[str] = "yfinance"


class OptionsChainResponse(BaseModel):
    """Options chain response"""
    symbol: str
    expirations: List[str]
    selected_expiration: Optional[str] = None
    calls: List[Dict[str, Any]]
    puts: List[Dict[str, Any]]
    underlying_price: float


class HistoricalDataPoint(BaseModel):
    """Single historical data point"""
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int


class HistoricalDataResponse(BaseModel):
    """Historical data response"""
    symbol: str
    period: str
    interval: str
    data: List[Dict[str, Any]]


class SymbolSearchResult(BaseModel):
    """Symbol search result"""
    symbol: str
    name: str
    type: str  # EQUITY, ETF, OPTION, etc.
    exchange: str
