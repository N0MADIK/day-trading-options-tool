"""Tests for SnapTrade integration using the official SDK."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.integrations.snaptrade import SnapTradeIntegration
from app.domain.errors import ExternalServiceError, ValidationError


@pytest.fixture
def mock_snaptrade_client():
    """Create a mock SnapTrade SDK client."""
    mock_client = MagicMock()
    mock_client.authentication = MagicMock()
    mock_client.account_information = MagicMock()
    mock_client.connections = MagicMock()
    mock_client.transactions_and_reporting = MagicMock()
    mock_client.reference_data = MagicMock()
    return mock_client


@pytest.fixture
def snaptrade_integration(mock_snaptrade_client):
    """Create a SnapTradeIntegration with mocked SDK client."""
    with patch.dict('os.environ', {
        'SNAPTRADE_CLIENT_ID': 'test_client',
        'SNAPTRADE_CONSUMER_KEY': 'test_key'
    }):
        with patch('app.integrations.snaptrade.SnapTrade', return_value=mock_snaptrade_client):
            integration = SnapTradeIntegration()
            integration.client = mock_snaptrade_client
            return integration


class TestValidateCredentials:
    """Tests for validate_credentials method."""

    @pytest.mark.asyncio
    async def test_validate_credentials_success(self, snaptrade_integration, mock_snaptrade_client):
        """Test successful credential validation."""
        mock_response = MagicMock()
        mock_response.body = [{'id': 'acc_123', 'name': 'Test Account'}]
        mock_snaptrade_client.account_information.list_user_accounts.return_value = mock_response
        
        credentials = {'user_secret': 'valid_secret', 'user_id': 'user_123'}
        
        with patch.object(snaptrade_integration, '_run_sdk', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = mock_response
            result = await snaptrade_integration.validate_credentials(credentials)
        
        assert result is True

    @pytest.mark.asyncio
    async def test_validate_credentials_missing_secret(self, snaptrade_integration):
        """Test validation fails when user_secret is missing."""
        credentials = {'user_id': 'user_123'}
        result = await snaptrade_integration.validate_credentials(credentials)
        assert result is False

    @pytest.mark.asyncio
    async def test_validate_credentials_missing_user_id(self, snaptrade_integration):
        """Test validation fails when user_id is missing."""
        credentials = {'user_secret': 'secret'}
        result = await snaptrade_integration.validate_credentials(credentials)
        assert result is False


class TestRegisterUser:
    """Tests for register_user method."""

    @pytest.mark.asyncio
    async def test_register_user_success(self, snaptrade_integration):
        """Test successful user registration."""
        mock_response = MagicMock()
        mock_response.body = {'userSecret': 'new_secret'}
        
        with patch.object(snaptrade_integration, '_run_sdk', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = mock_response
            result = await snaptrade_integration.register_user('user_123')
        
        assert result['user_secret'] == 'new_secret'
        assert result['user_id'] == 'user_123'

    @pytest.mark.asyncio
    async def test_register_user_api_error(self, snaptrade_integration):
        """Test registration failure raises ExternalServiceError."""
        from snaptrade_client import ApiException
        
        with patch.object(snaptrade_integration, '_run_sdk', new_callable=AsyncMock) as mock_run:
            mock_run.side_effect = ApiException(status=400, reason="Bad Request")
            
            with pytest.raises(ExternalServiceError):
                await snaptrade_integration.register_user('user_123')


class TestGetAccounts:
    """Tests for get_accounts method."""

    @pytest.mark.asyncio
    async def test_get_accounts_success(self, snaptrade_integration):
        """Test successful account retrieval."""
        mock_accounts = [
            {'id': 'acc_1', 'name': 'Robinhood Individual'},
            {'id': 'acc_2', 'name': 'Robinhood Margin'}
        ]
        mock_response = MagicMock()
        mock_response.body = mock_accounts
        
        credentials = {'user_secret': 'secret', 'user_id': 'user_123'}
        
        with patch.object(snaptrade_integration, '_run_sdk', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = mock_response
            result = await snaptrade_integration.get_accounts(credentials)
        
        assert result['accounts'] == mock_accounts
        assert len(result['accounts']) == 2


class TestGetHoldings:
    """Tests for get_holdings method."""

    @pytest.mark.asyncio
    async def test_get_holdings_all_accounts(self, snaptrade_integration):
        """Test fetching holdings for all accounts."""
        # The SDK returns a dict with holdings list and total_value
        mock_holdings_data = {
            'holdings': [
                {'symbol': 'AAPL', 'quantity': 10, 'market_value': 1500.00},
                {'symbol': 'GOOGL', 'quantity': 5, 'market_value': 700.00}
            ],
            'total_value': 2200.00
        }
        mock_response = MagicMock()
        mock_response.body = mock_holdings_data
        
        credentials = {'user_secret': 'secret', 'user_id': 'user_123'}
        
        with patch.object(snaptrade_integration, '_run_sdk', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = mock_response
            result = await snaptrade_integration.get_holdings(credentials)
        
        assert result['holdings'] == mock_holdings_data
        assert result['total_value'] == 2200.00

    @pytest.mark.asyncio
    async def test_get_holdings_specific_account(self, snaptrade_integration):
        """Test fetching holdings for a specific account."""
        mock_holdings = [{'symbol': 'TSLA', 'quantity': 3}]
        mock_response = MagicMock()
        mock_response.body = mock_holdings
        
        credentials = {'user_secret': 'secret', 'user_id': 'user_123'}
        
        with patch.object(snaptrade_integration, '_run_sdk', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = mock_response
            result = await snaptrade_integration.get_holdings(credentials, account_id='acc_123')
        
        assert result['holdings'] == mock_holdings


class TestGetTransactions:
    """Tests for get_transactions method."""

    @pytest.mark.asyncio
    async def test_get_transactions_success(self, snaptrade_integration):
        """Test successful transaction retrieval."""
        mock_transactions = [
            {'id': 'txn_1', 'type': 'BUY', 'symbol': 'AAPL', 'amount': 150.00},
            {'id': 'txn_2', 'type': 'SELL', 'symbol': 'GOOGL', 'amount': 200.00}
        ]
        mock_response = MagicMock()
        mock_response.body = mock_transactions
        
        credentials = {'user_secret': 'secret', 'user_id': 'user_123'}
        
        with patch.object(snaptrade_integration, '_run_sdk', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = mock_response
            result = await snaptrade_integration.get_transactions(credentials)
        
        assert result['activities'] == mock_transactions


class TestInitiateConnection:
    """Tests for initiate_connection method."""

    @pytest.mark.asyncio
    async def test_initiate_connection_success(self, snaptrade_integration):
        """Test successful connection initiation."""
        mock_response = MagicMock()
        mock_response.body = {'redirectURI': 'https://snaptrade.com/connect?token=abc123'}
        
        credentials = {'user_secret': 'secret', 'user_id': 'user_123'}
        
        with patch.object(snaptrade_integration, '_run_sdk', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = mock_response
            result = await snaptrade_integration.initiate_connection(
                credentials=credentials,
                brokerage_id='robinhood',
                redirect_uri='http://localhost:3000/callback'
            )
        
        assert result['redirect_uri'] == 'https://snaptrade.com/connect?token=abc123'

    @pytest.mark.asyncio
    async def test_initiate_connection_missing_credentials(self, snaptrade_integration):
        """Test connection fails with missing credentials."""
        credentials = {'user_secret': 'secret'}  # Missing user_id
        
        with pytest.raises(ValidationError):
            await snaptrade_integration.initiate_connection(
                credentials=credentials,
                brokerage_id='robinhood',
                redirect_uri='http://localhost:3000/callback'
            )


class TestBrokerSlugNormalization:
    """Tests for broker slug normalization."""

    def test_normalize_robinhood(self, snaptrade_integration):
        """Test Robinhood slug normalization."""
        assert snaptrade_integration._normalize_broker_slug('robinhood') == 'ROBINHOOD'

    def test_normalize_td_ameritrade(self, snaptrade_integration):
        """Test TD Ameritrade slug normalization."""
        assert snaptrade_integration._normalize_broker_slug('td-ameritrade') == 'TD'
        assert snaptrade_integration._normalize_broker_slug('tdameritrade') == 'TD'

    def test_normalize_unknown_broker(self, snaptrade_integration):
        """Test unknown broker gets uppercased."""
        assert snaptrade_integration._normalize_broker_slug('some-broker') == 'SOME_BROKER'
