import os
import unittest
import sys
import json
from datetime import datetime

# Adjust path to import services
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.finance.connector_snaptrade import SnapTradeConnector

# Mock env vars for testing
os.environ["FINANCE_DEMO_MODE"] = "true"
os.environ["SNAPTRADE_CLIENT_ID"] = "test_client"
os.environ["SNAPTRADE_CONSUMER_KEY"] = "test_key"

class TestSnapTradeConnector(unittest.TestCase):
    
    def test_demo_link_creation(self):
        connector = SnapTradeConnector()
        # Test link creation in demo mode
        result = connector.create_link_session("test_user")
        
        self.assertTrue(result.success)
        self.assertIn("mock", result.link_url)
        self.assertIsNotNone(result.link_token)

    def test_demo_sync(self):
        connector = SnapTradeConnector()
        # Mock auth data
        auth_data = {
            "user_id": "test_user",
            "user_secret": "mock_secret"
        }
        
        result = connector.sync_connection(1, auth_data)
        
        self.assertTrue(result.success)
        self.assertTrue(len(result.accounts) > 0)
        self.assertTrue(len(result.holdings) > 0)
        
        # Check if accounts have expected fields
        acc = result.accounts[0]
        self.assertIsNotNone(acc.name)
        self.assertIsNotNone(acc.external_id)

if __name__ == '__main__':
    unittest.main()
