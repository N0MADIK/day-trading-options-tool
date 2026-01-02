import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from app.services.notification_service import (
    NotificationService, NotificationTemplateService, NotificationSettingsService,
    NotificationDigestService, NotificationDeliveryService
)
from app.repositories.notification_repo import (
    NotificationRepository, NotificationTemplateRepository,
    NotificationSettingsRepository, NotificationDeliveryRepository,
    NotificationDigestRepository
)
from app.schemas.notifications import (
    NotificationCreateRequest, NotificationUpdateRequest, NotificationType,
    NotificationPriority, NotificationChannel, NotificationStatus,
    NotificationListRequest, NotificationTemplateCreateRequest,
    NotificationBatchRequest, NotificationSendRequest,
    NotificationSettingsRequest, NotificationDigestRequest
)
from app.domain.errors import NotFoundError, ConflictError, ValidationError


class TestNotificationService:
    """Test notification service operations"""
    
    @pytest.fixture
    def mock_repositories(self):
        """Create mock repositories"""
        return {
            'notification_repo': AsyncMock(spec=NotificationRepository),
            'template_repo': AsyncMock(spec=NotificationTemplateRepository),
            'settings_repo': AsyncMock(spec=NotificationSettingsRepository),
            'delivery_repo': AsyncMock(spec=NotificationDeliveryRepository),
            'digest_repo': AsyncMock(spec=NotificationDigestRepository)
        }
    
    @pytest.fixture
    def notification_service(self, mock_repositories):
        """Create notification service with mock repositories"""
        return NotificationService(
            mock_repositories['notification_repo'],
            mock_repositories['template_repo'],
            mock_repositories['settings_repo'],
            mock_repositories['delivery_repo'],
            mock_repositories['digest_repo']
        )
    
    @pytest.mark.asyncio
    async def test_create_notification_success(self, notification_service, mock_repositories):
        """Test successful notification creation"""
        # Setup
        notification_data = NotificationCreateRequest(
            user_id=1,
            type=NotificationType.TRADE_CLOSED,
            title="Trade Closed",
            message="Your AAPL trade has been closed",
            priority=NotificationPriority.HIGH,
            channel=NotificationChannel.IN_APP,
            data={"trade_id": 123, "pnl": 150.50}
        )
        
        mock_repositories['notification_repo'].create_notification.return_value = 1
        mock_repositories['notification_repo'].get_notification_by_id.return_value = {
            'id': 1,
            'title': 'Trade Closed',
            'type': 'TRADE_CLOSED'
        }
        
        # Execute
        result = await notification_service.create_notification(notification_data)
        
        # Assert
        assert result["success"] is True
        assert result["notification_id"] == 1
        mock_repositories['notification_repo'].create_notification.assert_called_once_with(notification_data)
    
    @pytest.mark.asyncio
    async def test_get_notification_by_id_success(self, notification_service, mock_repositories):
        """Test successful notification retrieval"""
        # Setup
        mock_notification = {
            'id': 1,
            'title': 'Test Notification',
            'type': 'TRADE_CLOSED'
        }
        mock_repositories['notification_repo'].get_notification_by_id.return_value = mock_notification
        
        # Execute
        result = await notification_service.get_notification_by_id(1)
        
        # Assert
        assert result == mock_notification
        mock_repositories['notification_repo'].get_notification_by_id.assert_called_once_with(1)
    
    @pytest.mark.asyncio
    async def test_get_notification_by_id_not_found(self, notification_service, mock_repositories):
        """Test notification retrieval when not found"""
        mock_repositories['notification_repo'].get_notification_by_id.return_value = None
        
        with pytest.raises(NotFoundError) as exc_info:
            await notification_service.get_notification_by_id(999)
        
        assert "Notification with ID 999 not found" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_list_notifications_success(self, notification_service, mock_repositories):
        """Test successful notification listing"""
        # Setup
        request = NotificationListRequest(user_id=1, limit=10)
        mock_notifications = [
            {'id': 1, 'title': 'Notification 1', 'type': 'TRADE_CLOSED'},
            {'id': 2, 'title': 'Notification 2', 'type': 'TRADE_OPENED'}
        ]
        mock_repositories['notification_repo'].get_all_notifications.return_value = mock_notifications
        
        # Execute
        result = await notification_service.list_notifications(request)
        
        # Assert
        assert len(result) == 2
        assert result[0]['type'] == 'TRADE_CLOSED'
        mock_repositories['notification_repo'].get_all_notifications.assert_called_once_with(
            user_id=1, type=None, priority=None, channel=None, read=None, limit=10, offset=None,
            expires_before=None, created_after=None
        )
    
    @pytest.mark.asyncio
    async def test_mark_notification_read_success(self, notification_service, mock_repositories):
        """Test marking notification as read"""
        # Setup
        mock_repositories['notification_repo'].mark_notification_read.return_value = True
        
        # Execute
        result = await notification_service.mark_notification_read(1)
        
        # Assert
        assert result["success"] is True
        assert "marked as read" in result["message"]
        mock_repositories['notification_repo'].mark_notification_read.assert_called_once_with(1)
    
    @pytest.mark.asyncio
    async def test_mark_notifications_read_success(self, notification_service, mock_repositories):
        """Test marking multiple notifications as read"""
        # Setup
        mock_repositories['notification_repo'].mark_notifications_read.return_value = 3
        
        # Execute
        result = await notification_service.mark_notifications_read([1, 2, 3])
        
        # Assert
        assert result["success"] is True
        assert result["marked_count"] == 3
        mock_repositories['notification_repo'].mark_notifications_read.assert_called_once_with([1, 2, 3])
    
    @pytest.mark.asyncio
    async def test_get_unread_count_success(self, notification_service, mock_repositories):
        """Test getting unread count"""
        # Setup
        mock_repositories['notification_repo'].get_unread_count.return_value = 5
        
        # Execute
        result = await notification_service.get_unread_count(1)
        
        # Assert
        assert result == 5
        mock_repositories['notification_repo'].get_unread_count.assert_called_once_with(1)
    
    @pytest.mark.asyncio
    async def test_get_notification_stats_success(self, notification_service, mock_repositories):
        """Test getting notification statistics"""
        # Setup
        mock_stats = {
            "total_notifications": 100,
            "unread_notifications": 15,
            "read_notifications": 85,
            "pending_notifications": 0,
            "failed_notifications": 0,
            "notifications_by_type": {"TRADE_CLOSED": 50, "TRADE_OPENED": 50},
            "avg_delivery_time_seconds": 2.5,
            "delivery_success_rate": 95.5
        }
        mock_repositories['notification_repo'].get_notification_stats.return_value = mock_stats
        
        # Execute
        result = await notification_service.get_notification_stats(1)
        
        # Assert
        assert result["total_notifications"] == 100
        assert result["unread_notifications"] == 15
        assert result["delivery_success_rate"] == 95.5
    
    @pytest.mark.asyncio
    async def test_search_notifications_success(self, notification_service, mock_repositories):
        """Test successful notification search"""
        # Setup
        search_results = [
            {'id': 1, 'title': 'Trade Closed Notification', 'type': 'TRADE_CLOSED'},
            {'id': 2, 'title': 'Trade Opened Notification', 'type': 'TRADE_OPENED'}
        ]
        mock_repositories['notification_repo'].search_notifications.return_value = search_results
        
        # Execute
        result = await notification_service.search_notifications("Trade", 1)
        
        # Assert
        assert len(result) == 2
        assert "Trade" in result[0]["title"]
        mock_repositories['notification_repo'].search_notifications.assert_called_once_with("Trade", 1)
    
    @pytest.mark.asyncio
    async def test_search_notifications_invalid_query(self, notification_service, mock_repositories):
        """Test notification search with invalid query"""
        # Execute & Assert
        with pytest.raises(ValidationError) as exc_info:
            await notification_service.search_notifications("A")
        
        assert "at least 2 characters" in str(exc_info.value)


