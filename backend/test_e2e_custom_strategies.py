#!/usr/bin/env python3
"""
End-to-end test script for Custom Strategies feature.
Tests the complete flow from API endpoints to database operations.
"""

import asyncio
import httpx
import pytest
from datetime import datetime, timezone, timedelta
from app.main import app
from app.core.database import get_async_session
from app.models.custom_strategies import Strategy, StrategyExecution, StrategyTemplate
from app.repositories.sqlalchemy.custom_strategy_repo import SQLAlchemyCustomStrategyRepository
from app.schemas.custom_strategies import StrategyExecutionType, StrategyStatus, StrategyScheduleType

# Test data
TEST_STRATEGY = {
    "name": "Test Momentum Strategy",
    "description": "A test momentum-based trading strategy",
    "execution_type": "manual",
    "config": {
        "lookback_period": 20,
        "threshold": 0.02,
        "symbols": ["AAPL", "GOOGL", "MSFT"]
    },
    "risk_parameters": {
        "max_position_size": 0.1,
        "stop_loss": 0.05
    }
}

TEST_TEMPLATE = {
    "name": "Momentum Template",
    "description": "Template for momentum strategies",
    "template_type": "momentum",
    "config": {
        "default_lookback": 20,
        "default_threshold": 0.02
    }
}

TEST_BACKTEST_REQUEST = {
    "start_date": "2024-01-01",
    "end_date": "2024-12-31",
    "initial_capital": 10000,
    "parameters": {
        "commission": 0.001,
        "slippage": 0.0001
    }
}

