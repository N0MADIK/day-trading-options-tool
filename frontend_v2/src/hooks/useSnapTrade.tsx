import { useState, useCallback } from 'react';
import { useAuth } from './useAuth';
import { toast } from 'sonner';
import { api } from '@/lib/api';

interface SnapTradeAccount {
  id: string;
  brokerage_authorization: string;
  portfolio_group: string | null;
  name: string;
  number: string;
  institution_name: string;
  balance: {
    total: { amount: number; currency: string };
  };
}

interface SnapTradeHolding {
  symbol: {
    id: string;
    symbol: string;
    description: string;
  };
  units: number;
  price: number;
  open_pnl: number;
  fractional_units: number;
  average_purchase_price: number | null;
}

export function useSnapTrade() {
  const { user } = useAuth();
  const [isLoading, setIsLoading] = useState(false);
  const [userSecret, setUserSecret] = useState<string | null>(null);

  const registerUser = useCallback(async () => {
    if (!user) {
      toast.error('Please sign in to connect accounts');
      return null;
    }

    setIsLoading(true);
    try {
      const response = await api.post<{ user_secret: string; user_id: string }>(
        '/integrations/snaptrade/register',
        { user_id: user.id }
      );

      setUserSecret(response.user_secret);

      // Store user secret in profile metadata for future use
      await api.put('/profiles/me', {
        metadata: { snaptrade_user_secret: response.user_secret }
      });

      return response.user_secret;
    } catch (error: any) {
      console.error('Error registering SnapTrade user:', error);
      // If user already exists, try to get existing secret
      if (error.message?.includes('already exists')) {
        toast.info('SnapTrade user already registered');
        return userSecret;
      }
      toast.error('Failed to register with SnapTrade: ' + error.message);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, [user, userSecret]);

  const getLoginLink = useCallback(async (secret?: string, broker?: string) => {
    if (!user) {
      toast.error('Please sign in to connect accounts');
      return null;
    }

    const userSecretToUse = secret || userSecret;
    if (!userSecretToUse) {
      toast.error('Please register with SnapTrade first');
      return null;
    }

    setIsLoading(true);
    try {
      const response = await api.post<{ authorization_url: string; brokerage_authorization_id: string }>(
        `/integrations/snaptrade/connect?user_secret=${encodeURIComponent(userSecretToUse)}`,
        {
          brokerage_id: broker || 'default',
          redirect_uri: window.location.origin + '/connections'
        }
      );

      return response.authorization_url;
    } catch (error: any) {
      console.error('Error getting login link:', error);
      toast.error('Failed to get connection link: ' + error.message);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, [user, userSecret]);

  const getAccounts = useCallback(async (secret?: string): Promise<SnapTradeAccount[] | null> => {
    if (!user) return null;

    const userSecretToUse = secret || userSecret;
    if (!userSecretToUse) return null;

    try {
      // Get accounts from connected-accounts endpoint
      // This returns the accounts synced via the backend
      const accounts = await api.get<any[]>('/connected-accounts');

      // Filter for SnapTrade accounts and map to expected format
      const snapTradeAccounts = accounts
        .filter(acc => acc.metadata?.integration_type === 'snaptrade')
        .map(acc => ({
          id: acc.metadata?.snaptrade_account_id || acc.id,
          brokerage_authorization: acc.metadata?.snaptrade_authorization_id || '',
          portfolio_group: null,
          name: acc.account_name || 'Account',
          number: acc.account_number_masked || '',
          institution_name: acc.institution_name || '',
          balance: {
            total: {
              amount: acc.balance || 0,
              currency: acc.currency || 'USD'
            }
          }
        }));

      return snapTradeAccounts;
    } catch (error: any) {
      console.error('Error fetching SnapTrade accounts:', error);
      return null;
    }
  }, [user, userSecret]);

  const getHoldings = useCallback(async (secret?: string, accountId?: string): Promise<SnapTradeHolding[] | null> => {
    if (!user) return null;

    const userSecretToUse = secret || userSecret;
    if (!userSecretToUse) return null;

    try {
      // Holdings are now stored in the backend database
      // We can fetch them via the holdings API endpoint
      const endpoint = accountId
        ? `/holdings?account_id=${encodeURIComponent(accountId)}`
        : '/holdings';
      const holdings = await api.get<any[]>(endpoint);

      return holdings.map(h => ({
        symbol: {
          id: h.symbol,
          symbol: h.symbol,
          description: h.name || h.symbol
        },
        units: h.quantity || 0,
        price: h.current_price || 0,
        open_pnl: h.unrealized_pnl || 0,
        fractional_units: 0,
        average_purchase_price: h.average_cost || null
      }));
    } catch (error: any) {
      console.error('Error fetching holdings:', error);
      return null;
    }
  }, [user, userSecret]);

  const getActivities = useCallback(async (secret?: string, accountId?: string) => {
    if (!user) return null;

    const userSecretToUse = secret || userSecret;
    if (!userSecretToUse) return null;

    try {
      // Activities/transactions are now stored in the backend database
      const endpoint = accountId
        ? `/transactions?account_id=${encodeURIComponent(accountId)}`
        : '/transactions';
      const transactions = await api.get<any[]>(endpoint);

      return transactions;
    } catch (error: any) {
      console.error('Error fetching activities:', error);
      return null;
    }
  }, [user, userSecret]);

  const listConnections = useCallback(async (secret?: string) => {
    if (!user) return null;

    const userSecretToUse = secret || userSecret;
    if (!userSecretToUse) return null;

    try {
      // Connections are now managed via integrations endpoint
      const integrations = await api.get<any[]>('/integrations');

      // Filter for SnapTrade integrations
      return integrations.filter(i => i.integration_type === 'snaptrade');
    } catch (error: any) {
      console.error('Error listing connections:', error);
      return null;
    }
  }, [user, userSecret]);

  const ensureIntegration = useCallback(async (secret?: string) => {
    const userSecretToUse = secret || userSecret;
    if (!user || !userSecretToUse) return null;

    try {
      const integrations = await api.get<any[]>('/integrations');
      const existing = integrations.find(i => i.integration_type === 'snaptrade');
      if (existing) return existing.id;

      // Create if not exists
      const newIntegration = await api.post<{ id: number }>('/integrations', {
        integration_type: 'snaptrade',
        credentials: { user_id: user.id, user_secret: userSecretToUse },
        is_sandbox: false
      });
      return newIntegration.id;
    } catch (error) {
      console.error('Error ensuring integration record:', error);
      return null;
    }
  }, [user, userSecret]);

  const syncIntegration = useCallback(async (integrationId: number | string) => {
    try {
      return await api.post(`/integrations/${integrationId}/sync/full`);
    } catch (error) {
      console.error('Sync failed:', error);
      throw error;
    }
  }, []);

  return {
    isLoading,
    userSecret,
    setUserSecret,
    registerUser,
    getLoginLink,
    getAccounts,
    getHoldings,
    getActivities,
    listConnections,
    ensureIntegration,
    syncIntegration,
  };
}
