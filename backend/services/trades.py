"""
Trades service for managing tracked trades
"""
from datetime import datetime
from services.database import get_db


def create_trade(contract_symbol: str, ticker: str, entry_price: float,
                fill_price: float = None, quantity: int = 1,
                stop_loss: float = None, take_profit: float = None,
                strategy_id: int = None, notifications_enabled: bool = True,
                notes: str = '') -> dict:
    """Create a new tracked trade"""
    if fill_price is None:
        fill_price = entry_price
    
    with get_db() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO trades 
                (contract_symbol, ticker, entry_price, fill_price, quantity,
                 stop_loss, take_profit, strategy_id, notifications_enabled, notes, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'OPEN')
            ''', (
                contract_symbol, ticker.upper(), entry_price, fill_price, quantity,
                stop_loss, take_profit, strategy_id,
                1 if notifications_enabled else 0, notes
            ))
            conn.commit()
            return {"success": True, "id": cursor.lastrowid}
        except Exception as e:
            return {"success": False, "error": str(e)}


def get_all_trades(status: str = None, strategy_id: int = None) -> list:
    """Get all trades, optionally filtered"""
    with get_db() as conn:
        cursor = conn.cursor()
        query = '''
            SELECT t.*, s.name as strategy_name
            FROM trades t
            LEFT JOIN strategies s ON t.strategy_id = s.id
            WHERE 1=1
        '''
        params = []
        
        if status:
            query += ' AND t.status = ?'
            params.append(status)
        if strategy_id:
            query += ' AND t.strategy_id = ?'
            params.append(strategy_id)
        
        query += ' ORDER BY t.entry_date DESC'
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        trades = []
        for row in rows:
            trade = dict(row)
            trade['notifications_enabled'] = bool(trade['notifications_enabled'])
            trades.append(trade)
        return trades


def get_trade_by_id(trade_id: int) -> dict:
    """Get a single trade by ID"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT t.*, s.name as strategy_name
            FROM trades t
            LEFT JOIN strategies s ON t.strategy_id = s.id
            WHERE t.id = ?
        ''', (trade_id,))
        row = cursor.fetchone()
        if row:
            trade = dict(row)
            trade['notifications_enabled'] = bool(trade['notifications_enabled'])
            return trade
        return None


def get_open_trades() -> list:
    """Get all open trades"""
    return get_all_trades(status='OPEN')


def update_trade(trade_id: int, **kwargs) -> dict:
    """Update a trade"""
    allowed_fields = ['stop_loss', 'take_profit', 'notes', 'notifications_enabled', 'quantity']
    
    updates = []
    values = []
    
    for field in allowed_fields:
        if field in kwargs:
            value = kwargs[field]
            if field == 'notifications_enabled':
                value = 1 if value else 0
            updates.append(f"{field} = ?")
            values.append(value)
    
    if not updates:
        return {"success": False, "error": "No fields to update"}
    
    values.append(trade_id)
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(f'''
            UPDATE trades SET {", ".join(updates)} WHERE id = ?
        ''', values)
        conn.commit()
        if cursor.rowcount > 0:
            return {"success": True}
        return {"success": False, "error": "Trade not found"}


def close_trade(trade_id: int, exit_price: float) -> dict:
    """Close a trade and calculate P&L"""
    trade = get_trade_by_id(trade_id)
    if not trade:
        return {"success": False, "error": "Trade not found"}
    
    if trade['status'] != 'OPEN':
        return {"success": False, "error": "Trade already closed"}
    
    fill_price = trade['fill_price'] or trade['entry_price']
    quantity = trade['quantity'] or 1
    
    # P&L = (exit - entry) * quantity * 100 (options multiplier)
    pnl = (exit_price - fill_price) * quantity * 100
    
    status = 'CLOSED_WIN' if pnl >= 0 else 'CLOSED_LOSS'
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE trades 
            SET status = ?, exit_price = ?, exit_date = ?, pnl = ?
            WHERE id = ?
        ''', (status, exit_price, datetime.now().isoformat(), pnl, trade_id))
        conn.commit()
    
    return {"success": True, "status": status, "pnl": pnl, "exit_price": exit_price}


def delete_trade(trade_id: int) -> dict:
    """Delete a trade"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM trades WHERE id = ?', (trade_id,))
        conn.commit()
        if cursor.rowcount > 0:
            return {"success": True}
        return {"success": False, "error": "Trade not found"}


def get_trade_stats() -> dict:
    """Get aggregate trade statistics"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Total trades
        cursor.execute('SELECT COUNT(*) FROM trades')
        total = cursor.fetchone()[0]
        
        # Open trades
        cursor.execute("SELECT COUNT(*) FROM trades WHERE status = 'OPEN'")
        open_count = cursor.fetchone()[0]
        
        # Wins
        cursor.execute("SELECT COUNT(*) FROM trades WHERE status = 'CLOSED_WIN'")
        wins = cursor.fetchone()[0]
        
        # Losses
        cursor.execute("SELECT COUNT(*) FROM trades WHERE status = 'CLOSED_LOSS'")
        losses = cursor.fetchone()[0]
        
        # Total P&L
        cursor.execute("SELECT COALESCE(SUM(pnl), 0) FROM trades WHERE pnl IS NOT NULL")
        total_pnl = cursor.fetchone()[0]
        
        closed = wins + losses
        win_rate = round((wins / closed * 100), 1) if closed > 0 else 0
        
        return {
            "total_trades": total,
            "open_trades": open_count,
            "closed_trades": closed,
            "wins": wins,
            "losses": losses,
            "win_rate": win_rate,
            "total_pnl": total_pnl
        }
