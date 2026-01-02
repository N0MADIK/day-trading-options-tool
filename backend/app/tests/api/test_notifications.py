import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from app.main import app


client = TestClient(app)


class TestNotificationsAPI:
    """Test notifications API endpoints"""
    
    @patch("app.api.v1.routers.notifications.get_notification_service")
    def test_create_notification_success(self, mock_get_service):
        """Test creating a notification successfully"""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.create_notification.return_value = {
            "success": True,
            "notification_id": 1,
            "notification": {
                "id": 1,
                "title": "Test Notification",
                "type": "TRADE_CLOSED"
            }
        }
        mock_get_service.return_value = mock_service
        
        # Execute
        response = client.post("/api/v1/notifications/", json={
            "user_id": 1,
            "type": "TRADE_CLOSED",
            "title": "Test Notification",
            "message": "Your AAPL trade has been closed",
            "priority": "HIGH"
        })
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["notification_id"] == 1
    
    @patch("app.api.v1.routers.notifications.get_notification_service")
    def test_create_notification_validation_error(self, mock_get_service):
        """Test creating a notification with validation error"""
        # Setup mock
        mock_service = AsyncMock()
        from app.domain.errors import ValidationError
        mock_service.create_notification.side_effect = ValidationError("Title is required")
        mock_get_service.return_value = mock_service
        
        # Execute
        response = client.post("/api/v1/notifications/", json={
            "message": "Test notification without title"
        })
        
        # Assert
        assert response.status_code == 400
        assert "Title is required" in response.json()["detail"]
    
    @patch("app.api.v1.routers.notifications.get_notification_service")
    def test_list_notifications_success(self, mock_get_service):
        """Test listing notifications successfully"""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.list_notifications.return_value = [
            {
                "id": 1,
                "title": "Notification 1",
                "type": "TRADE_CLOSED"
            },
            {
                "id": 2,
                "title": "Notification 2",
                "type": "TRADE_OPENED"
            }
        ]
        mock_get_service.return_value = mock_service
        
        # Execute
        response = client.get("/api/v1/notifications/")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["type"] == "TRADE_CLOSED"
    
    @patch("app.api.v1.routers.notifications.get_notification_service")
    def test_get_notification_by_id_success(self, mock_get_service):
        """Test getting a single notification by ID"""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.get_notification_by_id.return_value = {
            "id": 1,
            "title": "Test Notification",
            "type": "TRADE_CLOSED",
            "read": False
        }
        mock_get_service.return_value = mock_service
        
        # Execute
        response = client.get("/api/v1/notifications/1")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["read"] is False
    
    @patch("app.api.v1.routers.notifications.get_notification_service")
    def test_get_notification_by_id_not_found(self, mock_get_service):
        """Test getting a non-existent notification"""
        # Setup mock
        mock_service = AsyncMock()
        from app.domain.errors import NotFoundError
        mock_service.get_notification_by_id.side_effect = NotFoundError("Notification with ID 999 not found")
        mock_get_service.return_value = mock_service
        
        # Execute
        response = client.get("/api/v1/notifications/999")
        
        # Assert
        assert response.status_code == 404
        assert "Notification with ID 999 not found" in response.json()["detail"]
    
    @patch("app.api.v1.routers.notifications.get_notification_service")
    def test_update_notification_success(self, mock_get_service):
        """Test updating a notification successfully"""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.update_notification.return_value = {
            "success": True,
            "notification": {
                "id": 1,
                "title": "Updated Notification",
                "read": True
            }
        }
        mock_get_service.return_value = mock_service
        
        # Execute
        response = client.put("/api/v1/notifications/1", json={
            "read": True
        })
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["notification"]["read"] is True
    
    @patch("app.api.v1.routers.notifications.get_notification_service")
    def test_delete_notification_success(self, mock_get_service):
        """Test deleting a notification successfully"""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.delete_notification.return_value = {
            "success": True,
            "message": "Notification 1 deleted successfully"
        }
        mock_get_service.return_value = mock_service
        
        # Execute
        response = client.delete("/api/v1/notifications/1")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "deleted successfully" in data["message"]
    
    @patch("app.api.v1.routers.notifications.get_notification_service")
    def test_mark_notification_read_success(self, mock_get_service):
        """Test marking notification as read successfully"""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.mark_notification_read.return_value = {
            "success": True,
            "message": "Notification 1 marked as read"
        }
        mock_get_service.return_value = mock_service
        
        # Execute
        response = client.post("/api/v1/notifications/1/read")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "marked as read" in data["message"]
    
    @patch("app.api.v1.routers.notifications.get_notification_service")
    def test_get_unread_count_success(self, mock_get_service):
        """Test getting unread count successfully"""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.get_unread_count.return_value = 5
        
        # Execute
        response = client.get("/api/v1/notifications/unread-count")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["unread_count"] == 5
    
    @patch("app.api.v1.routers.notifications.get_notification_service")
    def test_get_notification_stats_success(self, mock_get_service):
        """Test getting notification statistics successfully"""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.get_notification_stats.return_value = {
            "total_notifications": 100,
            "unread_notifications": 15,
            "read_notifications": 85,
            "pending_notifications": 0,
            "failed_notifications": 0,
            "notifications_by_type": {"TRADE_CLOSED": 50, "TRADE_OPENED": 50},
            "avg_delivery_time_seconds": 2.5,
            "delivery_success_rate": 95.5
        }
        mock_get_service.return_value = mock_service
        
        # Execute
        response = client.get("/api/v1/notifications/stats")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total_notifications"] == 100
        assert data["unread_notifications"] == 15
        assert data["delivery_success_rate"] == 95.5
    
    @patch("app.api.v1.routers.notifications.get_notification_service")
    def test_search_notifications_success(self, mock_get_service):
        """Test searching notifications successfully"""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.search_notifications.return_value = [
            {
                "id": 1,
                "title": "Trade Closed Notification",
                "type": "TRADE_CLOSED"
            }
        ]
        mock_get_service.return_value = mock_service
        
        # Execute
        response = client.get("/api/v1/notifications/search?q=Trade")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert "Trade" in data[0]["title"]
    
    @patch("app.api.v1.routers.notifications.get_notification_service")
    def test_search_notifications_invalid_query(self, mock_get_service):
        """Test searching notifications with invalid query"""
        # Setup mock
        mock_service = AsyncMock()
        from app.domain.errors import ValidationError
        mock_service.search_notifications.side_effect = ValidationError("Search query must be at least 2 characters")
        mock_get_service.return_value = mock_service
        
        # Execute
        response = client.get("/api/v1/notifications/search?q=A")
        
        # Assert
        assert response.status_code == 400
        assert "at least 2 characters" in response.json()["detail"]


