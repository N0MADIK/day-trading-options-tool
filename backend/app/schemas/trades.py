from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


class TradeStatus(str, Enum):
    """Trade status enumeration"""
    OPEN = "OPEN"
    CLOSED_WIN = "CLOSED_WIN"
    CLOSED_LOSS = "CLOSED_LOSS"


class TradeCreateRequest(BaseModel):
    """Request for creating a new trade"""
    contract_symbol: str = Field(..., min_length=1, max_length=50, description="Option contract symbol")
    ticker: str = Field(..., min_length=1, max_length=10, description="Underlying ticker symbol")
    entry_price: float = Field(..., gt=0, description="Entry price of the trade")
    fill_price: Optional[float] = Field(None, ge=0, description="Actual fill price (defaults to entry_price)")
    quantity: int = Field(default=1, ge=1, le=1000, description="Number of contracts")
    stop_loss: Optional[float] = Field(None, ge=0, description="Stop loss price")
    take_profit: Optional[float] = Field(None, ge=0, description="Take profit price")
    strategy_id: Optional[int] = Field(None, ge=1, description="Associated strategy ID")
    notifications_enabled: bool = Field(default=True, description="Enable notifications for this trade")
    notes: Optional[str] = Field("", max_length=1000, description="Trade notes")
    
    @validator('contract_symbol')
    def normalize_contract_symbol(cls, v):
        return v.upper().strip()
    
    @validator('ticker')
    def normalize_ticker(cls, v):
        return v.upper().strip()


class TradeUpdateRequest(BaseModel):
    """Request for updating an existing trade"""
    stop_loss: Optional[float] = Field(None, ge=0, description="Stop loss price")
    take_profit: Optional[float] = Field(None, ge=0, description="Take profit price")
    quantity: Optional[int] = Field(None, ge=1, le=1000, description="Number of contracts")
    notifications_enabled: Optional[bool] = Field(None, description="Enable notifications for this trade")
    notes: Optional[str] = Field(None, max_length=1000, description="Trade notes")


class TradeCloseRequest(BaseModel):
    """Request for closing a trade"""
    exit_price: float = Field(..., gt=0, description="Exit price of the trade")


class TradeResponse(BaseModel):
    """Response model for trade data"""
    id: int
    strategy_id: Optional[int] = None
    contract_symbol: str
    ticker: str
    entry_date: datetime
    entry_price: float
    fill_price: Optional[float] = None
    quantity: int
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    status: TradeStatus
    exit_date: Optional[datetime] = None
    exit_price: Optional[float] = None
    pnl: Optional[float] = None
    notifications_enabled: bool
    notes: Optional[str] = None
    strategy_name: Optional[str] = None  # Joined from strategies table
    
    class Config:
        from_attributes = True


class TradeListRequest(BaseModel):
    """Request for listing trades with filters"""
    status: Optional[TradeStatus] = Field(None, description="Filter by trade status")
    strategy_id: Optional[int] = Field(None, ge=1, description="Filter by strategy ID")
    ticker: Optional[str] = Field(None, min_length=1, max_length=10, description="Filter by ticker")
    limit: Optional[int] = Field(None, ge=1, le=1000, description="Limit number of results")
    offset: Optional[int] = Field(None, ge=0, le=10000, description="Offset for pagination")
    
    @validator('ticker')
    def normalize_ticker(cls, v):
        return v.upper().strip() if v else None


class TradeStatsResponse(BaseModel):
    """Response model for trade statistics"""
    total_trades: int = Field(..., ge=0, description="Total number of trades")
    open_trades: int = Field(..., ge=0, description="Number of open trades")
    closed_trades: int = Field(..., ge=0, description="Number of closed trades")
    wins: int = Field(..., ge=0, description="Number of winning trades")
    losses: int = Field(..., ge=0, description="Number of losing trades")
    win_rate: float = Field(..., ge=0, le=100, description="Win rate percentage")
    total_pnl: float = Field(..., description="Total profit and loss")
    avg_win: Optional[float] = Field(None, description="Average winning trade P&L")
    avg_loss: Optional[float] = Field(None, description="Average losing trade P&L")
    largest_win: Optional[float] = Field(None, description="Largest winning trade")
    largest_loss: Optional[float] = Field(None, description="Largest losing trade")
    profit_factor: Optional[float] = Field(None, description="Profit factor (gross profit / gross loss)")


class TradePerformanceResponse(BaseModel):
    """Response model for detailed trade performance"""
    trade_id: int
    contract_symbol: str
    ticker: str
    entry_price: float
    exit_price: Optional[float] = None
    quantity: int
    pnl: Optional[float] = None
    pnl_percent: Optional[float] = None
    days_held: Optional[int] = None
    status: TradeStatus
    strategy_name: Optional[str] = None


class TradeBatchRequest(BaseModel):
    """Request for batch trade operations"""
    trade_ids: List[int] = Field(..., min_items=1, max_items=100, description="List of trade IDs")
    action: str = Field(..., description="Action to perform (close, delete, update)")


class TradeBatchUpdateRequest(BaseModel):
    """Request for batch updating trades"""
    trade_ids: List[int] = Field(..., min_items=1, max_items=100, description="List of trade IDs")
    updates: TradeUpdateRequest = Field(..., description="Updates to apply to all trades")


class TradeAnalysisRequest(BaseModel):
    """Request for trade analysis"""
    period: str = Field(default="3mo", description="Analysis period (1mo, 3mo, 6mo, 1y, all)")
    group_by: str = Field(default="month", description="Group results by (day, week, month, quarter)")
    strategy_id: Optional[int] = Field(None, ge=1, description="Filter by strategy ID")


class TradeAnalysisResponse(BaseModel):
    """Response model for trade analysis"""
    period: str
    group_by: str
    data_points: List[dict]
    summary: dict


class TradePaymentRequest(BaseModel):
    """Request for trade payment analysis"""
    user_id: int = Field(..., ge=1, description="User ID")
    symbol: str = Field(..., min_length=1, max_length=10, description="Trade symbol")
    shares: int = Field(..., ge=1, description="Number of shares")
    price: float = Field(..., gt=0, description="Price per share")
    trade_type: str = Field(..., description="Trade type (buy or sell)")
    
    @validator('symbol')
    def normalize_symbol(cls, v):
        return v.upper().strip()
    
    @validator('trade_type')
    def validate_trade_type(cls, v):
        if v.upper() not in ['BUY', 'SELL']:
            raise ValueError('trade_type must be either "buy" or "sell"')
        return v.upper()


class AssetSaleInfo(BaseModel):
    """Information about an asset sold to pay for a trade"""
    symbol: str
    shares_sold: int
    sale_price_per_share: float
    gross_proceeds: float
    taxes: float
    net_proceeds: float
    purchase_date: str
    days_held: int
    tax_rate: str


class TradePaymentResponse(BaseModel):
    """Response model for trade payment analysis"""
    success: bool
    trade: dict
    payment_analysis: dict
    message: Optional[str] = None
