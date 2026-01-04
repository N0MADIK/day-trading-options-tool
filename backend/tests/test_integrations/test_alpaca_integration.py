import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.integrations.alpaca import AlpacaIntegration
from datetime import datetime

@pytest.fixture
def alpaca_integration():
    with patch.dict('os.environ', {
        'ALPACA_API_KEY': 'test_key',
        'ALPACA_SECRET_KEY': 'test_secret',
        'ALPACA_BASE_URL': 'https://paper-api.alpaca.markets'
    }):
        return AlpacaIntegration()

@pytest.mark.asyncio
async def test_validate_credentials_success(alpaca_integration):
    alpaca_integration.test_connection = AsyncMock(return_value=True)
    credentials = {'api_key': 'key', 'secret_key': 'secret'}
    
    result = await alpaca_integration.validate_credentials(credentials)
    
    assert result is True
    alpaca_integration.test_connection.assert_called_once_with(credentials)

@pytest.mark.asyncio
async def test_validate_credentials_failure(alpaca_integration):
    alpaca_integration.test_connection = AsyncMock(side_effect=Exception("Connection failed"))
    credentials = {'api_key': 'key', 'secret_key': 'secret'}
    
    result = await alpaca_integration.validate_credentials(credentials)
    
    assert result is False

@pytest.mark.asyncio
async def test_get_accounts(alpaca_integration):
    mock_response = {
        'id': 'account_123',
        'status': 'ACTIVE',
        'currency': 'USD',
        'buying_power': '100000.00'
    }
    alpaca_integration._make_request = AsyncMock(return_value=mock_response)
    credentials = {'api_key': 'key', 'secret_key': 'secret', 'is_paper_trading': True}
    
    result = await alpaca_integration.get_accounts(credentials)
    
    assert result['account'] == mock_response
    assert result['is_paper_trading'] is True
    alpaca_integration._make_request.assert_called_once()

@pytest.mark.asyncio
async def test_get_positions(alpaca_integration):
    mock_positions = [
        {'symbol': 'AAPL', 'qty': '10', 'market_value': '1500.00'}
    ]
    alpaca_integration._make_request = AsyncMock(return_value=mock_positions)
    credentials = {'api_key': 'key', 'secret_key': 'secret'}
    
    result = await alpaca_integration.get_positions(credentials)
    
    assert result['positions'] == mock_positions

@pytest.mark.asyncio
async def test_place_order(alpaca_integration):
    mock_order_response = {'id': 'order_123', 'status': 'new'}
    alpaca_integration._make_request = AsyncMock(return_value=mock_order_response)
    credentials = {'api_key': 'key', 'secret_key': 'secret'}
    order_data = {
        'symbol': 'AAPL',
        'qty': '1',
        'side': 'buy',
        'type': 'market',
        'time_in_force': 'day'
    }
    
    result = await alpaca_integration.place_order(credentials, order_data)
    
    assert result == mock_order_response
    alpaca_integration._make_request.assert_called_once()
    args, kwargs = alpaca_integration._make_request.call_args
    assert kwargs['json_data'] == order_data
