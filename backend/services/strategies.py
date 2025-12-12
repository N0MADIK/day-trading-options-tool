"""
Strategies service for managing trading strategies
"""
import json
from datetime import datetime
from services.database import get_db


def create_strategy(name: str, description: str = '', scan_criteria: dict = None,
                   default_stop_loss_pct: float = 0.20, default_take_profit_pct: float = 0.50,
                   notifications_enabled: bool = True) -> dict:
    """Create a new strategy"""
    with get_db() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO strategies 
                (name, description, scan_criteria, default_stop_loss_pct, default_take_profit_pct, notifications_enabled)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                name,
                description,
                json.dumps(scan_criteria) if scan_criteria else None,
                default_stop_loss_pct,
                default_take_profit_pct,
                1 if notifications_enabled else 0
            ))
            conn.commit()
            return {"success": True, "id": cursor.lastrowid}
        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                return {"success": False, "error": f"Strategy '{name}' already exists"}
            return {"success": False, "error": str(e)}


def get_all_strategies() -> list:
    """Get all strategies"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, name, description, scan_criteria, default_stop_loss_pct, 
                   default_take_profit_pct, notifications_enabled, created_at
            FROM strategies ORDER BY created_at DESC
        ''')
        rows = cursor.fetchall()
        strategies = []
        for row in rows:
            strategy = dict(row)
            if strategy['scan_criteria']:
                try:
                    strategy['scan_criteria'] = json.loads(strategy['scan_criteria'])
                except:
                    strategy['scan_criteria'] = {}
            strategy['notifications_enabled'] = bool(strategy['notifications_enabled'])
            strategies.append(strategy)
        return strategies


def get_strategy_by_id(strategy_id: int) -> dict:
    """Get a single strategy by ID"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, name, description, scan_criteria, default_stop_loss_pct,
                   default_take_profit_pct, notifications_enabled, created_at
            FROM strategies WHERE id = ?
        ''', (strategy_id,))
        row = cursor.fetchone()
        if row:
            strategy = dict(row)
            if strategy['scan_criteria']:
                try:
                    strategy['scan_criteria'] = json.loads(strategy['scan_criteria'])
                except:
                    strategy['scan_criteria'] = {}
            strategy['notifications_enabled'] = bool(strategy['notifications_enabled'])
            return strategy
        return None


def update_strategy(strategy_id: int, **kwargs) -> dict:
    """Update a strategy"""
    allowed_fields = ['name', 'description', 'scan_criteria', 'default_stop_loss_pct',
                      'default_take_profit_pct', 'notifications_enabled']
    
    updates = []
    values = []
    
    for field in allowed_fields:
        if field in kwargs:
            value = kwargs[field]
            if field == 'scan_criteria' and isinstance(value, dict):
                value = json.dumps(value)
            elif field == 'notifications_enabled':
                value = 1 if value else 0
            updates.append(f"{field} = ?")
            values.append(value)
    
    if not updates:
        return {"success": False, "error": "No fields to update"}
    
    values.append(strategy_id)
    
    with get_db() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(f'''
                UPDATE strategies SET {", ".join(updates)} WHERE id = ?
            ''', values)
            conn.commit()
            if cursor.rowcount > 0:
                return {"success": True}
            return {"success": False, "error": "Strategy not found"}
        except Exception as e:
            return {"success": False, "error": str(e)}


def delete_strategy(strategy_id: int) -> dict:
    """Delete a strategy"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM strategies WHERE id = ?', (strategy_id,))
        conn.commit()
        if cursor.rowcount > 0:
            return {"success": True}
        return {"success": False, "error": "Strategy not found"}
