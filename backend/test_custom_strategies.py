import unittest
import os
import sys
import sqlite3
import json
from services.database import get_db, init_db, DB_PATH
from services.execution_engine import run_strategy_host

class TestCustomStrategies(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        # Use a test database
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
        init_db()

    def setUp(self):
        # Clean custom strategies tables before each test
        with get_db() as conn:
            conn.execute("DELETE FROM custom_strategies")
            conn.execute("DELETE FROM strategy_logs")
            conn.commit()
    
    def create_strategy(self, name, code):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO custom_strategies (name, code, is_active)
                VALUES (?, ?, 1)
            ''', (name, code))
            conn.commit()
            return cursor.lastrowid

    def test_create_strategy(self):
        """Test database persistence of a strategy"""
        sid = self.create_strategy("Test Strat", "def run(ctx): pass")
        self.assertIsNotNone(sid)
        
        with get_db() as conn:
            row = conn.execute("SELECT * FROM custom_strategies WHERE id=?", (sid,)).fetchone()
            self.assertEqual(row['name'], "Test Strat")

    def test_run_valid_strategy(self):
        """Test execution of a valid python script"""
        code = """
def run(context):
    context.log("Hello from test")
    price = context.market.get_price("AAPL")
    context.log(f"Price is {price}")
    return [{"ticker": "AAPL", "action": "BUY"}]
"""
        sid = self.create_strategy("Valid Strat", code)
        
        result = run_strategy_host(sid, code)
        
        self.assertEqual(result['status'], "SUCCESS")
        self.assertEqual(result['trades'], 1)
        self.assertIn("Hello from test", result['logs'])
        self.assertIn("Price is 150.0", result['logs']) # Mocked price
        
        # Verify db log
        with get_db() as conn:
            log = conn.execute("SELECT * FROM strategy_logs WHERE strategy_id=?", (sid,)).fetchone()
            self.assertEqual(log['status'], "SUCCESS")
            self.assertEqual(log['trades_generated'], 1)

    def test_run_syntax_error(self):
        """Test handling of syntax errors in user code"""
        code = """
def run(context):
    print("Missing closing parenthesis"
"""
        sid = self.create_strategy("Bad Syntax", code)
        result = run_strategy_host(sid, code)
        
        self.assertEqual(result['status'], "ERROR")
        self.assertIn("SyntaxError", result['logs'])

    def test_run_runtime_error(self):
        """Test handling of runtime exceptions"""
        code = """
def run(context):
    x = 1 / 0
"""
        sid = self.create_strategy("Runtime Error", code)
        result = run_strategy_host(sid, code)
        
        self.assertEqual(result['status'], "ERROR")
        self.assertIn("ZeroDivisionError", result['logs'])

    def test_missing_run_function(self):
        """Test script without entry point"""
        code = """
def other_function():
    pass
"""
        sid = self.create_strategy("No Run", code)
        result = run_strategy_host(sid, code)
        
        self.assertEqual(result['status'], "ERROR")
        self.assertIn("Script must define", result['logs'])

if __name__ == '__main__':
    unittest.main()
