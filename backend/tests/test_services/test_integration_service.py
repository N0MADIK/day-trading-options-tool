import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.integration_service import IntegrationService
from app.models.integrations import IntegrationType, IntegrationStatus, UserIntegration
from app.domain.errors import ValidationError, ExternalServiceError, NotFoundError

@pytest.fixture
def mock_session():
    session = AsyncMock()
    # Mock execute result
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_result.scalars.return_value.all.return_value = []
    session.execute.return_value = mock_result
    return session

@pytest.fixture
def integration_service(mock_session):
    return IntegrationService(mock_session)

@pytest.mark.asyncio
async def test_create_integration_success(integration_service, mock_session):
    # Mock encryption
    with patch('app.core.security.credential_encryption.encrypt_credentials', return_value='encrypted_data'):
        # Mock validation
        with patch('app.integrations.alpaca.AlpacaIntegration.validate_credentials', new_callable=AsyncMock) as mock_validate:
            mock_validate.return_value = True
            
            try:
                # Use Alpaca for test
                credentials = {'api_key': 'key', 'secret_key': 'secret'}
                result = await integration_service.create_integration(
                    user_id='user_123',
                    integration_type=IntegrationType.ALPACA,
                    credentials=credentials
                )
                
                # Assert encryption called
                # Assert session add/commit called
                mock_session.add.assert_called_once()
                mock_session.commit.assert_called_once()
            except Exception as e:
                print(f"TEST FAILED WITH ERROR: {type(e).__name__}: {e}")
                import traceback
                traceback.print_exc()
                raise e
            
@pytest.mark.asyncio
async def test_create_integration_invalid_credentials(integration_service, mock_session):
    with patch('app.integrations.alpaca.AlpacaIntegration.validate_credentials', new_callable=AsyncMock) as mock_validate:
        mock_validate.return_value = False
        
        credentials = {'api_key': 'key', 'secret_key': 'secret'}
        
        with pytest.raises(ValidationError):
            await integration_service.create_integration(
                user_id='user_123',
                integration_type=IntegrationType.ALPACA,
                credentials=credentials
            )

@pytest.mark.asyncio
async def test_delete_integration_success(integration_service, mock_session):
    mock_integration = MagicMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_integration
    mock_session.execute.return_value = mock_result
    
    result = await integration_service.delete_integration('user_123', 1)
    
    assert result['deleted'] is True
    mock_session.delete.assert_called_once_with(mock_integration)
    mock_session.commit.assert_called_once()

@pytest.mark.asyncio
async def test_delete_integration_not_found(integration_service, mock_session):
    # Mock session returning None
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result
    
    with pytest.raises(NotFoundError):
        await integration_service.delete_integration('user_123', 999)

@pytest.mark.asyncio
async def test_test_connection_success(integration_service, mock_session):
    mock_integration = MagicMock()
    mock_integration.integration_type = IntegrationType.ALPACA
    mock_integration.encrypted_credentials = "enc_creds"
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_integration
    mock_session.execute.return_value = mock_result
    
    with patch('app.core.security.credential_encryption.decrypt_credentials', return_value={'api_key': 'k'}), \
         patch('app.integrations.alpaca.AlpacaIntegration.test_connection', new_callable=AsyncMock) as mock_test:
        
        mock_test.return_value = {"connected": True}
        
        result = await integration_service.test_connection('user_123', 1)
        
        # Should verify status update
        assert mock_integration.status == IntegrationStatus.ACTIVE
        mock_session.commit.assert_called()

