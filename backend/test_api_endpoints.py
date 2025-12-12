"""
Tests for API endpoints
Phase 2: API Layer
"""
import unittest
import os
import sys
import json
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import app

class TestAPIEndpoints(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        
        # Mock database calls to avoid real DB interaction
        self.strategies_patcher = patch('main.get_all_strategies')
        self.mock_get_strategies = self.strategies_patcher.start()
        
        self.trades_patcher = patch('main.get_all_trades')
        self.mock_get_trades = self.trades_patcher.start()
        
    def tearDown(self):
        self.strategies_patcher.stop()
        self.trades_patcher.stop()

    def test_get_strategies(self):
        self.mock_get_strategies.return_value = [{"id": 1, "name": "Test Strat"}]
        response = self.client.get("/api/strategies")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"strategies": [{"id": 1, "name": "Test Strat"}]})

    @patch('main.create_strategy')
    def test_create_strategy(self, mock_create):
        mock_create.return_value = {"success": True, "id": 1}
        payload = {
            "name": "New Strat",
            "description": "Desc",
            "default_stop_loss_pct": 0.1
        }
        response = self.client.post("/api/strategies", json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])

    def test_get_trades(self):
        self.mock_get_trades.return_value = []
        response = self.client.get("/api/trades")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"trades": []})
        
    @patch('main.create_trade')
    def test_create_trade_endpoint(self, mock_create):
        mock_create.return_value = {"success": True, "id": 1}
        payload = {
            "contract_symbol": "TEST",
            "ticker": "TEST",
            "entry_price": 10.0,
            "quantity": 1
        }
        response = self.client.post("/api/trades", json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        
    @patch('main.get_trade_by_id')
    @patch('main.close_trade')
    def test_close_trade(self, mock_close, mock_get):
        mock_get.return_value = {"id": 1, "status": "OPEN"}
        mock_close.return_value = {"success": True, "status": "CLOSED_WIN", "pnl": 100}
        
        response = self.client.post("/api/trades/1/close", json={"exit_price": 11.0})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['pnl'], 100)

class TestAPIValidation(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_create_trade_validation(self):
        # Missing required fields
        response = self.client.post("/api/trades", json={})
        self.assertEqual(response.status_code, 422) 

if __name__ == '__main__':
    unittest.main()