class TestNotificationTemplateService:
    """Test notification template service operations"""
    
    @pytest.fixture
    def mock_repository(self):
        """Create mock template repository"""
        return AsyncMock(spec=NotificationTemplateRepository)
    
    @pytest.fixture
    def template_service(self, mock_repository):
        """Create template service with mock repository"""
        return NotificationTemplateService(mock_repository)
    
    @pytest.mark.asyncio
    async def test_create_template_success(self, template_service, mock_repository):
        """Test successful template creation"""
        # Setup
        template_data = NotificationTemplateCreateRequest(
            name="Trade Closed Template",
            type=NotificationType.TRADE_CLOSED,
            title_template="Trade {{ticker}} Closed",
            message_template="Your {{ticker}} trade has been closed with P&L of {{pnl}}",
            default_priority=NotificationPriority.HIGH,
            default_channel=NotificationChannel.IN_APP,
            variables=["ticker", "pnl"]
        )
        
        mock_repository.create_template.return_value = 1
        mock_repository.get_template_by_id.return_value = {
            'id': 1,
            'name': 'Trade Closed Template',
            'title_template': 'Trade {{ticker}} Closed'
        }
        
        # Execute
        result = await template_service.create_template(template_data)
        
        # Assert
        assert result["success"] is True
        assert result["template_id"] == 1
        mock_repository.create_template.assert_called_once_with(template_data)
    
    @pytest.mark.asyncio
    async def test_render_template_success(self, template_service, mock_repository):
        """Test successful template rendering"""
        # Setup
        mock_repository.get_template_by_id.return_value = {
            'id': 1,
            'title_template': 'Trade {{ticker}} Closed',
            'message_template': 'Your {{ticker}} trade has been closed with P&L of {{pnl}}',
            'variables': '["ticker", "pnl"]'
        }
        mock_repository.render_template.return_value = {
            'template_id': 1,
            'rendered_title': 'Trade AAPL Closed',
            'rendered_message': 'Your AAPL trade has been closed with P&L of 150.50',
            'used_variables': {"ticker": "AAPL", "pnl": "150.50"}
        }
        
        # Execute
        result = await template_service.render_template(1, {"ticker": "AAPL", "pnl": "150.50"})
        
        # Assert
        assert result["rendered_title"] == "Trade AAPL Closed"
        assert result["rendered_message"] == "Your AAPL trade has been closed with P&L of 150.50"
        assert result["used_variables"]["ticker"] == "AAPL"
        mock_repository.render_template.assert_called_once_with(1, {"ticker": "AAPL", "pnl": "150.50"})


