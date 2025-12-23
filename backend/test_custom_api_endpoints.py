import unittest
import asyncio
from main import (
    create_new_custom_strategy, CustomStrategyRequest, 
    list_custom_strategies,
    get_custom_strategy_details, toggle_custom_strategy, execute_custom_strategy_manual
)
from services.database import get_db, init_db, DB_PATH
import os

class TestCustomAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
        init_db()

    def setUp(self):
        # Clear custom strategies
        with get_db() as conn:
            conn.execute("DELETE FROM custom_strategies")
            conn.commit()
            
    def run_async(self, coro):
        return asyncio.run(coro)

    def test_create_and_run_flow(self):
        # 1. Create Strategy
        import main # Force load
        
        req = CustomStrategyRequest(
            name="API Test Strat",
            code="def run(context): return [{'ticker':'SPY', 'action':'BUY'}]",
            schedule_type="INTERVAL",
            schedule_value="60",
            execution_type="HOST"
        )
        
        # Call handler directly
        res = self.run_async(create_new_custom_strategy(req))
        self.assertIn("id", res)
        sid = res["id"]

        # 2. Get Strategy
        res = self.run_async(get_custom_strategy_details(sid))
        self.assertEqual(res['name'], "API Test Strat")

        # 3. Toggle Active
        res = self.run_async(toggle_custom_strategy(sid))
        self.assertTrue(res['active'])

        # 4. Manual Execute
        res = self.run_async(execute_custom_strategy_manual(sid))
        self.assertEqual(res['status'], "SUCCESS")
        self.assertEqual(res['trades'], 1)

if __name__ == '__main__':
    unittest.main()
