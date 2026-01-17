"""Service layer for managing external integrations"""
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.models.integrations import UserIntegration, ConnectedAccount, IntegrationType, IntegrationStatus
from app.models.personal_finance import (
    Institution, Connection, Account as PFAccount, 
    Security, Holding, Transaction as PFTransaction
)
from app.integrations import PlaidIntegration, AlpacaIntegration, SnapTradeIntegration
from app.core.security import credential_encryption
from app.domain.errors import NotFoundError, ValidationError, ExternalServiceError


class IntegrationService:
    """Service for managing external service integrations"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.integrations = {
            IntegrationType.PLAID: PlaidIntegration,
            IntegrationType.ALPACA: AlpacaIntegration,
            IntegrationType.SNAPTRADE: SnapTradeIntegration
        }
    
    async def create_integration(
        self,
        user_id: str,
        integration_type: IntegrationType,
        credentials: Dict[str, Any],
        is_sandbox: bool = True
    ) -> Dict[str, Any]:
        """Create a new integration for a user"""
        
        # Check if integration already exists
        existing = await self.session.execute(
            select(UserIntegration).where(
                and_(
                    UserIntegration.user_id == user_id,
                    UserIntegration.integration_type == integration_type
                )
            )
        )
        if existing.scalar_one_or_none():
            raise ValidationError(f"Integration of type {integration_type.value} already exists for user")
        
        # Validate credentials with the service
        integration_class = self.integrations.get(integration_type)
        if not integration_class:
            raise ValidationError(f"Unsupported integration type: {integration_type}")
        
        async with integration_class() as integration:
            try:
                is_valid = await integration.validate_credentials(credentials)
                if not is_valid:
                    raise ValidationError("Invalid credentials provided")
            except ValidationError:
                raise
            except Exception as e:
                raise ExternalServiceError(f"Failed to validate credentials: {str(e)}")
        
        # Encrypt and store credentials
        encrypted_creds = credential_encryption.encrypt_credentials(credentials)
        
        integration = UserIntegration(
            user_id=user_id,
            integration_type=integration_type,
            encrypted_credentials=encrypted_creds,
            is_sandbox=is_sandbox,
            status=IntegrationStatus.ACTIVE
        )
        
        self.session.add(integration)
        await self.session.commit()
        await self.session.refresh(integration)
        
        return {
            'id': integration.id,
            'integration_type': integration.integration_type.value,
            'status': integration.status.value,
            'is_sandbox': integration.is_sandbox,
            'created_at': integration.created_at.isoformat() if integration.created_at else None
        }
    
    async def update_credentials(
        self,
        user_id: str,
        integration_id: int,
        credentials: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update credentials for an existing integration"""
        
        result = await self.session.execute(
            select(UserIntegration).where(
                and_(
                    UserIntegration.id == integration_id,
                    UserIntegration.user_id == user_id
                )
            )
        )
        integration = result.scalar_one_or_none()
        
        if not integration:
            raise NotFoundError("Integration not found")
        
        # Validate new credentials
        integration_class = self.integrations.get(integration.integration_type)
        async with integration_class() as integration_instance:
            try:
                is_valid = await integration_instance.validate_credentials(credentials)
                if not is_valid:
                    raise ValidationError("Invalid credentials provided")
            except Exception as e:
                raise ExternalServiceError(f"Failed to validate credentials: {str(e)}")
        
        # Update encrypted credentials
        integration.encrypted_credentials = credential_encryption.encrypt_credentials(credentials)
        integration.status = IntegrationStatus.ACTIVE
        integration.last_error = None
        
        await self.session.commit()
        await self.session.refresh(integration)
        
        return {
            'id': integration.id,
            'status': integration.status.value,
            'updated_at': integration.updated_at.isoformat() if integration.updated_at else None
        }
    
    async def delete_integration(self, user_id: str, integration_id: int) -> Dict[str, Any]:
        """Delete an integration"""
        
        result = await self.session.execute(
            select(UserIntegration).where(
                and_(
                    UserIntegration.id == integration_id,
                    UserIntegration.user_id == user_id
                )
            )
        )
        integration = result.scalar_one_or_none()
        
        if not integration:
            raise NotFoundError("Integration not found")
        
        await self.session.delete(integration)
        await self.session.commit()
        
        return {'deleted': True, 'integration_id': integration_id}
    
    async def get_user_integrations(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all integrations for a user"""
        
        result = await self.session.execute(
            select(UserIntegration).where(UserIntegration.user_id == user_id)
        )
        integrations = result.scalars().all()
        
        return [
            {
                'id': integration.id,
                'integration_type': integration.integration_type.value,
                'status': integration.status.value,
                'is_sandbox': integration.is_sandbox,
                'last_sync_at': integration.last_sync_at.isoformat() if integration.last_sync_at else None,
                'created_at': integration.created_at.isoformat() if integration.created_at else None,
                'connected_accounts': len(integration.connected_accounts) if integration.connected_accounts else 0
            }
            for integration in integrations
        ]
    
    async def test_connection(self, user_id: str, integration_id: int) -> Dict[str, Any]:
        """Test an integration connection"""
        
        result = await self.session.execute(
            select(UserIntegration).where(
                and_(
                    UserIntegration.id == integration_id,
                    UserIntegration.user_id == user_id
                )
            )
        )
        integration = result.scalar_one_or_none()
        
        if not integration:
            raise NotFoundError("Integration not found")
        
        # Decrypt credentials
        credentials = credential_encryption.decrypt_credentials(integration.encrypted_credentials)
        
        # Test connection
        integration_class = self.integrations.get(integration.integration_type)
        async with integration_class() as integration_instance:
            try:
                result = await integration_instance.test_connection(credentials)
                
                # Update status
                integration.status = IntegrationStatus.ACTIVE
                integration.last_error = None
                await self.session.commit()
                
                return result
                
            except Exception as e:
                # Update status on error
                integration.status = IntegrationStatus.ERROR
                integration.last_error = str(e)
                await self.session.commit()
                
                raise ExternalServiceError(f"Connection test failed: {str(e)}")
    
    async def sync_accounts(self, user_id: str, integration_id: int) -> Dict[str, Any]:
        """Sync accounts from an integration"""
        
        result = await self.session.execute(
            select(UserIntegration).where(
                and_(
                    UserIntegration.id == integration_id,
                    UserIntegration.user_id == user_id
                )
            )
        )
        integration = result.scalar_one_or_none()
        
        if not integration:
            raise NotFoundError("Integration not found")
        
        # Decrypt credentials
        credentials = credential_encryption.decrypt_credentials(integration.encrypted_credentials)
        
        # Get accounts from service
        integration_class = self.integrations.get(integration.integration_type)
        async with integration_class() as integration_instance:
            try:
                accounts_data = await integration_instance.get_accounts(credentials)
                
                # Process accounts based on integration type
                if integration.integration_type == IntegrationType.PLAID:
                    accounts = accounts_data.get('accounts', [])
                elif integration.integration_type == IntegrationType.ALPACA:
                    # Alpaca returns a single account
                    account = accounts_data.get('account', {})
                    accounts = [account] if account else []
                else:  # SnapTrade
                    accounts = accounts_data.get('accounts', [])
                
                # Update or create connected accounts
                synced_accounts = []
                for account in accounts:
                    # Check if account exists
                    existing = await self.session.execute(
                        select(ConnectedAccount).where(
                            and_(
                                ConnectedAccount.integration_id == integration.id,
                                ConnectedAccount.external_account_id == str(account.get('account_id') or account.get('id') or account.get('account_number'))
                            )
                        )
                    )
                    connected_account = existing.scalar_one_or_none()
                    
                    if not connected_account:
                        connected_account = ConnectedAccount(
                            integration_id=integration.id,
                            external_account_id=str(account.get('account_id') or account.get('id') or account.get('account_number')),
                        )
                        self.session.add(connected_account)
                    
                    # Update account details
                    connected_account.account_name = account.get('name') or account.get('official_name') or 'Trading Account'
                    connected_account.account_type = account.get('type') or account.get('account_type') or 'investment'
                    connected_account.account_subtype = account.get('subtype')
                    connected_account.institution_name = account.get('institution_name')
                    connected_account.last_successful_sync = datetime.utcnow()
                    
                    synced_accounts.append({
                        'external_id': connected_account.external_account_id,
                        'name': connected_account.account_name,
                        'type': connected_account.account_type
                    })
                
                # Update integration sync time
                integration.last_sync_at = datetime.utcnow()
                integration.status = IntegrationStatus.ACTIVE
                
                await self.session.commit()
                
                return {
                    'synced_accounts': synced_accounts,
                    'total': len(synced_accounts)
                }
                
            except Exception as e:
                integration.status = IntegrationStatus.ERROR
                integration.last_error = str(e)
                await self.session.commit()
                
                raise ExternalServiceError(f"Failed to sync accounts: {str(e)}")
    
    async def get_integration_accounts(self, user_id: str, integration_id: int) -> List[Dict[str, Any]]:
        """Get all connected accounts for an integration"""
        
        result = await self.session.execute(
            select(UserIntegration).where(
                and_(
                    UserIntegration.id == integration_id,
                    UserIntegration.user_id == user_id
                )
            )
        )
        integration = result.scalar_one_or_none()
        
        if not integration:
            raise NotFoundError("Integration not found")
        
        accounts = []
        for account in integration.connected_accounts:
            accounts.append({
                'id': account.id,
                'external_account_id': account.external_account_id,
                'account_name': account.account_name,
                'account_type': account.account_type,
                'account_subtype': account.account_subtype,
                'institution_name': account.institution_name,
                'is_active': account.is_active,
                'sync_enabled': account.sync_enabled,
                'last_successful_sync': account.last_successful_sync.isoformat() if account.last_successful_sync else None
            })
        
        return accounts

    async def _get_or_create_security(self, symbol: str, name: Optional[str] = None, security_type: str = 'equity') -> Security:
        """Get existing security or create a new one."""
        result = await self.session.execute(
            select(Security).where(Security.symbol == symbol)
        )
        security = result.scalar_one_or_none()
        
        if not security:
            security = Security(
                symbol=symbol,
                name=name or symbol,
                security_type=security_type
            )
            self.session.add(security)
            await self.session.flush()  # Get the ID without committing
        
        return security

    async def _get_pf_account_id(self, integration_id: int, external_account_id: str) -> Optional[int]:
        """Get personal_finance Account ID from integration's connected account."""
        # First get the connected account
        result = await self.session.execute(
            select(ConnectedAccount).where(
                and_(
                    ConnectedAccount.integration_id == integration_id,
                    ConnectedAccount.external_account_id == external_account_id
                )
            )
        )
        connected_account = result.scalar_one_or_none()
        
        if not connected_account:
            return None
        
        # Now find the corresponding personal_finance Account
        pf_result = await self.session.execute(
            select(PFAccount).where(PFAccount.external_account_id == external_account_id)
        )
        pf_account = pf_result.scalar_one_or_none()
        
        return pf_account.id if pf_account else None

    async def sync_holdings(self, user_id: str, integration_id: int) -> Dict[str, Any]:
        """Sync holdings from an integration to personal_finance models."""
        
        result = await self.session.execute(
            select(UserIntegration).where(
                and_(
                    UserIntegration.id == integration_id,
                    UserIntegration.user_id == user_id
                )
            )
        )
        integration = result.scalar_one_or_none()
        
        if not integration:
            raise NotFoundError("Integration not found")
        
        if integration.integration_type != IntegrationType.SNAPTRADE:
            raise ValidationError("Holdings sync is only supported for SnapTrade integrations")
        
        # Decrypt credentials
        credentials = credential_encryption.decrypt_credentials(integration.encrypted_credentials)
        
        async with SnapTradeIntegration() as snaptrade:
            try:
                holdings_data = await snaptrade.get_holdings(credentials)
                holdings_list = holdings_data.get('holdings', [])
                
                synced_holdings = []
                
                for holding in holdings_list:
                    symbol = holding.get('symbol') or holding.get('ticker')
                    if not symbol:
                        continue
                    
                    # Get or create the security
                    security = await self._get_or_create_security(
                        symbol=symbol,
                        name=holding.get('name'),
                        security_type=holding.get('security_type', 'equity')
                    )
                    
                    # Get the personal_finance account ID
                    account_id = holding.get('account_id') or holding.get('accountId')
                    pf_account_id = await self._get_pf_account_id(integration_id, str(account_id)) if account_id else None
                    
                    if not pf_account_id:
                        # Skip if we can't map to a personal_finance account
                        continue
                    
                    # Check if holding exists
                    existing = await self.session.execute(
                        select(Holding).where(
                            and_(
                                Holding.account_id == pf_account_id,
                                Holding.security_id == security.id
                            )
                        )
                    )
                    pf_holding = existing.scalar_one_or_none()
                    
                    quantity = float(holding.get('quantity', 0) or holding.get('units', 0))
                    market_value = float(holding.get('market_value', 0) or holding.get('marketValue', 0))
                    cost_basis = float(holding.get('cost_basis', 0) or holding.get('averagePurchasePrice', 0) * quantity)
                    
                    if not pf_holding:
                        pf_holding = Holding(
                            account_id=pf_account_id,
                            security_id=security.id,
                            quantity=quantity,
                            cost_basis=cost_basis,
                            market_value=market_value,
                            as_of_date=datetime.utcnow()
                        )
                        self.session.add(pf_holding)
                    else:
                        pf_holding.quantity = quantity
                        pf_holding.cost_basis = cost_basis
                        pf_holding.market_value = market_value
                        pf_holding.as_of_date = datetime.utcnow()
                    
                    synced_holdings.append({
                        'symbol': symbol,
                        'quantity': quantity,
                        'market_value': market_value
                    })
                
                integration.last_sync_at = datetime.utcnow()
                await self.session.commit()
                
                return {
                    'synced_holdings': synced_holdings,
                    'total': len(synced_holdings)
                }
                
            except Exception as e:
                integration.status = IntegrationStatus.ERROR
                integration.last_error = str(e)
                await self.session.commit()
                raise ExternalServiceError(f"Failed to sync holdings: {str(e)}")

    async def sync_transactions(
        self, 
        user_id: str, 
        integration_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Sync transactions from an integration to personal_finance models."""
        
        result = await self.session.execute(
            select(UserIntegration).where(
                and_(
                    UserIntegration.id == integration_id,
                    UserIntegration.user_id == user_id
                )
            )
        )
        integration = result.scalar_one_or_none()
        
        if not integration:
            raise NotFoundError("Integration not found")
        
        if integration.integration_type != IntegrationType.SNAPTRADE:
            raise ValidationError("Transaction sync is only supported for SnapTrade integrations")
        
        # Decrypt credentials
        credentials = credential_encryption.decrypt_credentials(integration.encrypted_credentials)
        
        async with SnapTradeIntegration() as snaptrade:
            try:
                txn_data = await snaptrade.get_transactions(
                    credentials,
                    start_date=start_date,
                    end_date=end_date
                )
                activities = txn_data.get('activities', [])
                
                synced_transactions = []
                
                for activity in activities:
                    external_txn_id = activity.get('id') or activity.get('transactionId')
                    
                    # Check if transaction already exists
                    existing = await self.session.execute(
                        select(PFTransaction).where(
                            PFTransaction.external_transaction_id == str(external_txn_id)
                        )
                    )
                    if existing.scalar_one_or_none():
                        continue  # Skip duplicates
                    
                    # Get the personal_finance account ID
                    account_id = activity.get('account_id') or activity.get('accountId')
                    pf_account_id = await self._get_pf_account_id(integration_id, str(account_id)) if account_id else None
                    
                    if not pf_account_id:
                        continue
                    
                    # Get or create security if applicable
                    symbol = activity.get('symbol') or activity.get('ticker')
                    security_id = None
                    if symbol:
                        security = await self._get_or_create_security(symbol)
                        security_id = security.id
                    
                    # Parse transaction date
                    txn_date_str = activity.get('trade_date') or activity.get('settlement_date') or activity.get('date')
                    if isinstance(txn_date_str, str):
                        try:
                            txn_date = datetime.fromisoformat(txn_date_str.replace('Z', '+00:00'))
                        except ValueError:
                            txn_date = datetime.utcnow()
                    else:
                        txn_date = txn_date_str or datetime.utcnow()
                    
                    pf_transaction = PFTransaction(
                        account_id=pf_account_id,
                        security_id=security_id,
                        external_transaction_id=str(external_txn_id),
                        transaction_type=activity.get('type', 'UNKNOWN'),
                        quantity=float(activity.get('quantity', 0) or activity.get('units', 0) or 0),
                        amount=float(activity.get('amount', 0) or activity.get('price', 0) or 0),
                        price=float(activity.get('price', 0) or 0),
                        fees=float(activity.get('fee', 0) or activity.get('commission', 0) or 0),
                        transaction_date=txn_date,
                        description=activity.get('description', ''),
                        raw_data=activity
                    )
                    self.session.add(pf_transaction)
                    
                    synced_transactions.append({
                        'external_id': external_txn_id,
                        'type': activity.get('type'),
                        'symbol': symbol,
                        'amount': pf_transaction.amount
                    })
                
                integration.last_sync_at = datetime.utcnow()
                await self.session.commit()
                
                return {
                    'synced_transactions': synced_transactions,
                    'total': len(synced_transactions)
                }
                
            except Exception as e:
                integration.status = IntegrationStatus.ERROR
                integration.last_error = str(e)
                await self.session.commit()
                raise ExternalServiceError(f"Failed to sync transactions: {str(e)}")

    async def full_sync(self, user_id: str, integration_id: int) -> Dict[str, Any]:
        """Perform a full sync: accounts, holdings, and transactions."""
        accounts_result = await self.sync_accounts(user_id, integration_id)
        holdings_result = await self.sync_holdings(user_id, integration_id)
        transactions_result = await self.sync_transactions(user_id, integration_id)
        
        return {
            'accounts': accounts_result,
            'holdings': holdings_result,
            'transactions': transactions_result
        }