class TestCustomStrategiesE2E:
    """End-to-end tests for Custom Strategies"""
    
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
        # Create test strategy
        strategy = Strategy(
            name=TEST_STRATEGY["name"],
            description=TEST_STRATEGY["description"],
            execution_type=TEST_STRATEGY["execution_type"],
            config=TEST_STRATEGY["config"],
            risk_parameters=TEST_STRATEGY["risk_parameters"],
            status=StrategyStatus.ACTIVE
        )
        db_session.add(strategy)
        await db_session.commit()
        await db_session.refresh(strategy)
        
        # Create test template
        template = StrategyTemplate(
            name=TEST_TEMPLATE["name"],
            description=TEST_TEMPLATE["description"],
            template_type=TEST_TEMPLATE["template_type"],
            config=TEST_TEMPLATE["config"]
        )
        db_session.add(template)
        await db_session.commit()
        await db_session.refresh(template)
        
        return strategy, template
    
    async def cleanup_test_data(self, db_session):
        """Cleanup test data from database"""
        # Delete in reverse order of creation
        await db_session.execute("DELETE FROM strategy_executions")
        await db_session.execute("DELETE FROM strategy_templates")
        await db_session.execute("DELETE FROM strategies")
        await db_session.commit()
    
    async def test_complete_strategy_flow(self, client, db_session):
        """Test complete flow: create strategy -> execute -> backtest -> analytics"""
        
        try:
            # Step 1: Create strategy
            response = await client.post("/api/v1/custom-strategies/strategies", json=TEST_STRATEGY)
            assert response.status_code == 201
            strategy_data = response.json()
            strategy_id = strategy_data["id"]
            assert strategy_data["name"] == TEST_STRATEGY["name"]
            assert strategy_data["execution_type"] == TEST_STRATEGY["execution_type"]
            
            # Step 2: Retrieve and verify strategy
            response = await client.get(f"/api/v1/custom-strategies/strategies/{strategy_id}")
            assert response.status_code == 200
            retrieved_strategy = response.json()
            assert retrieved_strategy["name"] == TEST_STRATEGY["name"]
            assert retrieved_strategy["config"] == TEST_STRATEGY["config"]
            
            # Step 3: Update strategy
            update_data = {
                "name": "Updated Strategy Name",
                "description": "Updated description"
            }
            response = await client.put(f"/api/v1/custom-strategies/strategies/{strategy_id}", json=update_data)
            assert response.status_code == 200
            updated_strategy = response.json()
            assert updated_strategy["name"] == "Updated Strategy Name"
            
            # Step 4: Execute strategy
            execution_request = {
                "strategy_id": strategy_id,
                "parameters": {
                    "symbols": ["AAPL"],
                    "timeframe": "1d"
                }
            }
            response = await client.post(f"/api/v1/custom-strategies/strategies/{strategy_id}/execute", json=execution_request)
            assert response.status_code == 200
            execution_result = response.json()
            assert "execution_id" in execution_result
            
            execution_id = execution_result["execution_id"]
            
            # Step 5: Check execution status
            response = await client.get(f"/api/v1/custom-strategies/strategies/{strategy_id}/executions/{execution_id}")
            assert response.status_code == 200
            execution_status = response.json()
            assert "status" in execution_status
            
            # Step 6: Run backtest
            response = await client.post(f"/api/v1/custom-strategies/strategies/{strategy_id}/backtest", json=TEST_BACKTEST_REQUEST)
            assert response.status_code == 200
            backtest_result = response.json()
            assert "backtest_id" in backtest_result
            assert "total_return" in backtest_result
            assert "sharpe_ratio" in backtest_result
            
            # Step 7: Generate signals
            signal_request = {
                "strategy_id": strategy_id,
                "symbols": ["AAPL", "GOOGL"],
                "timeframe": "1d"
            }
            response = await client.post("/api/v1/custom-strategies/signals", json=signal_request)
            assert response.status_code == 200
            signals = response.json()
            assert "signals" in signals
            assert isinstance(signals["signals"], list)
            
            # Step 8: Validate strategy
            response = await client.post(f"/api/v1/custom-strategies/strategies/{strategy_id}/validate")
            assert response.status_code == 200
            validation_result = response.json()
            assert "is_valid" in validation_result
            assert "errors" in validation_result
            
            # Step 9: Schedule strategy
            schedule_request = {
                "strategy_id": strategy_id,
                "schedule_type": "daily",
                "schedule_config": {
                    "time": "09:30",
                    "timezone": "UTC"
                }
            }
            response = await client.post(f"/api/v1/custom-strategies/strategies/{strategy_id}/schedule", json=schedule_request)
            assert response.status_code == 200
            schedule_result = response.json()
            assert "schedule_id" in schedule_result
            
            # Step 10: Get strategy analytics
            analytics_request = {
                "strategy_id": strategy_id,
                "start_date": "2024-01-01",
                "end_date": "2024-12-31"
            }
            response = await client.post("/api/v1/custom-strategies/analytics", json=analytics_request)
            assert response.status_code == 200
            analytics = response.json()
            assert "performance_metrics" in analytics
            assert "risk_metrics" in analytics
            
            # Step 11: List all strategies
            response = await client.get("/api/v1/custom-strategies/strategies")
            assert response.status_code == 200
            strategies = response.json()
            assert len(strategies) >= 1
            assert any(strategy["id"] == strategy_id for strategy in strategies)
            
            # Step 12: Delete strategy
            response = await client.delete(f"/api/v1/custom-strategies/strategies/{strategy_id}")
            assert response.status_code == 204
            
            # Step 13: Verify deletion
            response = await client.get(f"/api/v1/custom-strategies/strategies/{strategy_id}")
            assert response.status_code == 404
            
            print("✅ Complete Custom Strategies E2E test passed!")
            
        except Exception as e:
            print(f"❌ E2E test failed: {e}")
            raise
    
    async def test_template_management_flow(self, client, db_session):
        """Test template creation and management"""
        
        try:
            # Step 1: Create template
            response = await client.post("/api/v1/custom-strategies/templates", json=TEST_TEMPLATE)
            assert response.status_code == 201
            template_data = response.json()
            template_id = template_data["id"]
            assert template_data["name"] == TEST_TEMPLATE["name"]
            
            # Step 2: Retrieve template
            response = await client.get(f"/api/v1/custom-strategies/templates/{template_id}")
            assert response.status_code == 200
            retrieved_template = response.json()
            assert retrieved_template["template_type"] == TEST_TEMPLATE["template_type"]
            
            # Step 3: List all templates
            response = await client.get("/api/v1/custom-strategies/templates")
            assert response.status_code == 200
            templates = response.json()
            assert len(templates) >= 1
            assert any(template["id"] == template_id for template in templates)
            
            # Step 4: Create strategy from template
            strategy_from_template = {
                "name": "Strategy from Template",
                "template_id": template_id,
                "config_overrides": {
                    "lookback_period": 30
                }
            }
            response = await client.post("/api/v1/custom-strategies/strategies/from-template", json=strategy_from_template)
            assert response.status_code == 201
            strategy_data = response.json()
            strategy_id = strategy_data["id"]
            
            # Step 5: Verify strategy uses template config
            response = await client.get(f"/api/v1/custom-strategies/strategies/{strategy_id}")
            assert response.status_code == 200
            strategy = response.json()
            assert strategy["config"]["lookback_period"] == 30  # Override applied
            
            # Step 6: Cleanup
            await client.delete(f"/api/v1/custom-strategies/strategies/{strategy_id}")
            await client.delete(f"/api/v1/custom-strategies/templates/{template_id}")
            
            print("✅ Template management E2E test passed!")
            
        except Exception as e:
            print(f"❌ Template E2E test failed: {e}")
            raise
    
    async def test_batch_operations_flow(self, client, db_session):
        """Test batch operations on strategies"""
        
        # Create multiple strategies
        strategy_ids = []
        
        try:
            for i in range(3):
                strategy_data = TEST_STRATEGY.copy()
                strategy_data["name"] = f"Test Strategy {i+1}"
                response = await client.post("/api/v1/custom-strategies/strategies", json=strategy_data)
                assert response.status_code == 201
                strategy_ids.append(response.json()["id"])
            
            # Step 1: Batch activate strategies
            batch_request = {
                "operation": "activate",
                "strategy_ids": strategy_ids
            }
            response = await client.post("/api/v1/custom-strategies/batch", json=batch_request)
            assert response.status_code == 200
            batch_result = response.json()
            assert batch_result["success_count"] == 3
            assert batch_result["failed_count"] == 0
            
            # Step 2: Batch update strategies
            update_request = {
                "operation": "update",
                "strategy_ids": strategy_ids,
                "update_data": {
                    "description": "Batch updated description"
                }
            }
            response = await client.post("/api/v1/custom-strategies/batch", json=update_request)
            assert response.status_code == 200
            update_result = response.json()
            assert update_result["success_count"] == 3
            
            # Step 3: Verify updates
            for strategy_id in strategy_ids:
                response = await client.get(f"/api/v1/custom-strategies/strategies/{strategy_id}")
                assert response.status_code == 200
                strategy = response.json()
                assert strategy["description"] == "Batch updated description"
            
            print("✅ Batch operations E2E test passed!")
            
        except Exception as e:
            print(f"❌ Batch operations E2E test failed: {e}")
            raise
        
        finally:
            # Cleanup
            for strategy_id in strategy_ids:
                await client.delete(f"/api/v1/custom-strategies/strategies/{strategy_id}")
    
    async def test_error_handling_flow(self, client):
        """Test error handling in various scenarios"""
        
        # Test 1: Get non-existent strategy
        response = await client.get("/api/v1/custom-strategies/strategies/99999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
        
        # Test 2: Execute non-existent strategy
        execution_request = {"strategy_id": 99999, "parameters": {}}
        response = await client.post("/api/v1/custom-strategies/strategies/99999/execute", json=execution_request)
        assert response.status_code == 404
        
        # Test 3: Create strategy with invalid data
        invalid_strategy = TEST_STRATEGY.copy()
        invalid_strategy["execution_type"] = "invalid_type"
        response = await client.post("/api/v1/custom-strategies/strategies", json=invalid_strategy)
        assert response.status_code == 422  # Validation error
        
        # Test 4: Backtest with invalid date range
        invalid_backtest = TEST_BACKTEST_REQUEST.copy()
        invalid_backtest["start_date"] = "2024-12-31"
        invalid_backtest["end_date"] = "2024-01-01"  # End before start
        response = await client.post("/api/v1/custom-strategies/strategies/1/backtest", json=invalid_backtest)
        assert response.status_code == 400  # Business logic error
        
        print("✅ Error handling E2E test passed!")

async def run_e2e_tests():
    """Run all E2E tests"""
    print("🚀 Starting Custom Strategies E2E Tests...")
    
    # Create test instance
    test_instance = TestCustomStrategiesE2E()
    
    # Setup database session
    async for session in get_async_session():
        try:
            # Create HTTP client
            async with httpx.AsyncClient(app=app, base_url="http://test") as client:
                # Run tests
                await test_instance.test_complete_strategy_flow(client, session)
                await test_instance.test_template_management_flow(client, session)
                await test_instance.test_batch_operations_flow(client, session)
                await test_instance.test_error_handling_flow(client)
                
                print("🎉 All Custom Strategies E2E tests completed successfully!")
                
        except Exception as e:
            print(f"💥 E2E test suite failed: {e}")
            raise
        finally:
            await session.close()

if __name__ == "__main__":
    asyncio.run(run_e2e_tests())
