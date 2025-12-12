"""
Unit tests for Trade Tracker features
Phase 1: Database, Services, Scheduler
"""
import unittest
import os
import sys
import shutil
import tempfile
from unittest.mock import MagicMock, patch

# Add parent directory to path to import services
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import services after path setup
from services import database
from services import strategies
from services import trades
from services import notifications
from services import scheduler

class TestCompilation(unittest.TestCase):
    """Test that all modules compile and import without errors"""
    
    def test_imports(self):
        self.assertTrue(True)
        print("Imports successful")

class TestDatabaseSetup(unittest.TestCase):
    """Test database initialization and schema"""
    
    def setUp(self):
        # Create a temporary directory/file for the test database
        self.test_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.test_dir, 'test_watchlist.db')
        
        # Patch the DB_PATH in database module
        self.patcher = patch('services.database.DB_PATH', self.db_path)
        self.patcher.start()
        
        # Initialize DB
        database.init_db()
        
    def tearDown(self):
        self.patcher.stop()
        shutil.rmtree(self.test_dir)
        
    def test_tables_exist(self):
        with database.get_db() as conn:
            cursor = conn.cursor()
            
            # Check strategies table
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='strategies'")
            self.assertIsNotNone(cursor.fetchone())
            
            # Check trades table
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='trades'")
            self.assertIsNotNone(cursor.fetchone())
            
            # Check columns in strategies
            cursor.execute("PRAGMA table_info(strategies)")
            columns = [col[1] for col in cursor.fetchall()]
            expected = ['id', 'name', 'scan_criteria', 'default_stop_loss_pct']
            for col in expected:
                self.assertIn(col, columns)
                
    def test_strategies_crud(self):
        # Create
        res = strategies.create_strategy("Test Strat", "Desc", {"sector": "tech"})
        self.assertTrue(res['success'])
        strat_id = res['id']
        
        # Read
        strat = strategies.get_strategy_by_id(strat_id)
        self.assertEqual(strat['name'], "Test Strat")
        self.assertEqual(strat['scan_criteria']['sector'], "tech")
        
        # Update
        strategies.update_strategy(strat_id, name="Updated Strat")
        strat = strategies.get_strategy_by_id(strat_id)
        self.assertEqual(strat['name'], "Updated Strat")
        
        # Delete
        strategies.delete_strategy(strat_id)
        strat = strategies.get_strategy_by_id(strat_id)
        self.assertIsNone(strat)

class TestTradesService(unittest.TestCase):
    """Test trade management"""
    
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.test_dir, 'test_watchlist.db')
        self.patcher = patch('services.database.DB_PATH', self.db_path)
        self.patcher.start()
        database.init_db()
        
        # Create a strategy for foreign key
        res = strategies.create_strategy("Base Strat")
        self.strat_id = res['id']
        
    def tearDown(self):
        self.patcher.stop()
        shutil.rmtree(self.test_dir)
        
    def test_create_and_get_trade(self):
        res = trades.create_trade(
            contract_symbol="SPY241220C550",
            ticker="SPY",
            entry_price=5.00,
            quantity=2,
            strategy_id=self.strat_id
        )
        self.assertTrue(res['success'])
        trade_id = res['id']
        
        trade = trades.get_trade_by_id(trade_id)
        self.assertEqual(trade['ticker'], "SPY")
        self.assertEqual(trade['strategy_id'], self.strat_id)
        self.assertEqual(trade['status'], "OPEN")
        self.assertEqual(trade['quantity'], 2)
        
    def test_close_trade_logic(self):
        # Create trade
        res = trades.create_trade("TEST", "TEST", 10.00, quantity=1)
        trade_id = res['id']
        
        # Close with profit
        res = trades.close_trade(trade_id, 12.00)
        self.assertTrue(res['success'])
        self.assertEqual(res['status'], "CLOSED_WIN")
        self.assertEqual(res['pnl'], 200.0) # (12-10)*1*100
        
        # Verify DB update
        trade = trades.get_trade_by_id(trade_id)
        self.assertEqual(trade['status'], "CLOSED_WIN")
        self.assertEqual(trade['exit_price'], 12.00)
        self.assertIsNotNone(trade['exit_date'])
        
    def test_stats_calculation(self):
        # Win
        t1 = trades.create_trade("T1", "T", 10.00)
        trades.close_trade(t1['id'], 12.00) # +200
        
        # Loss
        t2 = trades.create_trade("T2", "T", 10.00)
        trades.close_trade(t2['id'], 8.00) # -200
        
        # Open
        trades.create_trade("T3", "T", 10.00)
        
        stats = trades.get_trade_stats()
        self.assertEqual(stats['total_trades'], 3)
        self.assertEqual(stats['open_trades'], 1)
        self.assertEqual(stats['wins'], 1)
        self.assertEqual(stats['losses'], 1)
        self.assertEqual(stats['total_pnl'], 0) # +200 - 200

class TestNotificationsService(unittest.TestCase):
    def test_notification_queue(self):
        notifications.clear_notifications()
        notifications.send_notification(1, "TEST", "CLOSED_WIN", 10.0, 100.0)
        
        notifs = notifications.get_notifications()
        self.assertEqual(len(notifs), 1)
        self.assertFalse(notifs[0]['read'])
        
        notifications.mark_notification_read(notifs[0]['id'])
        notifs = notifications.get_notifications()
        self.assertTrue(notifs[0]['read'])
        
        self.assertEqual(notifications.get_unread_count(), 0)

class TestSchedulerModule(unittest.TestCase):
    @patch('services.scheduler.BackgroundScheduler')
    def test_scheduler_init(self, mock_scheduler_cls):
        mock_instance = MagicMock()
        mock_scheduler_cls.return_value = mock_instance
        
        # Test init
        scheduler.init_scheduler()
        mock_instance.start.assert_called_once()
        
        # Test shutdown
        scheduler.shutdown_scheduler()
        mock_instance.shutdown.assert_called_once()

if __name__ == '__main__':
    unittest.main()
