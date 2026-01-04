import pytest
from unittest.mock import AsyncMock, patch
import os
from app.integrations.plaid import PlaidIntegration

@pytest.fixture
def plaid_integration():
    with patch.dict('os.environ', {
        'PLAID_CLIENT_ID': 'test_client',
        'PLAID_SECRET': 'test_secret',
        'PLAID_BASE_URL': 'https://sandbox.plaid.com'
    }):
        return PlaidIntegration()

@pytest.mark.asyncio
async def test_create_link_token(plaid_integration):
    # Mock the http request
    plaid_integration._make_request = AsyncMock(return_value={
        'link_token': 'link-sandbox-123',
        'expiration': '2025-01-01T00:00:00Z',
        'request_id': 'req_123'
    })
    
    result = await plaid_integration.create_link_token('user123')
    
    assert result['link_token'] == 'link-sandbox-123'
    plaid_integration._make_request.assert_called_once()
    args, kwargs = plaid_integration._make_request.call_args
    assert kwargs['json_data']['user']['client_user_id'] == 'user123'
    assert kwargs['json_data']['client_id'] == 'test_client'

@pytest.mark.asyncio
async def test_exchange_public_token(plaid_integration):
    plaid_integration._make_request = AsyncMock(return_value={
        'access_token': 'access-sandbox-123',
        'item_id': 'item_123'
    })
    
    result = await plaid_integration.exchange_public_token('public-sandbox-123')
    
    assert result['access_token'] == 'access-sandbox-123'
    assert result['item_id'] == 'item_123'
    
    plaid_integration._make_request.assert_called_once()
    args, kwargs = plaid_integration._make_request.call_args
    assert kwargs['json_data']['public_token'] == 'public-sandbox-123'
