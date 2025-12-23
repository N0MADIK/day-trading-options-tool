import sys
import io
import traceback
import json
import logging
from datetime import datetime
from services.database import get_db

# Configure logger
logger = logging.getLogger("ExecutionEngine")
logger.setLevel(logging.INFO)

class StrategyContext:
    """
    Context object injected into the user's script.
    Provides access to market data, logging, and account functions.
    """
    def __init__(self):
        self.logs = []
        self.market = MarketDataClient()
    
    def log(self, message):
        """Append a log message to the execution operations"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.logs.append(f"[{timestamp}] {message}")
        print(f"[{timestamp}] {message}")

class MarketDataClient:
    """
    Mock/Real market data client exposed to the user script.
    In a real scenario, this would import 'yfinance' or other providers.
    """
    def get_price(self, ticker):
        # TODO: Hook into actual data provider or cache
        # For now, return a dummy price to enable testing
        return 150.00
    
    def get_chain(self, ticker, expiry=None):
        return []

def run_strategy_host(strategy_id, code):
    """
    Execute a strategy script directly on the host machine.
    WARNING: RESTRICTED SCOPE, but still capable of host actions.
    """
    
    # 1. Prepare Context and Capture IO
    context = StrategyContext()
    
    # Capture stdout/stderr
    capture_io = io.StringIO()
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    
    sys.stdout = capture_io
    sys.stderr = capture_io
    
    status = "SUCCESS"
    trades_generated = 0
    error_msg = None
    
    try:
        # 2. Define the execution environment (globals)
        # We inject 'context' and some safe builtins.
        # User script MUST implement a 'run(context)' function.
        
        local_scope = {}
        
        # Execute the definition
        exec(code, {}, local_scope)
        
        if 'run' not in local_scope:
            raise Exception("Script must define a 'run(context)' function.")
        
        # 3. Run the strategy function
        # Expecting it to return a list of trade dictionaries
        # run(context) -> [{'ticker': 'SPY', ...}]
        result_trades = local_scope['run'](context)
        
        if result_trades and isinstance(result_trades, list):
            trades_generated = len(result_trades)
            # TODO: Persist trades to DB
            for trade in result_trades:
                context.log(f"Generated Trade: {trade}")
        
    except Exception as e:
        status = "ERROR"
        error_msg = str(e)
        trace = traceback.format_exc()
        print(f"Runtime Error: {error_msg}\n{trace}")
        
    finally:
        # Restore IO
        sys.stdout = original_stdout
        sys.stderr = original_stderr
    
    # 4. Log the result to DB
    log_output = capture_io.getvalue()
    if context.logs:
        log_output += "\n=== Context Logs ===\n" + "\n".join(context.logs)
        
    save_execution_log(strategy_id, status, log_output, trades_generated)
    
    return {
        "status": status,
        "logs": log_output,
        "trades": trades_generated
    }

def run_strategy_docker(strategy_id, code):
    """
    Execute strategy in a Docker container (python:3.9-slim).
    Uses host.docker.internal to access API.
    """
    import os
    import docker
    import tempfile
    import shutil
    
    status = "SUCCESS"
    trades_generated = 0
    log_output = ""
    
    # Check if docker is available
    try:
        client = docker.from_env()
        client.ping()
    except Exception as e:
        return {
            "status": "ERROR",
            "logs": f"Docker not available: {e}",
            "trades": 0
        }

    # Create temp dir for execution context
    tmp_dir = tempfile.mkdtemp()
    
    try:
        # 1. Write User Script
        with open(os.path.join(tmp_dir, "strategy.py"), "w") as f:
            f.write(code)
            
        # 2. Write Wrapper Script (The entry point)
        wrapper_code = """
import sys
import requests
import json
import traceback
from datetime import datetime
try:
    import strategy
except Exception:
    traceback.print_exc()
    sys.exit(1)

API_URL = "http://host.docker.internal:8000/api"

class RemoteMarketData:
    def get_price(self, ticker):
        try:
            # Use quote-lite for speed
            res = requests.get(f"{API_URL}/quote-lite/{ticker.upper()}", timeout=2)
            if res.ok:
                return res.json().get('price', 0.0)
        except:
            pass
        return 0.0
    
    def get_chain(self, ticker, expiry=None):
        return []

class RemoteContext:
    def __init__(self):
        self.market = RemoteMarketData()
        self.logs = []
    
    def log(self, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"[{ts}] {msg}")
        self.logs.append(f"[{ts}] {msg}")

def main():
    ctx = RemoteContext()
    try:
        if not hasattr(strategy, 'run'):
            print("Error: Strategy must define run(context)")
            return
            
        trades = strategy.run(ctx)
        
        # Output trades as specific formatted JSON on last line for parsing?
        # Or just print them.
        if trades:
            for t in trades:
                ctx.log(f"Generated: {t}")
            
    except Exception:
        traceback.print_exc()

if __name__ == "__main__":
    main()
"""
        with open(os.path.join(tmp_dir, "main.py"), "w") as f:
            f.write(wrapper_code)
            
        # 3. Write requirements (requests)
        with open(os.path.join(tmp_dir, "requirements.txt"), "w") as f:
            f.write("requests\n")

        # 4. Run Container
        # We mount the tmp_dir to /app and run python /app/main.py
        # We need to ensure 'requests' is installed. 
        # Using a heavy image or installing on fly is slow.
        # Ideally use a pre-built image. For now, use python:3.9-slim and pip install (slow but works)
        
        logs = client.containers.run(
            image="python:3.9-slim",
            command="/bin/sh -c 'pip install requests -q && python /app/main.py'",
            volumes={tmp_dir: {'bind': '/app', 'mode': 'rw'}},
            extra_hosts={"host.docker.internal": "host-gateway"},
            remove=True,
            stdout=True,
            stderr=True,
            working_dir="/app"
        )
        
        log_output = logs.decode('utf-8')

    except Exception as e:
        status = "ERROR"
        log_output = f"Container Error: {str(e)}"
    finally:
        shutil.rmtree(tmp_dir)
        
    save_execution_log(strategy_id, status, log_output, trades_generated)
    
    return {
        "status": status,
        "logs": log_output,
        "trades": trades_generated
    }

def save_execution_log(strategy_id, status, output, trades_count):
    """Persist execution result to database"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO strategy_logs (strategy_id, status, output, trades_generated)
                VALUES (?, ?, ?, ?)
            ''', (strategy_id, status, output, trades_count))
            
            # Update last run time
            cursor.execute('''
                UPDATE custom_strategies 
                SET last_run = CURRENT_TIMESTAMP 
                WHERE id = ?
            ''', (strategy_id,))
            
            conn.commit()
    except Exception as e:
        logger.error(f"Failed to save strategy log: {e}")

