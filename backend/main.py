"""
FastAPI backend for Options Trading Dashboard
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from pydantic import BaseModel

from services.options import (
    get_stock_quote, get_options_chain, get_top_volume_options, 
    scan_market_options, get_stock_history, detect_unusual_activity,
    get_ai_recommendation, get_option_history, get_quote_lite
)
from services.options_search import find_best_options
from services.database import (
    init_db, get_all_tickers, get_scanner_tickers, add_ticker, remove_ticker,
    get_all_options, add_option, remove_option, is_option_in_watchlist
)
from services.strategies import (
    create_strategy, get_all_strategies, get_strategy_by_id,
    update_strategy, delete_strategy
)
from services.trades import (
    create_trade, get_all_trades, get_trade_by_id,
    update_trade, close_trade, delete_trade, get_trade_stats
)
from services.notifications import (
    get_notifications, mark_notification_read, 
    mark_all_read, clear_notifications, get_unread_count
)
from services.scheduler import (
    init_scheduler, shutdown_scheduler, get_scheduler_status
)

app = FastAPI(
    title="Options Trading API",
    description="API for fetching real-time stock and options data",
    version="1.0.0"
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost", "http://localhost:80", "http://localhost:8420"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize database and scheduler on startup"""
    init_db()
    init_scheduler()
    print("Database and Scheduler initialized")


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown scheduler on exit"""
    shutdown_scheduler()


@app.get("/")
async def root():
    return {"message": "Options Trading API", "status": "running"}


@app.get("/api/quote/{ticker}")
async def quote(ticker: str):
    """Get current stock quote"""
    try:
        data = get_stock_quote(ticker.upper())
        return data
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error fetching quote for {ticker}: {str(e)}")


@app.get("/api/quote-lite/{ticker}")
async def quote_lite(ticker: str):
    """Lightweight quote for live updates - fast price data only"""
    try:
        data = get_quote_lite(ticker.upper())
        return data
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error fetching quote for {ticker}: {str(e)}")


@app.get("/api/options/{ticker}")
async def options(ticker: str, expiry: Optional[str] = None):
    """Get options chain for a stock"""
    try:
        data = get_options_chain(ticker.upper(), expiry)
        return data
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error fetching options for {ticker}: {str(e)}")


@app.get("/api/top-volume/{ticker}")
async def top_volume(ticker: str, top_n: int = 10):
    """Get top volume options for near-term expiry (1-2 days out)"""
    try:
        data = get_top_volume_options(ticker.upper(), top_n)
        return data
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error fetching top volume for {ticker}: {str(e)}")


@app.get("/api/scan")
async def market_scan():
    """Scan top stocks for most active options - uses watchlist tickers"""
    try:
        data = scan_market_options()
        return data
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error scanning market: {str(e)}")


@app.get("/api/history/{ticker}")
async def stock_history(ticker: str, period: str = "3mo", interval: str = "1d"):
    """Get stock price history with EMAs and technical indicators"""
    try:
        data = get_stock_history(ticker.upper(), period, interval)
        return data
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error fetching history for {ticker}: {str(e)}")


@app.get("/api/unusual/{ticker}")
async def unusual_activity(ticker: str):
    """Detect unusual options activity"""
    try:
        data = detect_unusual_activity(ticker.upper())
        return data
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error detecting unusual activity for {ticker}: {str(e)}")


@app.get("/api/option-history/{contract_symbol}")
async def option_history(contract_symbol: str, period: str = "1mo", interval: str = "1d"):
    """Get historical prices for a specific option contract"""
    try:
        data = get_option_history(contract_symbol, period, interval)
        return data
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error fetching option history: {str(e)}")


class AIRecommendRequest(BaseModel):
    topCalls: list = []
    topPuts: list = []


@app.post("/api/ai-recommend")
async def ai_recommend(request: AIRecommendRequest):
    """Get AI-powered trade recommendation based on scan results"""
    try:
        data = get_ai_recommendation({
            "topCalls": request.topCalls,
            "topPuts": request.topPuts
        })
        return data
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error generating recommendation: {str(e)}")


class FindOptionsRequest(BaseModel):
    ticker: str
    optionType: str
    targetPrice: float
    stopLoss: float | None = None
    targetDate: str
    maxOptionPrice: float | None = None


@app.post("/api/find-options")
async def find_options(request: FindOptionsRequest):
    """Find best options based on user thesis"""
    try:
        data = find_best_options(
            request.ticker,
            request.targetPrice,
            request.targetDate,
            request.optionType,
            max_option_price=request.maxOptionPrice
        )
        if "error" in data:
            raise HTTPException(status_code=400, detail=data["error"])
        return data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error finding options: {str(e)}")


# ============== WATCHLIST API ENDPOINTS ==============

# --- Ticker Watchlist ---

@app.get("/api/watchlist/tickers")
async def get_tickers():
    """Get all tickers in watchlist"""
    try:
        return {"tickers": get_all_tickers()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class AddTickerRequest(BaseModel):
    symbol: str
    category: str = "Other"


@app.post("/api/watchlist/tickers")
async def add_ticker_endpoint(request: AddTickerRequest):
    """Add a ticker to watchlist"""
    try:
        result = add_ticker(request.symbol, request.category)
        if result["success"]:
            return result
        raise HTTPException(status_code=400, detail=result["error"])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/watchlist/tickers/{symbol}")
async def remove_ticker_endpoint(symbol: str):
    """Remove a ticker from watchlist"""
    try:
        result = remove_ticker(symbol)
        if result["success"]:
            return result
        raise HTTPException(status_code=404, detail=result["error"])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- Option Watchlist ---

@app.get("/api/watchlist/options")
async def get_options_watchlist():
    """Get all options in watchlist"""
    try:
        return {"options": get_all_options()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class AddOptionRequest(BaseModel):
    contractSymbol: str
    ticker: str
    strike: float
    expiry: str
    optionType: str
    notes: str = ""


@app.post("/api/watchlist/options")
async def add_option_endpoint(request: AddOptionRequest):
    """Add an option to watchlist"""
    try:
        result = add_option(
            request.contractSymbol,
            request.ticker,
            request.strike,
            request.expiry,
            request.optionType,
            request.notes
        )
        if result["success"]:
            return result
        raise HTTPException(status_code=400, detail=result["error"])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/watchlist/options/{contract_symbol}")
async def remove_option_endpoint(contract_symbol: str):
    """Remove an option from watchlist"""
    try:
        result = remove_option(contract_symbol)
        if result["success"]:
            return result
        raise HTTPException(status_code=404, detail=result["error"])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/watchlist/options/check/{contract_symbol}")
async def check_option_in_watchlist(contract_symbol: str):
    """Check if an option is in the watchlist"""
    try:
        return {"inWatchlist": is_option_in_watchlist(contract_symbol)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



# ============== TRADE TRACKER ENDPOINTS ==============

# --- Strategies ---

@app.get("/api/strategies")
async def list_strategies():
    """Get all trading strategies"""
    try:
        return {"strategies": get_all_strategies()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/strategies/{strategy_id}")
async def get_strategy(strategy_id: int):
    """Get single strategy"""
    strategy = get_strategy_by_id(strategy_id)
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    return strategy


class StrategyModel(BaseModel):
    name: str
    description: str = ""
    scan_criteria: dict = {}
    default_stop_loss_pct: float = 0.20
    default_take_profit_pct: float = 0.50
    notifications_enabled: bool = True


@app.post("/api/strategies")
async def create_strategy_endpoint(strategy: StrategyModel):
    """Create a new strategy"""
    result = create_strategy(
        name=strategy.name,
        description=strategy.description,
        scan_criteria=strategy.scan_criteria,
        default_stop_loss_pct=strategy.default_stop_loss_pct,
        default_take_profit_pct=strategy.default_take_profit_pct,
        notifications_enabled=strategy.notifications_enabled
    )
    if result["success"]:
        return result
    raise HTTPException(status_code=400, detail=result["error"])


@app.put("/api/strategies/{strategy_id}")
async def update_strategy_endpoint(strategy_id: int, strategy: StrategyModel):
    """Update a strategy"""
    result = update_strategy(
        strategy_id,
        name=strategy.name,
        description=strategy.description,
        scan_criteria=strategy.scan_criteria,
        default_stop_loss_pct=strategy.default_stop_loss_pct,
        default_take_profit_pct=strategy.default_take_profit_pct,
        notifications_enabled=strategy.notifications_enabled
    )
    if result["success"]:
        return result
    raise HTTPException(status_code=400, detail=result.get("error", "Failed to update"))


@app.delete("/api/strategies/{strategy_id}")
async def delete_strategy_endpoint(strategy_id: int):
    """Delete a strategy"""
    result = delete_strategy(strategy_id)
    if result["success"]:
        return result
    raise HTTPException(status_code=404, detail=result.get("error", "Failed to delete"))


# --- Trades ---

@app.get("/api/trades")
async def list_trades(status: Optional[str] = None, strategy_id: Optional[int] = None):
    """List trades with optional filters"""
    try:
        return {"trades": get_all_trades(status, strategy_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/trades/stats")
async def trade_stats():
    """Get aggregate trade statistics"""
    try:
        return get_trade_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/trades/{trade_id}")
async def get_trade(trade_id: int):
    """Get single trade"""
    trade = get_trade_by_id(trade_id)
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    return trade


class TradeModel(BaseModel):
    contract_symbol: str
    ticker: str
    entry_price: float
    fill_price: float = None
    quantity: int = 1
    stop_loss: float = None
    take_profit: float = None
    strategy_id: int = None
    notifications_enabled: bool = True
    notes: str = ""


@app.post("/api/trades")
async def create_trade_endpoint(trade: TradeModel):
    """Create a new trade"""
    result = create_trade(
        contract_symbol=trade.contract_symbol,
        ticker=trade.ticker,
        entry_price=trade.entry_price,
        fill_price=trade.fill_price,
        quantity=trade.quantity,
        stop_loss=trade.stop_loss,
        take_profit=trade.take_profit,
        strategy_id=trade.strategy_id,
        notifications_enabled=trade.notifications_enabled,
        notes=trade.notes
    )
    if result["success"]:
        return result
    raise HTTPException(status_code=400, detail=result.get("error", "Failed to create trade"))


class UpdateTradeModel(BaseModel):
    stop_loss: float = None
    take_profit: float = None
    priority: str = None # Unused but often sent
    notes: str = None
    notifications_enabled: bool = None
    quantity: int = None


@app.put("/api/trades/{trade_id}")
async def update_trade_endpoint(trade_id: int, updates: UpdateTradeModel):
    """Update trade parameters"""
    # Filter out None values
    update_data = {k: v for k, v in updates.dict().items() if v is not None}
    
    result = update_trade(trade_id, **update_data)
    if result["success"]:
        return result
    raise HTTPException(status_code=400, detail=result.get("error", "Failed to update trade"))


class CloseTradeModel(BaseModel):
    exit_price: float


@app.post("/api/trades/{trade_id}/close")
async def close_trade_endpoint(trade_id: int, data: CloseTradeModel):
    """Close a trade manually"""
    result = close_trade(trade_id, data.exit_price)
    if result["success"]:
        return result
    raise HTTPException(status_code=400, detail=result.get("error", "Failed to close trade"))


@app.delete("/api/trades/{trade_id}")
async def delete_trade_endpoint(trade_id: int):
    """Delete a trade record"""
    result = delete_trade(trade_id)
    if result["success"]:
        return result
    raise HTTPException(status_code=404, detail=result.get("error", "Failed to delete trade"))


# --- Notifications & System ---

@app.get("/api/notifications")
async def list_notifications():
    """Get notifications"""
    return {
        "notifications": get_notifications(), 
        "unread_count": get_unread_count()
    }


@app.post("/api/notifications/{notification_id}/read")
async def read_notification(notification_id: int):
    """Mark notification as read"""
    result = mark_notification_read(notification_id)
    if result["success"]:
        return result
    raise HTTPException(status_code=404, detail="Notification not found")


@app.post("/api/notifications/read-all")
async def read_all_notifications():
    """Mark all notifications as read"""
    return mark_all_read()


@app.delete("/api/notifications")
async def clear_all_notifications():
    """Clear all notifications"""
    return clear_notifications()


@app.get("/api/tracker/status")
async def tracker_status():
    """Get background scheduler status"""
    return get_scheduler_status()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

