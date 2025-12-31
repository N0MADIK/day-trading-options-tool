"""
Test suite for the Personal Finance Connector Framework
"""
import os
import sys
import sqlite3

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_demo_mode_flag():
    """Test that FINANCE_DEMO_MODE flag is read correctly."""
    os.environ["FINANCE_DEMO_MODE"] = "true"
    
    from services.finance.connector_aggregator import AggregatorConnector
    from services.finance.connector_robinhood import RobinhoodCryptoConnector
    
    agg = AggregatorConnector()
    rh = RobinhoodCryptoConnector()
    
    assert agg._is_demo_mode() == True, "Aggregator should be in demo mode"
    assert rh._is_demo_mode() == True, "Robinhood should be in demo mode"
    print("✓ Demo mode flag test passed")


def test_database_init():
    """Test database initialization."""
    from services.finance.database import init_finance_db, get_all_institutions, FINANCE_DB_PATH
    
    # Remove existing DB for clean test
    if FINANCE_DB_PATH.exists():
        FINANCE_DB_PATH.unlink()
    
    init_finance_db()
    
    institutions = get_all_institutions()
    assert len(institutions) >= 4, f"Expected at least 4 institutions, got {len(institutions)}"
    
    # Check institution names
    names = [i.name for i in institutions]
    assert "Fidelity" in names
    assert "Vanguard" in names
    assert "Robinhood (Crypto)" in names
    
    print("✓ Database initialization test passed")


def test_demo_data_seeding():
    """Test demo data seeding."""
    from services.finance.database import (
        init_finance_db, seed_demo_data, clear_demo_data,
        get_all_connections, get_accounts_by_connection, FINANCE_DB_PATH
    )
    
    # Clean start
    if FINANCE_DB_PATH.exists():
        FINANCE_DB_PATH.unlink()
    
    init_finance_db()
    
    # Seed demo data
    result = seed_demo_data()
    assert result == True, "Seeding should succeed on first run"
    
    # Check connections exist
    connections = get_all_connections()
    assert len(connections) >= 3, f"Expected at least 3 connections, got {len(connections)}"
    
    # Check accounts exist
    total_accounts = 0
    for conn in connections:
        accounts = get_accounts_by_connection(conn.id)
        total_accounts += len(accounts)
    
    assert total_accounts >= 5, f"Expected at least 5 accounts, got {total_accounts}"
    
    # Re-seed should skip
    result2 = seed_demo_data()
    assert result2 == False, "Re-seeding should skip (data exists)"
    
    # Clear and verify
    clear_demo_data()
    connections_after = get_all_connections()
    assert len(connections_after) == 0, "Connections should be cleared"
    
    print("✓ Demo data seeding test passed")


def test_connector_sync():
    """Test connector sync returns valid data."""
    os.environ["FINANCE_DEMO_MODE"] = "true"
    
    from services.finance.connector_aggregator import AggregatorConnector
    from services.finance.connector_robinhood import RobinhoodCryptoConnector
    from services.finance.models import SyncMode
    
    # Test aggregator
    agg = AggregatorConnector()
    agg_result = agg.sync_connection(1, {"access_token": "demo"}, SyncMode.INITIAL)
    
    assert agg_result.success == True
    assert len(agg_result.accounts) >= 1, "Should have accounts"
    assert len(agg_result.holdings) >= 1, "Should have holdings"
    
    # Test Robinhood
    rh = RobinhoodCryptoConnector()
    rh_result = rh.sync_connection(2, {"access_token": "demo"}, SyncMode.INITIAL)
    
    assert rh_result.success == True
    assert len(rh_result.accounts) >= 1
    assert "rh_crypto_main" in rh_result.holdings or len(rh_result.holdings) >= 1
    
    print("✓ Connector sync test passed")


def test_overview_integration():
    """Test that overview pulls from database correctly."""
    from services.finance.database import init_finance_db, seed_demo_data, clear_demo_data, FINANCE_DB_PATH
    from services.overview import get_finance_overview
    
    # Setup
    if FINANCE_DB_PATH.exists():
        FINANCE_DB_PATH.unlink()
    init_finance_db()
    seed_demo_data()
    
    # Get overview
    overview = get_finance_overview()
    
    assert "netWorthTotal" in overview
    assert "custodians" in overview
    assert overview["netWorthTotal"]["value"] > 0
    assert len(overview["custodians"]) >= 3
    assert overview.get("source") == "database"
    
    # Cleanup
    clear_demo_data()
    
    # Should fall back to mock
    overview_mock = get_finance_overview()
    assert overview_mock.get("source") == "mock"
    
    print("✓ Overview integration test passed")


def run_all_tests():
    """Run all tests."""
    print("\n" + "="*60)
    print("Running Finance Connector Framework Tests")
    print("="*60 + "\n")
    
    try:
        test_demo_mode_flag()
        test_database_init()
        test_demo_data_seeding()
        test_connector_sync()
        test_overview_integration()
        
        print("\n" + "="*60)
        print("All tests passed! ✓")
        print("="*60 + "\n")
        return True
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        return False
    except Exception as e:
        print(f"\n✗ Test error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
