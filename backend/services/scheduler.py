"""
Background scheduler for monitoring trades
Uses APScheduler to periodically check open trades against SL/TP
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import logging

logger = logging.getLogger(__name__)

# Global scheduler instance
_scheduler = None


def init_scheduler():
    """Initialize and start the background scheduler"""
    global _scheduler
    
    if _scheduler is not None:
        return
    
    _scheduler = BackgroundScheduler()
    
    # Add job to monitor trades every 60 seconds
    _scheduler.add_job(
        monitor_trades,
        IntervalTrigger(seconds=60),
        id='monitor_trades',
        name='Monitor Open Trades',
        replace_existing=True
    )
    
    _scheduler.start()
    logger.info("Trade monitor scheduler started")


def shutdown_scheduler():
    """Shutdown the scheduler gracefully"""
    global _scheduler
    
    if _scheduler:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        logger.info("Trade monitor scheduler stopped")


def get_scheduler_status() -> dict:
    """Get current scheduler status"""
    global _scheduler
    
    if _scheduler is None:
        return {"running": False, "jobs": []}
    
    jobs = []
    for job in _scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run": str(job.next_run_time) if job.next_run_time else None
        })
    
    return {
        "running": _scheduler.running,
        "jobs": jobs
    }


def monitor_trades():
    """Check open trades and close if SL/TP hit"""
    try:
        from services.trades import get_open_trades, close_trade
        from services.notifications import send_notification
        
        open_trades = get_open_trades()
        
        if not open_trades:
            return
        
        logger.info(f"Checking {len(open_trades)} open trades")
        
        for trade in open_trades:
            try:
                current_price = get_current_option_price(trade['contract_symbol'])
                
                if current_price is None:
                    continue
                
                result = check_trade_conditions(trade, current_price)
                
                if result:
                    # Close the trade
                    close_result = close_trade(trade['id'], current_price)
                    
                    if close_result['success'] and trade['notifications_enabled']:
                        send_notification(
                            trade_id=trade['id'],
                            ticker=trade['ticker'],
                            status=close_result['status'],
                            exit_price=current_price,
                            pnl=close_result['pnl']
                        )
                        logger.info(f"Trade {trade['id']} closed: {close_result['status']}, P&L: {close_result['pnl']}")
                        
            except Exception as e:
                logger.error(f"Error checking trade {trade['id']}: {e}")
                
    except Exception as e:
        logger.error(f"Error in monitor_trades: {e}")


def get_current_option_price(contract_symbol: str) -> float:
    """Get current price for an option contract"""
    try:
        import yfinance as yf
        option = yf.Ticker(contract_symbol)
        hist = option.history(period="1d")
        if not hist.empty:
            return hist['Close'].iloc[-1]
    except Exception as e:
        logger.debug(f"Could not get price for {contract_symbol}: {e}")
    return None


def check_trade_conditions(trade: dict, current_price: float) -> bool:
    """Check if trade should be closed based on SL/TP"""
    stop_loss = trade.get('stop_loss')
    take_profit = trade.get('take_profit')
    
    if stop_loss and current_price <= stop_loss:
        return True
    
    if take_profit and current_price >= take_profit:
        return True
    
    return False
