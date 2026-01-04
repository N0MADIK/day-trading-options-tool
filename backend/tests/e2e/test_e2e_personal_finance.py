#!/usr/bin/env python3
"""
End-to-end test script for Personal Finance Integration feature.
Tests the complete flow from API endpoints to database operations.
"""

import asyncio
import httpx
import pytest
from datetime import datetime, timezone
from app.main import app
from app.core.database import get_async_session
from app.models.personal_finance import Institution, Connection, Account
from app.repositories.sqlalchemy.personal_finance_repo import SQLAlchemyPersonalFinanceRepository

# Test data
TEST_INSTITUTION = {
    "name": "Test Bank",
    "source_type": "plaid",
    "config": {"api_key": "test_key"}
}

TEST_CONNECTION = {
    "institution_id": 1,
    "external_id": "conn_123",
    "status": "connected"
}

TEST_ACCOUNT = {
    "connection_id": 1,
    "external_id": "acc_123",
    "name": "Test Checking Account",
    "account_type": "checking",
    "currency": "USD",
    "balance": 1000.0
}

class TestPersonalFinanceE2E:
    """End-to-end tests for Personal Finance Integration"""
    
    @pytest.fixture
    async def client(self):
        """Test client for HTTP requests"""
        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            yield client
    
    @pytest.fixture
    async def db_session(self):
        """Database session for setup/teardown"""
        async for session in get_async_session():
            yield session
            await session.close()
    
    async def setup_test_data(self, db_session):
        """Setup test data in database"""
        # Create test institution
        institution = Institution(
            name=TEST_INSTITUTION["name"],
            source_type=TEST_INSTITUTION["source_type"],
            config=TEST_INSTITUTION["config"]
        )
        db_session.add(institution)
        await db_session.commit()
        await db_session.refresh(institution)
        
        # Create test connection
        connection = Connection(
            institution_id=institution.id,
            external_id=TEST_CONNECTION["external_id"],
            status=TEST_CONNECTION["status"]
        )
        db_session.add(connection)
        await db_session.commit()
        await db_session.refresh(connection)
        
        # Create test account
        account = Account(
            connection_id=connection.id,
            external_id=TEST_ACCOUNT["external_id"],
            name=TEST_ACCOUNT["name"],
            account_type=TEST_ACCOUNT["account_type"],
            currency=TEST_ACCOUNT["currency"],
            balance=TEST_ACCOUNT["balance"]
        )
        db_session.add(account)
        await db_session.commit()
        await db_session.refresh(account)
        
        return institution, connection, account
    
    async def cleanup_test_data(self, db_session):
        """Cleanup test data from database"""
        # Delete in reverse order of creation
        await db_session.execute("DELETE FROM accounts")
        await db_session.execute("DELETE FROM connections")
        await db_session.execute("DELETE FROM institutions")
        await db_session.commit()
    
    async def test_complete_personal_finance_flow(self, client, db_session):
        """Test complete flow: create institution -> connection -> account -> retrieve data"""
        
        try:
            # Step 1: Create institution
            response = await client.post("/api/v1/personal-finance/institutions", json=TEST_INSTITUTION)
            assert response.status_code == 201
            institution_data = response.json()
            institution_id = institution_data["id"]
            assert institution_data["name"] == TEST_INSTITUTION["name"]
            
            # Step 2: Create connection for the institution
            connection_data = TEST_CONNECTION.copy()
            connection_data["institution_id"] = institution_id
            response = await client.post("/api/v1/personal-finance/connections", json=connection_data)
            assert response.status_code == 201
            connection_response = response.json()
            connection_id = connection_response["id"]
            assert connection_response["institution_id"] == institution_id
            
            # Step 3: Create account for the connection
            account_data = TEST_ACCOUNT.copy()
            account_data["connection_id"] = connection_id
            response = await client.post("/api/v1/personal-finance/accounts", json=account_data)
            assert response.status_code == 201
            account_response = response.json()
            account_id = account_response["id"]
            assert account_response["connection_id"] == connection_id
            assert account_response["balance"] == TEST_ACCOUNT["balance"]
            
            # Step 4: Retrieve and verify institution
            response = await client.get(f"/api/v1/personal-finance/institutions/{institution_id}")
            assert response.status_code == 200
            retrieved_institution = response.json()
            assert retrieved_institution["name"] == TEST_INSTITUTION["name"]
            
            # Step 5: Retrieve and verify connection
            response = await client.get(f"/api/v1/personal-finance/connections/{connection_id}")
            assert response.status_code == 200
            retrieved_connection = response.json()
            assert retrieved_connection["external_id"] == TEST_CONNECTION["external_id"]
            
            # Step 6: Retrieve and verify account
            response = await client.get(f"/api/v1/personal-finance/accounts/{account_id}")
            assert response.status_code == 200
            retrieved_account = response.json()
            assert retrieved_account["name"] == TEST_ACCOUNT["name"]
            assert retrieved_account["balance"] == TEST_ACCOUNT["balance"]
            
            # Step 7: List all institutions
            response = await client.get("/api/v1/personal-finance/institutions")
            assert response.status_code == 200
            institutions = response.json()
            assert len(institutions) >= 1
            assert any(inst["id"] == institution_id for inst in institutions)
            
            # Step 8: List all connections for the institution
            response = await client.get(f"/api/v1/personal-finance/institutions/{institution_id}/connections")
            assert response.status_code == 200
            connections = response.json()
            assert len(connections) >= 1
            assert any(conn["id"] == connection_id for conn in connections)
            
            # Step 9: List all accounts for the connection
            response = await client.get(f"/api/v1/personal-finance/connections/{connection_id}/accounts")
            assert response.status_code == 200
            accounts = response.json()
            assert len(accounts) >= 1
            assert any(acc["id"] == account_id for acc in accounts)
            
            # Step 10: Update account balance
            new_balance = 1500.0
            update_data = {"balance": new_balance}
            response = await client.put(f"/api/v1/personal-finance/accounts/{account_id}", json=update_data)
            assert response.status_code == 200
            updated_account = response.json()
            assert updated_account["balance"] == new_balance
            
            # Step 11: Verify update persisted
            response = await client.get(f"/api/v1/personal-finance/accounts/{account_id}")
            assert response.status_code == 200
            verified_account = response.json()
            assert verified_account["balance"] == new_balance
            
            # Step 12: Delete account
            response = await client.delete(f"/api/v1/personal-finance/accounts/{account_id}")
            assert response.status_code == 204
            
            # Step 13: Verify account deletion
            response = await client.get(f"/api/v1/personal-finance/accounts/{account_id}")
            assert response.status_code == 404
            
            # Step 14: Delete connection
            response = await client.delete(f"/api/v1/personal-finance/connections/{connection_id}")
            assert response.status_code == 204
            
            # Step 15: Delete institution
            response = await client.delete(f"/api/v1/personal-finance/institutions/{institution_id}")
            assert response.status_code == 204
            
            print("✅ Complete Personal Finance E2E test passed!")
            
        except Exception as e:
            print(f"❌ E2E test failed: {e}")
            raise
    
    async def test_error_handling_flow(self, client):
        """Test error handling in various scenarios"""
        
        # Test 1: Get non-existent institution
        response = await client.get("/api/v1/personal-finance/institutions/99999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
        
        # Test 2: Create connection with non-existent institution
        invalid_connection = TEST_CONNECTION.copy()
        invalid_connection["institution_id"] = 99999
        response = await client.post("/api/v1/personal-finance/connections", json=invalid_connection)
        assert response.status_code == 404
        
        # Test 3: Create account with invalid data
        invalid_account = TEST_ACCOUNT.copy()
        invalid_account["balance"] = "invalid_balance"
        response = await client.post("/api/v1/personal-finance/accounts", json=invalid_account)
        assert response.status_code == 422  # Validation error
        
        print("✅ Error handling E2E test passed!")
    
    async def test_analytics_endpoints(self, client, db_session):
        """Test analytics endpoints with real data"""
        
        # Setup test data
        institution, connection, account = await self.setup_test_data(db_session)
        
        try:
            # Test account balance analytics
            response = await client.get("/api/v1/personal-finance/analytics/account-balances")
            assert response.status_code == 200
            analytics = response.json()
            assert "total_balance" in analytics
            assert "account_count" in analytics
            assert analytics["total_balance"] >= TEST_ACCOUNT["balance"]
            
            # Test institution summary
            response = await client.get(f"/api/v1/personal-finance/analytics/institutions/{institution.id}/summary")
            assert response.status_code == 200
            summary = response.json()
            assert "institution" in summary
            assert "connection_count" in summary
            assert "account_count" in summary
            assert summary["connection_count"] >= 1
            assert summary["account_count"] >= 1
            
            print("✅ Analytics E2E test passed!")
            
        finally:
            await self.cleanup_test_data(db_session)

async def run_e2e_tests():
    """Run all E2E tests"""
    print("🚀 Starting Personal Finance E2E Tests...")
    
    # Create test instance
    test_instance = TestPersonalFinanceE2E()
    
    # Setup database session
    async for session in get_async_session():
        try:
            # Create HTTP client
            async with httpx.AsyncClient(app=app, base_url="http://test") as client:
                # Run tests
                await test_instance.test_complete_personal_finance_flow(client, session)
                await test_instance.test_error_handling_flow(client)
                await test_instance.test_analytics_endpoints(client, session)
                
                print("🎉 All Personal Finance E2E tests completed successfully!")
                
        except Exception as e:
            print(f"💥 E2E test suite failed: {e}")
            raise
        finally:
            await session.close()

if __name__ == "__main__":
    asyncio.run(run_e2e_tests())
