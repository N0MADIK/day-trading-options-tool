import sqlite3
import logging
from services.database import get_db
from services.scheduler import _scheduler
from services.execution_engine import run_strategy_host, run_strategy_docker
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

def create_custom_strategy(name, code, schedule_type, schedule_value, execution_type):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO custom_strategies (name, code, schedule_type, schedule_value, execution_type, is_active)
            VALUES (?, ?, ?, ?, ?, 0)
        ''', (name, code, schedule_type, schedule_value, execution_type))
        conn.commit()
        return cursor.lastrowid

def get_custom_strategies():
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM custom_strategies ORDER BY id DESC").fetchall()
        return [dict(row) for row in rows]

def get_custom_strategy_by_id(sid):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM custom_strategies WHERE id = ?", (sid,)).fetchone()
        return dict(row) if row else None

def update_custom_strategy(sid, name, code, schedule_type, schedule_value, execution_type):
    with get_db() as conn:
        conn.execute('''
            UPDATE custom_strategies 
            SET name=?, code=?, schedule_type=?, schedule_value=?, execution_type=?
            WHERE id=?
        ''', (name, code, schedule_type, schedule_value, execution_type, sid))
        conn.commit()

def toggle_strategy_active(sid):
    with get_db() as conn:
        cursor = conn.cursor()
        # Toggle state
        cursor.execute('''
            UPDATE custom_strategies 
            SET is_active = NOT is_active
            WHERE id = ?
        ''', (sid,))
        conn.commit()
        
        # Return new state
        row = cursor.execute("SELECT is_active FROM custom_strategies WHERE id=?", (sid,)).fetchone()
        return bool(row['is_active'])

def get_strategy_logs(sid):
    with get_db() as conn:
        rows = conn.execute('''
            SELECT * FROM strategy_logs 
            WHERE strategy_id = ? 
            ORDER BY timestamp DESC 
            LIMIT 50
        ''', (sid,)).fetchall()
        return [dict(row) for row in rows]

# ===== Scheduler Integration =====

def schedule_strategy_job(strategy_id):
    """Add or Update the scheduler job for a strategy"""
    if _scheduler is None:
        logger.warning("Scheduler not initialized")
        return
        
    strat = get_custom_strategy_by_id(strategy_id)
    if not strat or not strat['is_active']:
        return
        
    job_id = f"strat_{strategy_id}"
    
    # Determine Trigger
    trigger = None
    try:
        if strat['schedule_type'] == 'INTERVAL':
            # Value in minutes
            minutes = int(strat['schedule_value'])
            trigger = IntervalTrigger(minutes=minutes)
        elif strat['schedule_type'] == 'CRON':
            # Value is cron string "min hour day month dow"
            parts = strat['schedule_value'].split()
            trigger = CronTrigger.from_crontab(strat['schedule_value'])
            
        if trigger:
            logger.info(f"Scheduling strategy {strategy_id} with {trigger}")
            _scheduler.add_job(
                run_strategy_wrapper,
                trigger,
                args=[strategy_id, strat['code'], strat['execution_type']],
                id=job_id,
                name=f"Custom: {strat['name']}",
                replace_existing=True
            )
    except Exception as e:
        logger.error(f"Failed to schedule strategy {strategy_id}: {e}")

def reschedule_strategy_job(strategy_id):
    """Refreshes the job. If inactive, removes it. If active, updates it."""
    stop_strategy_job(strategy_id)
    schedule_strategy_job(strategy_id)

def stop_strategy_job(strategy_id):
    if _scheduler and _scheduler.get_job(f"strat_{strategy_id}"):
        _scheduler.remove_job(f"strat_{strategy_id}")

def run_strategy_wrapper(strategy_id, code, execution_type):
    """Wrapper to run from scheduler"""
    logger.info(f"Executing strategy {strategy_id} [{execution_type}]")
    if execution_type == 'HOST':
        run_strategy_host(strategy_id, code)
    elif execution_type == 'DOCKER':
        run_strategy_docker(strategy_id, code)
    else:
        logger.warning(f"Unknown execution type: {execution_type}")
