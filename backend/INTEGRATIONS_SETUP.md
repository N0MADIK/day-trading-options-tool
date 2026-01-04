# External Service Integrations Setup

This document describes the setup and usage of external service integrations for Plaid, Alpaca, and SnapTrade.

## Overview

The system now supports connecting to three major financial service providers:

1. **Plaid** - Banking and financial account aggregation
2. **Alpaca** - Stock and crypto trading API
3. **SnapTrade** - Multi-brokerage account connections

## Environment Variables

Set the following environment variables for the integrations to work:

```bash
# Credential Encryption (Required)
CREDENTIAL_ENCRYPTION_KEY=your-encryption-key-here

# Plaid Integration
PLAID_CLIENT_ID=your-plaid-client-id
PLAID_SECRET=your-plaid-secret
PLAID_BASE_URL=https://development.plaid.com  # or https://api.plaid.com for production

# Alpaca Integration
ALPACA_API_KEY=your-alpaca-api-key
ALPACA_SECRET_KEY=your-alpaca-secret-key

# SnapTrade Integration
SNAPTRADE_CLIENT_ID=your-snaptrade-client-id
SNAPTRADE_CONSUMER_KEY=your-snaptrade-consumer-key
```

## API Endpoints

### General Integration Management

- `GET /api/v1/integrations/` - Get all user integrations
- `POST /api/v1/integrations/` - Create new integration
- `PUT /api/v1/integrations/{integration_id}/credentials` - Update credentials
- `DELETE /api/v1/integrations/{integration_id}` - Delete integration
- `POST /api/v1/integrations/{integration_id}/test` - Test connection
- `POST /api/v1/integrations/{integration_id}/sync` - Sync accounts
- `GET /api/v1/integrations/{integration_id}/accounts` - Get connected accounts

### Plaid-Specific Endpoints

- `POST /api/v1/integrations/plaid/link-token` - Create Plaid Link token
- `POST /api/v1/integrations/plaid/exchange-token` - Exchange public token

### SnapTrade-Specific Endpoints

- `POST /api/v1/integrations/snaptrade/register` - Register SnapTrade user
- `GET /api/v1/integrations/snaptrade/brokerages` - Get supported brokerages
- `POST /api/v1/integrations/snaptrade/connect` - Initiate brokerage connection

## Usage Examples

### Creating a Plaid Integration

```bash
# First, create a Link token
curl -X POST "http://localhost:8000/api/v1/integrations/plaid/link-token" \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user123"}'

# Use the Link token in Plaid Link frontend, then exchange the public token
curl -X POST "http://localhost:8000/api/v1/integrations/plaid/exchange-token" \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{"public_token": "public-sandbox-token"}'

# Create the integration with the access token
curl -X POST "http://localhost:8000/api/v1/integrations/" \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{
    "integration_type": "plaid",
    "credentials": {
      "access_token": "access-sandbox-token"
    },
    "is_sandbox": true
  }'
```

### Creating an Alpaca Integration

```bash
curl -X POST "http://localhost:8000/api/v1/integrations/" \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{
    "integration_type": "alpaca",
    "credentials": {
      "api_key": "your-alpaca-api-key",
      "secret_key": "your-alpaca-secret-key",
      "is_paper_trading": true
    },
    "is_sandbox": true
  }'
```

### Creating a SnapTrade Integration

```bash
# First, register a user
curl -X POST "http://localhost:8000/api/v1/integrations/snaptrade/register" \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user123"}'

# Then create the integration with the user secret
curl -X POST "http://localhost:8000/api/v1/integrations/" \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{
    "integration_type": "snaptrade",
    "credentials": {
      "user_secret": "user-secret-from-registration"
    },
    "is_sandbox": true
  }'
```

## Database Schema

The integrations use two main database tables:

### user_integrations
- Stores encrypted credentials for each integration
- Tracks integration status and metadata
- Links to connected accounts

### connected_accounts
- Stores individual account information from each service
- Tracks sync status and account details
- Links back to the parent integration

## Security Features

1. **Credential Encryption**: All user credentials are encrypted using Fernet symmetric encryption
2. **Secure Storage**: Encrypted credentials are stored in the database
3. **API Key Protection**: Service API keys are stored in environment variables
4. **Sandbox Mode**: Integrations support sandbox/development environments

## Error Handling

The system includes comprehensive error handling:

- `ValidationError` - Invalid input data
- `NotFoundError` - Resource not found
- `ExternalServiceError` - Service API errors
- `UnauthorizedError` - Authentication failures

## Next Steps

1. **Authentication System**: Replace the temporary authentication with a proper JWT-based system
2. **Webhook Support**: Add webhook endpoints for real-time data updates
3. **Rate Limiting**: Implement rate limiting for external API calls
4. **Monitoring**: Add logging and monitoring for integration health
5. **Testing**: Add comprehensive unit and integration tests

## Troubleshooting

### Common Issues

1. **Encryption Key Missing**: Set `CREDENTIAL_ENCRYPTION_KEY` environment variable
2. **API Keys Invalid**: Verify all service API keys are correct
3. **Connection Failures**: Check network connectivity and service status
4. **Credential Validation**: Ensure credentials are in the correct format

### Debug Mode

Enable debug mode by setting `DEBUG=true` in your environment to get more detailed error messages.
