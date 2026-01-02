from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime


class StockQuoteRequest(BaseModel):
    """Request for stock quote"""
    ticker: str = Field(..., min_length=1, max_length=10, description="Ticker symbol")
    
    @validator('ticker')
    def normalize_ticker(cls, v):
        return v.upper().strip()


class StockQuoteResponse(BaseModel):
    """Response for stock quote"""
    ticker: str
    price: float
    change: Optional[float] = None
    change_percent: Optional[float] = None
    volume: Optional[int] = None
    market_cap: Optional[int] = None
    day_high: Optional[float] = None
    day_low: Optional[float] = None
    year_high: Optional[float] = None
    year_low: Optional[float] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class QuoteLiteResponse(BaseModel):
    """Lightweight quote response for live updates"""
    ticker: str
    price: float
    change: Optional[float] = None
    change_percent: Optional[float] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class OptionsChainRequest(BaseModel):
    """Request for options chain"""
    ticker: str = Field(..., min_length=1, max_length=10, description="Ticker symbol")
    expiry: Optional[str] = Field(None, description="Expiration date (YYYY-MM-DD)")
    
    @validator('ticker')
    def normalize_ticker(cls, v):
        return v.upper().strip()


class OptionGreeks(BaseModel):
    """Option Greeks data"""
    delta: float = Field(..., description="Delta")
    gamma: float = Field(..., description="Gamma")
    theta: float = Field(..., description="Theta")
    vega: float = Field(..., description="Vega")


class OptionContract(BaseModel):
    """Single option contract data"""
    contract_symbol: str
    strike: float
    expiry: str
    option_type: str  # CALL or PUT
    last_price: Optional[float] = None
    bid: Optional[float] = None
    ask: Optional[float] = None
    volume: Optional[int] = None
    open_interest: Optional[int] = None
    implied_volatility: Optional[float] = None
    greeks: Optional[OptionGreeks] = None
    scalp_score: Optional[float] = None


class OptionsChainResponse(BaseModel):
    """Response for options chain"""
    ticker: str
    expiry: Optional[str]
    calls: List[OptionContract]
    puts: List[OptionContract]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class TopVolumeOptionsRequest(BaseModel):
    """Request for top volume options"""
    ticker: str = Field(..., min_length=1, max_length=10, description="Ticker symbol")
    top_n: int = Field(default=10, ge=1, le=50, description="Number of top options to return")
    
    @validator('ticker')
    def normalize_ticker(cls, v):
        return v.upper().strip()


class TopVolumeOptionsResponse(BaseModel):
    """Response for top volume options"""
    ticker: str
    options: List[OptionContract]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class StockHistoryRequest(BaseModel):
    """Request for stock history"""
    ticker: str = Field(..., min_length=1, max_length=10, description="Ticker symbol")
    period: str = Field(default="3mo", description="Period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)")
    interval: str = Field(default="1d", description="Interval (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)")
    
    @validator('ticker')
    def normalize_ticker(cls, v):
        return v.upper().strip()


class PricePoint(BaseModel):
    """Single price point in history"""
    date: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    adj_close: Optional[float] = None


class TechnicalIndicator(BaseModel):
    """Technical indicator data"""
    ema_20: Optional[float] = None
    ema_50: Optional[float] = None
    rsi: Optional[float] = None
    macd: Optional[Dict[str, float]] = None
    atr: Optional[float] = None


class StockHistoryResponse(BaseModel):
    """Response for stock history"""
    ticker: str
    period: str
    interval: str
    prices: List[PricePoint]
    technicals: Optional[TechnicalIndicator] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class OptionHistoryRequest(BaseModel):
    """Request for option history"""
    contract_symbol: str = Field(..., description="Option contract symbol")
    period: str = Field(default="1mo", description="Period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)")
    interval: str = Field(default="1d", description="Interval (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)")


class OptionHistoryResponse(BaseModel):
    """Response for option history"""
    contract_symbol: str
    period: str
    interval: str
    prices: List[PricePoint]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AIRecommendationRequest(BaseModel):
    """Request for AI recommendation"""
    top_calls: List[Dict[str, Any]] = Field(default=[], description="Top call options data")
    top_puts: List[Dict[str, Any]] = Field(default=[], description="Top put options data")


class AIRecommendationResponse(BaseModel):
    """Response for AI recommendation"""
    recommendation: Dict[str, Any]
    reasoning: Optional[str] = None
    confidence: Optional[float] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class MarketScanRequest(BaseModel):
    """Request for market scan"""
    # No parameters needed - uses watchlist tickers


class MarketScanResponse(BaseModel):
    """Response for market scan"""
    scan_results: List[Dict[str, Any]]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class UnusualActivityRequest(BaseModel):
    """Request for unusual activity detection"""
    ticker: str = Field(..., min_length=1, max_length=10, description="Ticker symbol")
    
    @validator('ticker')
    def normalize_ticker(cls, v):
        return v.upper().strip()


class UnusualActivityResponse(BaseModel):
    """Response for unusual activity detection"""
    ticker: str
    unusual_options: List[Dict[str, Any]]
    analysis: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
