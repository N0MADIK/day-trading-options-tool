"""
Notification service for trade alerts
Provides in-memory notification queue, extensible for other methods
"""
from datetime import datetime
from typing import List, Optional
import threading

# Thread-safe notification storage
_notifications = []
_lock = threading.Lock()
_next_id = 1


def send_notification(trade_id: int, ticker: str, status: str, 
                     exit_price: float, pnl: float) -> dict:
    """Send a trade notification"""
    global _next_id
    
    notification = {
        "id": _next_id,
        "trade_id": trade_id,
        "ticker": ticker,
        "status": status,
        "exit_price": exit_price,
        "pnl": pnl,
        "timestamp": datetime.now().isoformat(),
        "read": False
    }
    
    with _lock:
        _notifications.append(notification)
        _next_id += 1
    
    # Log the notification
    pnl_str = f"+${pnl:.2f}" if pnl >= 0 else f"-${abs(pnl):.2f}"
    print(f"[NOTIFICATION] {ticker} {status}: Exit ${exit_price:.2f}, P&L {pnl_str}")
    
    return {"success": True, "notification_id": notification["id"]}


def get_notifications(unread_only: bool = False) -> List[dict]:
    """Get all notifications, optionally filtered to unread only"""
    with _lock:
        if unread_only:
            return [n.copy() for n in _notifications if not n['read']]
        return [n.copy() for n in _notifications]


def mark_notification_read(notification_id: int) -> dict:
    """Mark a notification as read"""
    with _lock:
        for n in _notifications:
            if n['id'] == notification_id:
                n['read'] = True
                return {"success": True}
    return {"success": False, "error": "Notification not found"}


def mark_all_read() -> dict:
    """Mark all notifications as read"""
    with _lock:
        for n in _notifications:
            n['read'] = True
    return {"success": True}


def clear_notifications() -> dict:
    """Clear all notifications"""
    global _notifications
    with _lock:
        _notifications = []
    return {"success": True}


def get_unread_count() -> int:
    """Get count of unread notifications"""
    with _lock:
        return sum(1 for n in _notifications if not n['read'])
