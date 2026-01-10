import { useState, useCallback } from 'react';
import { supabase } from '@/integrations/supabase/client';
import { useAuth } from './useAuth';
import { toast } from 'sonner';

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
      const { data, error } = await supabase.functions.invoke('snaptrade-link', {
        body: { action: 'register_user', user_id: user.id },
      });

      if (error) throw error;
      if (data.error) throw new Error(data.error);

      setUserSecret(data.user_secret);
      
      // Store user secret in profile metadata for future use
      await supabase
        .from('profiles')
        .update({ 
          metadata: { snaptrade_user_secret: data.user_secret }
        } as any)
        .eq('user_id', user.id);

      return data.user_secret;
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
      const { data, error } = await supabase.functions.invoke('snaptrade-link', {
        body: { 
          action: 'get_login_link', 
          user_id: user.id,
          user_secret: userSecretToUse,
          ...(broker && { account_id: broker }),
        },
      });

      if (error) throw error;
      if (data.error) throw new Error(data.error);

      return data.redirect_uri;
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
      const { data, error } = await supabase.functions.invoke('snaptrade-link', {
        body: { 
          action: 'get_accounts', 
          user_id: user.id,
          user_secret: userSecretToUse,
        },
      });

      if (error) throw error;
      if (data.error) throw new Error(data.error);

      return data.accounts;
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
      const { data, error } = await supabase.functions.invoke('snaptrade-link', {
        body: { 
          action: 'get_holdings', 
          user_id: user.id,
          user_secret: userSecretToUse,
          ...(accountId && { account_id: accountId }),
        },
      });

      if (error) throw error;
      if (data.error) throw new Error(data.error);

      return data.holdings;
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
      const { data, error } = await supabase.functions.invoke('snaptrade-link', {
        body: { 
          action: 'get_activities', 
          user_id: user.id,
          user_secret: userSecretToUse,
          ...(accountId && { account_id: accountId }),
        },
      });

      if (error) throw error;
      if (data.error) throw new Error(data.error);

      return data.activities;
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
      const { data, error } = await supabase.functions.invoke('snaptrade-link', {
        body: { 
          action: 'list_connections', 
          user_id: user.id,
          user_secret: userSecretToUse,
        },
      });

      if (error) throw error;
      if (data.error) throw new Error(data.error);

      return data.connections;
    } catch (error: any) {
      console.error('Error listing connections:', error);
      return null;
    }
  }, [user, userSecret]);

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
  };
}