class TestNotificationSettingsService:
    """Test notification settings service operations"""
    
    @pytest.fixture
    def mock_repository(self):
        """Create mock settings repository"""
        return AsyncMock(spec=NotificationSettingsRepository)
    
    @pytest.fixture
    def settings_service(self, mock_repository):
        """Create settings service with mock repository"""
        return NotificationSettingsService(mock_repository)
    
    @pytest.mark.asyncio
    async def test_get_settings_success(self, settings_service, mock_repository):
        """Test successful settings retrieval"""
        # Setup
        mock_settings = {
            'user_id': 1,
            'enabled_channels': '["IN_APP", "EMAIL"]',
            'quiet_hours': '{"22:00": "08:00"}',
            'min_priority': 'LOW',
            'email_address': 'user@example.com'
        }
        mock_repository.get_settings.return_value = mock_settings
        
        # Execute
        result = await settings_service.get_settings(1)
        
        # Assert
        assert result["user_id"] == 1
        assert "EMAIL" in result["enabled_channels"]
        assert result["email_address"] == "user@example.com"
        mock_repository.get_settings.assert_called_once_with(1)
    
    @pytest.mark.asyncio
    async def test_get_settings_default(self, settings_service, mock_repository):
        """Test settings retrieval when user has no settings"""
        # Setup
        mock_repository.get_settings.return_value = None
        
        # Execute
        result = await settings_service.get_settings(1)
        
        # Assert
        assert result["user_id"] == 1
        assert result["enabled_channels"] == ["IN_APP"]  # Default
        assert result["min_priority"] == "LOW"  # Default
    
    @pytest.mark.asyncio
    async def test_update_settings_success(self, settings_service, mock_repository):
        """Test successful settings update"""
        # Setup
        mock_repository.get_settings.return_value = {'user_id': 1}
        mock_repository.update_settings.return_value = True
        
        # Execute
        from app.schemas.notifications import NotificationSettingsRequest
        settings_request = NotificationSettingsRequest(
            user_id=1,
            enabled_channels=["IN_APP", "SMS"],
            email_address="updated@example.com"
        )
        result = await settings_service.update_settings(1, settings_request)
        
        # Assert
        assert result["success"] is True
        mock_repository.update_settings.assert_called_once_with(1, settings_request)
    
    @pytest.mark.asyncio
    async def test_get_users_with_enabled_channel(self, settings_service, mock_repository):
        """Test getting users with enabled channel"""
        # Setup
        mock_repository.get_users_with_enabled_channel.return_value = [1, 2, 3]
        
        # Execute
        result = await settings_service.get_users_with_enabled_channel(NotificationChannel.EMAIL)
        
        # Assert
        assert result == [1, 2, 3]
        mock_repository.get_users_with_enabled_channel.assert_called_once_with(NotificationChannel.EMAIL)


