"""
FastAPI backend for Options Trading Dashboard
"""
from fastapi import FastAPI, HTTPException, UploadFile, File
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
from services.overview import (
    get_finance_overview, get_connections_list, trigger_sync
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
async def clear_all_notifications_endpoint():
    """Clear all notifications"""
    return clear_notifications()


# ===== Custom Strategies API =====

class CustomStrategyRequest(BaseModel):
    name: str
    code: str
    schedule_type: str = 'INTERVAL'
    schedule_value: str = '60'
    execution_type: str = 'HOST'
    targets: Optional[str] = None

@app.post("/api/custom-strategies")
async def create_new_custom_strategy(strategy: CustomStrategyRequest):
    """Create a new custom strategy script"""
    try:
        from services.custom_strategies import create_custom_strategy, schedule_strategy_job
        sid = create_custom_strategy(
            strategy.name, strategy.code, strategy.schedule_type, 
            strategy.schedule_value, strategy.execution_type
        )
        return {"id": sid, "message": "Strategy created"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/custom-strategies")
async def list_custom_strategies():
    """List all custom strategies"""
    try:
        from services.custom_strategies import get_custom_strategies
        strats = get_custom_strategies()
        return {"strategies": strats}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/custom-strategies/{strategy_id}")
async def get_custom_strategy_details(strategy_id: int):
    """Get details of a specific custom strategy"""
    try:
        from services.custom_strategies import get_custom_strategy_by_id
        strat = get_custom_strategy_by_id(strategy_id)
        if not strat:
            raise HTTPException(status_code=404, detail="Strategy not found")
        return strat
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/api/custom-strategies/{strategy_id}")
async def update_custom_strategy_endpoint(strategy_id: int, strategy: CustomStrategyRequest):
    """Update a custom strategy code/config"""
    try:
        from services.custom_strategies import update_custom_strategy, reschedule_strategy_job
        update_custom_strategy(
            strategy_id, strategy.name, strategy.code, 
            strategy.schedule_type, strategy.schedule_value, 
            strategy.execution_type
        )
        reschedule_strategy_job(strategy_id)
        return {"message": "Strategy updated"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/custom-strategies/{strategy_id}/toggle")
async def toggle_custom_strategy(strategy_id: int):
    """Toggle strategy active state"""
    try:
        from services.custom_strategies import toggle_strategy_active, reschedule_strategy_job, stop_strategy_job
        new_state = toggle_strategy_active(strategy_id)
        if new_state:
            reschedule_strategy_job(strategy_id)
        else:
            stop_strategy_job(strategy_id)
        return {"active": new_state}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/custom-strategies/{strategy_id}/execute")
async def execute_custom_strategy_manual(strategy_id: int):
    """Manually trigger a strategy execution"""
    try:
        from services.execution_engine import run_strategy_host, run_strategy_docker
        from services.custom_strategies import get_custom_strategy_by_id
        
        strat = get_custom_strategy_by_id(strategy_id)
        if not strat:
            raise HTTPException(status_code=404, detail="Strategy not found")
            
        if strat.get('execution_type') == 'DOCKER':
            result = run_strategy_docker(strategy_id, strat['code'])
        else:
            result = run_strategy_host(strategy_id, strat['code'])
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/custom-strategies/{strategy_id}/logs")
async def get_strategy_execution_logs(strategy_id: int):
    """Get execution history for a strategy"""
    try:
        from services.custom_strategies import get_strategy_logs
        logs = get_strategy_logs(strategy_id)
        return {"logs": logs}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/tracker/status")
async def tracker_status():
    """Get background scheduler status"""
    return get_scheduler_status()


# ============== PERSONAL FINANCE ENDPOINTS ==============

@app.get("/api/overview")
async def personal_finance_overview():
    """Get personal finance overview with all custodians, accounts, and totals"""
    try:
        return get_finance_overview()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching overview: {str(e)}")


@app.get("/api/connections")
async def list_connections():
    """Get all financial connections"""
    try:
        return {"connections": get_connections_list()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching connections: {str(e)}")


@app.post("/api/connections/{connection_id}/sync")
async def sync_connection_endpoint(connection_id: str):
    """Trigger a manual sync for a connection"""
    try:
        result = trigger_sync(connection_id)
        if result["success"]:
            return result
        raise HTTPException(status_code=404, detail=result.get("error", "Sync failed"))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error triggering sync: {str(e)}")


# ============== FINANCE CONNECTOR ENDPOINTS ==============

# Import finance module (lazy import to avoid circular deps)
def get_finance_module():
    from services.finance import (
        init_finance_db, get_all_institutions, get_institution_by_brand_key,
        create_connection, get_all_connections as get_db_connections, get_connection_by_id,
        update_connection_status, update_connection_auth,
        get_accounts_by_connection, get_holdings_by_account, get_transactions_by_account,
        get_account_total_value, encrypt_auth_blob, SourceType, SyncMode, ConnectionStatus,
        sync_connection as do_sync, process_file_upload,
        ConnectorRegistry
    )
    return {
        "init_finance_db": init_finance_db,
        "get_all_institutions": get_all_institutions,
        "get_institution_by_brand_key": get_institution_by_brand_key,
        "create_connection": create_connection,
        "get_all_connections": get_db_connections,
        "get_connection_by_id": get_connection_by_id,
        "update_connection_status": update_connection_status,
        "update_connection_auth": update_connection_auth,
        "get_accounts_by_connection": get_accounts_by_connection,
        "get_holdings_by_account": get_holdings_by_account,
        "get_transactions_by_account": get_transactions_by_account,
        "get_account_total_value": get_account_total_value,
        "encrypt_auth_blob": encrypt_auth_blob,
        "SourceType": SourceType,
        "SyncMode": SyncMode,
        "ConnectionStatus": ConnectionStatus,
        "sync_connection": do_sync,
        "process_file_upload": process_file_upload,
        "ConnectorRegistry": ConnectorRegistry
    }


@app.on_event("startup")
async def init_finance_database():
    """Initialize finance database and seed demo data on startup"""
    try:
        from services.finance import init_finance_db, seed_demo_data
        init_finance_db()
        # Auto-seed demo data if no connections exist
        seed_demo_data()
        print("Finance database initialized with demo data")
    except Exception as e:
        print(f"Warning: Could not initialize finance database: {e}")


@app.get("/api/finance/institutions")
async def list_institutions():
    """Get all available financial institutions"""
    try:
        fm = get_finance_module()
        institutions = fm["get_all_institutions"]()
        return {
            "institutions": [inst.to_dict() for inst in institutions]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/finance/connections")
async def list_finance_connections():
    """Get all user connections from database"""
    try:
        fm = get_finance_module()
        connections = fm["get_all_connections"]()
        return {
            "connections": [conn.to_dict() for conn in connections]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class CreateConnectionRequest(BaseModel):
    institution_brand_key: str
    auth_data: Optional[dict] = None


@app.post("/api/finance/connections")
async def create_finance_connection(request: CreateConnectionRequest):
    """Create a new connection to a financial institution"""
    try:
        fm = get_finance_module()
        
        # Get institution
        institution = fm["get_institution_by_brand_key"](request.institution_brand_key)
        if not institution:
            raise HTTPException(status_code=404, detail=f"Institution not found: {request.institution_brand_key}")
        
        # Handle specific connector setup (like Plaid token exchange)
        final_auth_data = request.auth_data
        
        if institution.source_type == fm["SourceType"].AGGREGATOR.value and request.auth_data and "public_token" in request.auth_data:
            try:
                registry = fm["ConnectorRegistry"]()
                connector = registry.get_connector(fm["SourceType"].AGGREGATOR)
                # user_id is 'default' for now
                exchange_result = connector.exchange_link_artifact("default", request.auth_data)
                
                if not exchange_result.success:
                     raise HTTPException(status_code=400, detail=f"Token exchange failed: {exchange_result.error}")
                     
                final_auth_data = exchange_result.auth_data
            except Exception as e:
                print(f"Token exchange error: {e}")
                # Fallback to saving raw data if exchange fails (might be useful for debugging)
                pass

        # Encrypt auth data if provided
        auth_encrypted = None
        if final_auth_data:
            import json
            auth_encrypted = fm["encrypt_auth_blob"](json.dumps(final_auth_data))
        
        # Check if connection already exists for this institution
        existing_connections = fm["get_all_connections"]()
        existing = next((c for c in existing_connections if c.institution_id == institution.id), None)
        
        if existing:
            # Update existing connection
            if auth_encrypted:
                fm["update_connection_auth"](existing.id, auth_encrypted)
            fm["update_connection_status"](existing.id, fm["ConnectionStatus"].ACTIVE)
            connection_id = existing.id
            created = False
        else:
            # Create new connection
            connection_id = fm["create_connection"](
                institution_id=institution.id,
                source_type=institution.source_type,
                auth_blob_encrypted=auth_encrypted
            )
            created = True
        
        return {
            "success": True, 
            "connection_id": connection_id,
            "status": "created" if created else "updated",
            "institution": institution.to_dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/finance/connections/{connection_id}/sync")
async def sync_finance_connection(connection_id: int, mode: str = "incremental"):
    """Trigger sync for a connection using the connector framework"""
    try:
        fm = get_finance_module()
        sync_mode = fm["SyncMode"].INCREMENTAL if mode == "incremental" else fm["SyncMode"].INITIAL
        
        result = fm["sync_connection"](connection_id, sync_mode, "USER")
        
        if result.get("success"):
            return result
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "Sync failed"))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/finance/connections/{connection_id}/accounts")
async def get_connection_accounts(connection_id: int):
    """Get all accounts for a connection"""
    try:
        fm = get_finance_module()
        accounts = fm["get_accounts_by_connection"](connection_id)
        
        # Add total value for each account
        result = []
        for account in accounts:
            acc_dict = account.to_dict()
            acc_dict["total_value"] = fm["get_account_total_value"](account.id)
            result.append(acc_dict)
        
        return {"accounts": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/finance/accounts/{account_id}/holdings")
async def get_account_holdings(account_id: int, as_of: Optional[str] = None):
    """Get holdings for an account"""
    try:
        fm = get_finance_module()
        holdings = fm["get_holdings_by_account"](account_id, as_of)
        return {
            "holdings": [h.to_dict() for h in holdings],
            "total_value": sum(h.value or 0 for h in holdings)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/finance/accounts/{account_id}/transactions")
async def get_account_transactions(
    account_id: int, 
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 100
):
    """Get transactions for an account"""
    try:
        fm = get_finance_module()
        transactions = fm["get_transactions_by_account"](account_id, start_date, end_date, limit)
        return {
            "transactions": [t.to_dict() for t in transactions],
            "count": len(transactions)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class LinkStartRequest(BaseModel):
    institution_brand_key: str


@app.post("/api/finance/link/start")
async def start_link_session(request: LinkStartRequest):
    """Start a link session for connecting a new institution"""
    try:
        fm = get_finance_module()
        
        institution = fm["get_institution_by_brand_key"](request.institution_brand_key)
        if not institution:
            raise HTTPException(status_code=404, detail="Institution not found")
        
        connector = fm["ConnectorRegistry"].get(institution.source_type)
        if not connector:
            raise HTTPException(status_code=400, detail="No connector available for this institution")
        
        result = connector.create_link_session("default", institution=request.institution_brand_key)
        
        if result.success:
            return {
                "success": True,
                "session_id": result.session_id,
                "link_url": result.link_url,
                "link_token": result.link_token,
                "expires_at": result.expires_at,
                "institution": institution.to_dict()
            }
        else:
            raise HTTPException(status_code=400, detail=result.error)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class LinkExchangeRequest(BaseModel):
    institution_brand_key: str
    artifact: dict  # Contains public_token, code, etc.


@app.post("/api/finance/link/exchange")
async def exchange_link_artifact(request: LinkExchangeRequest):
    """Exchange link artifact for credentials and create connection"""
    try:
        fm = get_finance_module()
        import json
        
        institution = fm["get_institution_by_brand_key"](request.institution_brand_key)
        if not institution:
            raise HTTPException(status_code=404, detail="Institution not found")
        
        connector = fm["ConnectorRegistry"].get(institution.source_type)
        if not connector:
            raise HTTPException(status_code=400, detail="No connector available")
        
        # Exchange artifact
        result = connector.exchange_link_artifact("default", request.artifact)
        
        if not result.success:
            raise HTTPException(status_code=400, detail=result.error)
        
        # Encrypt and store
        auth_encrypted = fm["encrypt_auth_blob"](json.dumps(result.auth_data))
        
        connection_id = fm["create_connection"](
            institution_id=institution.id,
            source_type=institution.source_type,
            auth_blob_encrypted=auth_encrypted
        )
        
        # Run initial sync
        sync_result = fm["sync_connection"](connection_id, fm["SyncMode"].INITIAL, "USER")
        
        return {
            "success": True,
            "connection_id": connection_id,
            "sync_result": sync_result
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/finance/demo/seed")
async def seed_demo_data_endpoint():
    """Seed demo data for the finance module"""
    try:
        from services.finance import seed_demo_data
        result = seed_demo_data()
        if result:
            return {"success": True, "message": "Demo data seeded successfully"}
        return {"success": True, "message": "Demo data already exists"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/finance/demo/reset")
async def reset_demo_data_endpoint():
    """Clear and reseed demo data"""
    try:
        from services.finance import clear_demo_data, seed_demo_data
        clear_demo_data()
        seed_demo_data()
        return {"success": True, "message": "Demo data reset successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/finance/connections/{connection_id}/upload")
async def upload_finance_file(connection_id: int, file: UploadFile = File(...)):
    """Upload and process a finance file (OFX/QFX/CSV)"""
    try:
        import os
        from pathlib import Path
        import shutil
        
        # Save uploaded file
        upload_dir = Path(__file__).parent / "data" / "uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = upload_dir / file.filename
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Determine file type
        filename_lower = file.filename.lower()
        file_type = "unknown"
        if filename_lower.endswith(".ofx") or filename_lower.endswith(".qfx"):
            file_type = "ofx"
        elif filename_lower.endswith(".csv"):
            file_type = "csv"
            
        # Process file
        fm = get_finance_module()
        result = fm["process_file_upload"](connection_id, str(file_path), file_type)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