class TestNotificationTemplatesAPI:
    """Test notification templates API endpoints"""
    
    @patch("app.api.v1.routers.notifications.get_template_service")
    def test_create_template_success(self, mock_get_service):
        """Test creating a template successfully"""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.create_template.return_value = {
            "success": True,
            "template_id": 1,
            "template": {
                "id": 1,
                "name": "Trade Closed Template",
                "type": "TRADE_CLOSED",
                "title_template": "Trade {{ticker}} Closed",
                "message_template": "Your {{ticker}} trade has been closed with P&L of {{pnl}}"
            }
        }
        mock_get_service.return_value = mock_service
        
        # Execute
        response = client.post("/api/v1/notifications/templates/", json={
            "name": "Trade Closed Template",
            "type": "TRADE_CLOSED",
            "title_template": "Trade {{ticker}} Closed",
            "message_template": "Your {{ticker}} trade has been closed with P&L of {{pnl}}",
            "variables": ["ticker", "pnl"]
        })
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["template_id"] == 1
    
    @patch("app.api.v1.routers.notifications.get_template_service")
    def test_list_templates_success(self, mock_get_service):
        """Test listing templates successfully"""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.list_templates.return_value = [
            {
                "id": 1,
                "name": "Trade Closed Template",
                "type": "TRADE_CLOSED"
            }
        ]
        mock_get_service.return_value = mock_service
        
        # Execute
        response = client.get("/api/v1/notifications/templates/")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Trade Closed Template"
    
    @patch("app.api.v1.routers.notifications.get_template_service")
    def test_render_template_success(self, mock_get_service):
        """Test rendering a template successfully"""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.render_template.return_value = {
            "template_id": 1,
            "rendered_title": "Trade AAPL Closed",
            "rendered_message": "Your AAPL trade has been closed with P&L of 150.50",
            "used_variables": {"ticker": "AAPL", "pnl": "150.50"}
        }
        mock_get_service.return_value = mock_service
        
        # Execute
        response = client.post("/api/v1/notifications/templates/1/render", json={
            "ticker": "AAPL",
            "pnl": "150.50"
        })
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["rendered_title"] == "Trade AAPL Closed"
        assert data["rendered_message"] == "Your AAPL trade has been closed with P&L of 150.50"


class TestNotificationSettingsAPI:
    """Test notification settings API endpoints"""
    
    @patch("app.api.v1.routers.notifications.get_settings_service")
    def test_get_settings_success(self, mock_get_service):
        """Test getting settings successfully"""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.get_settings.return_value = {
            "user_id": 1,
            "enabled_channels": ["IN_APP", "EMAIL"],
            "quiet_hours": {"22:00": "08:00"},
            "min_priority": "LOW",
            "email_address": "user@example.com"
        }
        mock_get_service.return_value = mock_service
        
        # Execute
        response = client.get("/api/v1/notifications/settings/1")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == 1
        assert "EMAIL" in data["enabled_channels"]
    
    @patch("app.api.v1.routers.notifications.get_settings_service")
    def test_update_settings_success(self, mock_get_service):
        """Test updating settings successfully"""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.update_settings.return_value = {
            "success": True,
            "settings": {
                "user_id": 1,
                "enabled_channels": ["IN_APP", "SMS"],
                "email_address": "updated@example.com"
            }
        }
        mock_get_service.return_value = mock_service
        
        # Execute
        response = client.put("/api/v1/notifications/settings/1", json={
            "enabled_channels": ["IN_APP", "SMS"],
            "email_address": "updated@example.com"
        })
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["settings"]["email_address"] == "updated@example.com"
