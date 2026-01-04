import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.integrations.snaptrade import SnapTradeIntegration
from app.domain.errors import UnauthorizedError

@pytest.fixture
def snaptrade_integration():
    with patch.dict('os.environ', {
        'SNAPTRADE_CLIENT_ID': 'test_client',
        'SNAPTRADE_CONSUMER_KEY': 'test_key'
    }):
        return SnapTradeIntegration()

@pytest.mark.asyncio
async def test_validate_credentials(snaptrade_integration):
    snaptrade_integration.test_connection = AsyncMock(return_value=True)
    credentials = {'user_secret': 'valid_secret'}
    
    result = await snaptrade_integration.validate_credentials(credentials)
    
    assert result is True
    snaptrade_integration.test_connection.assert_called_once_with(credentials)

@pytest.mark.asyncio
async def test_validate_credentials_no_secret(snaptrade_integration):
    credentials = {}
    
    # Should raise ValidationError but the method just raises it and doesn't catch it
    # in usage, so let's check it propagates or handle it
    from app.domain.errors import ValidationError
    with pytest.raises(ValidationError):
        await snaptrade_integration.validate_credentials(credentials)

@pytest.mark.asyncio
async def test_register_user(snaptrade_integration):
    mock_response = {'userSecret': 'new_secret', 'userId': 'user_123'}
    snaptrade_integration._make_request = AsyncMock(return_value=mock_response)
    
    result = await snaptrade_integration.register_user('user_123')
    
    assert result['user_secret'] == 'new_secret'
    assert result['user_id'] == 'user_123'
    snaptrade_integration._make_request.assert_called_once()

@pytest.mark.asyncio
async def test_get_holdings(snaptrade_integration):
    mock_response = {
        'holdings': [{'symbol': 'AAPL', 'quantity': 10}],
        'totalValue': 1500.00
    }
    snaptrade_integration._make_request = AsyncMock(return_value=mock_response)
    credentials = {'user_secret': 'secret'}
    
    result = await snaptrade_integration.get_holdings(credentials)
    
    assert result['holdings'] == mock_response['holdings']
    assert result['total_value'] == 1500.00
    snaptrade_integration._make_request.assert_called_once()

@pytest.mark.asyncio
async def test_signature_generation(snaptrade_integration):
    # Test that signature generation produces consistent output for same input
    user_secret = "secret"
    timestamp = "1234567890"
    path = "/test"
    
    sig1 = snaptrade_integration._generate_signature(user_secret, timestamp, path)
    sig2 = snaptrade_integration._generate_signature(user_secret, timestamp, path)
    
    assert sig1 == sig2
    assert len(sig1) > 0

