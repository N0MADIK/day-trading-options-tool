"""
Tests for Finance-Flow Integration Endpoints
Tests the new routers added for finance-flow frontend compatibility
"""
import pytest
from httpx import AsyncClient


class TestProfilesRouter:
    """Test /api/v1/profiles endpoints"""
    
    @pytest.mark.asyncio
    async def test_get_my_profile(self, authenticated_client: AsyncClient):
        """Test GET /api/v1/profiles/me"""
        response = await authenticated_client.get("/api/v1/profiles/me")
        # Should return 404 since user doesn't exist in test db
        assert response.status_code in [200, 404]


class TestUserRolesRouter:
    """Test /api/v1/roles endpoints"""
    
    @pytest.mark.asyncio
    async def test_get_my_roles(self, authenticated_client: AsyncClient):
        """Test GET /api/v1/roles/me"""
        response = await authenticated_client.get("/api/v1/roles/me")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    @pytest.mark.asyncio
    async def test_check_role(self, authenticated_client: AsyncClient):
        """Test GET /api/v1/roles/check/{role}"""
        response = await authenticated_client.get("/api/v1/roles/check/admin")
        assert response.status_code == 200
        data = response.json()
        assert "has_role" in data
        assert data["role"] == "admin"


class TestMarketDataSubscriptionsRouter:
    """Test /api/v1/market-data-subscriptions endpoints"""
    
    @pytest.mark.asyncio
    async def test_list_providers(self, authenticated_client: AsyncClient):
        """Test GET /api/v1/market-data-subscriptions/providers"""
        response = await authenticated_client.get("/api/v1/market-data-subscriptions/providers")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        # Check provider structure
        provider = data[0]
        assert "id" in provider
        assert "name" in provider
        assert "type" in provider
    
    @pytest.mark.asyncio
    async def test_list_subscriptions(self, authenticated_client: AsyncClient):
        """Test GET /api/v1/market-data-subscriptions/"""
        response = await authenticated_client.get("/api/v1/market-data-subscriptions/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestNetWorthRouter:
    """Test /api/v1/net-worth endpoints"""
    
    @pytest.mark.asyncio
    async def test_get_history(self, authenticated_client: AsyncClient):
        """Test GET /api/v1/net-worth/history"""
        response = await authenticated_client.get("/api/v1/net-worth/history")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    @pytest.mark.asyncio
    async def test_get_summary(self, authenticated_client: AsyncClient):
        """Test GET /api/v1/net-worth/summary"""
        response = await authenticated_client.get("/api/v1/net-worth/summary")
        assert response.status_code == 200
        data = response.json()
        assert "total_net_worth" in data
        assert "total_assets" in data
        assert "total_liabilities" in data
    
    @pytest.mark.asyncio
    async def test_get_goals(self, authenticated_client: AsyncClient):
        """Test GET /api/v1/net-worth/goals"""
        response = await authenticated_client.get("/api/v1/net-worth/goals")
        # Returns null/None if no goals, or the goal object
        assert response.status_code == 200


class TestNotificationSettingsRouter:
    """Test /api/v1/notification-settings endpoints"""
    
    @pytest.mark.asyncio
    async def test_get_notification_settings(self, authenticated_client: AsyncClient):
        """Test GET /api/v1/notification-settings/"""
        response = await authenticated_client.get("/api/v1/notification-settings/")
        assert response.status_code == 200
        data = response.json()
        # Should have default settings
        assert "email_notifications" in data
        assert "push_notifications" in data
        assert "price_alerts" in data
    
    @pytest.mark.asyncio
    async def test_update_notification_settings(self, authenticated_client: AsyncClient):
        """Test PUT /api/v1/notification-settings/"""
        response = await authenticated_client.put(
            "/api/v1/notification-settings/",
            json={"email_notifications": False}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email_notifications"] == False


class TestCustomNotificationRulesRouter:
    """Test /api/v1/custom-notification-rules endpoints"""
    
    @pytest.mark.asyncio
    async def test_list_rules(self, authenticated_client: AsyncClient):
        """Test GET /api/v1/custom-notification-rules/"""
        response = await authenticated_client.get("/api/v1/custom-notification-rules/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestConnectedAccountsRouter:
    """Test /api/v1/connected-accounts endpoints"""
    
    @pytest.mark.asyncio
    async def test_list_connected_accounts(self, authenticated_client: AsyncClient):
        """Test GET /api/v1/connected-accounts/"""
        response = await authenticated_client.get("/api/v1/connected-accounts/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestMarketDataRouter:
    """Test /api/v1/market endpoints"""
    
    @pytest.mark.asyncio
    async def test_get_quote(self, authenticated_client: AsyncClient):
        """Test POST /api/v1/market/quote"""
        response = await authenticated_client.post(
            "/api/v1/market/quote",
            json={"symbol": "AAPL"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "AAPL"
        assert "price" in data
        assert "timestamp" in data


class TestHealthEndpoint:
    """Basic health check test"""
    
    @pytest.mark.asyncio
    async def test_health_check(self, client: AsyncClient):
        """Test health endpoint is accessible"""
        response = await client.get("/api/v1/health")
        assert response.status_code == 200


# Run with: pytest tests/test_finance_flow_integration.py -v