class TestNotificationDigestService:
    """Test notification digest service operations"""
    
    @pytest.fixture
    def mock_repositories(self):
        """Create mock repositories"""
        return {
            'digest_repo': AsyncMock(spec=NotificationDigestRepository),
            'notification_repo': AsyncMock(spec=NotificationRepository)
        }
    
    @pytest.fixture
    def digest_service(self, mock_repositories):
        """Create digest service with mock repositories"""
        return NotificationDigestService(
            mock_repositories['digest_repo'],
            mock_repositories['notification_repo']
        )
    
    @pytest.mark.asyncio
    async def test_create_digest_success(self, digest_service, mock_repositories):
        """Test successful digest creation"""
        # Setup
        mock_repositories['notification_repo'].get_all_notifications.return_value = [
            {'id': 1, 'title': 'Notification 1'},
            {'id': 2, 'title': 'Notification 2'}
        ]
        mock_repositories['digest_repo'].create_digest.return_value = 1
        
        # Execute
        from app.schemas.notifications import NotificationDigestRequest
        request = NotificationDigestRequest(
            user_id=1,
            frequency="daily",
            max_items=10
        )
        result = await digest_service.create_digest(request)
        
        # Assert
        assert result["success"] is True
        assert result["notification_count"] == 2
        assert result["digest_id"] == 1


class TestNotificationDeliveryService:
    """Test notification delivery service operations"""
    
    @pytest.fixture
    def mock_repository(self):
        """Create mock delivery repository"""
        return AsyncMock(spec=NotificationDeliveryRepository)
    
    @pytest.fixture
    def delivery_service(self, mock_repository):
        """Create delivery service with mock repository"""
        return NotificationDeliveryService(mock_repository)
    
    @pytest.mark.asyncio
    async def test_send_notification_success(self, delivery_service, mock_repository):
        """Test successful notification sending"""
        # Setup
        mock_repository.send_notification.return_value = {
            "success": True,
            "delivery_id": "delivery_123",
            "status": "SENT"
        }
        
        # Execute
        from app.schemas.notifications import NotificationSendRequest
        request = NotificationSendRequest(
            template_id=1,
            type=NotificationType.TRADE_CLOSED,
            title="Test Notification",
            message="Test message",
            user_ids=[1, 2]
        )
        result = await delivery_service.send_notification(request)
        
        # Assert
        assert result["success"] is True
        assert result["delivery_id"] == "delivery_123"
        assert result["status"] == "SENT"
    
    @pytest.mark.asyncio
    async def test_send_bulk_notifications_success(self, delivery_service, mock_repository):
        """Test successful bulk notification sending"""
        # Setup
        mock_repository.send_bulk_notifications.return_value = {
            "success": True,
            "sent_count": 100,
            "status": "SENT"
        }
        
        # Execute
        from app.schemas.notifications import NotificationSendRequest
        request = NotificationSendRequest(
            template_id=1,
            type=NotificationType.MARKET_NEWS,
            title="Market Update",
            message="Market news update",
            user_ids=list(range(1, 101))
        )
        result = await delivery_service.send_bulk_notifications(request)
        
        # Assert
        assert result["success"] is True
        assert result["sent_count"] == 100
    
    @pytest.mark.asyncio
    async def test_get_delivery_stats_success(self, delivery_service, mock_repository):
        """Test getting delivery statistics"""
        # Setup
        mock_repository.get_delivery_stats.return_value = {
            "channel": "EMAIL",
            "total_sent": 1000,
            "success_rate": 95.5,
            "avg_delivery_time": 2.3
        }
        
        # Execute
        result = await delivery_service.get_delivery_stats(NotificationChannel.EMAIL)
        
        # Assert
        assert result["channel"] == "EMAIL"
        assert result["total_sent"] == 1000
        assert result["success_rate"] == 95.5
