import { useState, useCallback } from 'react';
import { usePlaidLink, PlaidLinkOnSuccess, PlaidLinkOptions } from 'react-plaid-link';
import { supabase } from '@/integrations/supabase/client';
import { useAuth } from './useAuth';
import { toast } from 'sonner';

interface PlaidAccount {
  account_id: string;
  name: string;
  official_name: string | null;
  type: string;
  subtype: string;
  mask: string | null;
  balances: {
    available: number | null;
    current: number | null;
    limit: number | null;
    iso_currency_code: string | null;
  };
}

interface PlaidHolding {
  account_id: string;
  security_id: string;
  quantity: number;
  institution_value: number;
  cost_basis: number | null;
}

interface PlaidSecurity {
  security_id: string;
  name: string;
  ticker_symbol: string | null;
  type: string;
  close_price: number | null;
}

interface PlaidInstitution {
  institution_id: string;
  name: string;
}

export function usePlaid() {
  const { user } = useAuth();
  const [isLoading, setIsLoading] = useState(false);
  const [linkToken, setLinkToken] = useState<string | null>(null);
  const [pendingInstitution, setPendingInstitution] = useState<{ id: string; name: string; type: string } | null>(null);

  const createLinkToken = useCallback(async () => {
    if (!user) {
      toast.error('Please sign in to connect accounts');
      return null;
    }

    setIsLoading(true);
    try {
      const { data, error } = await supabase.functions.invoke('plaid-link', {
        body: { action: 'create_link_token', user_id: user.id },
      });

      if (error) throw error;
      if (data.error) throw new Error(data.error);

      setLinkToken(data.link_token);
      return data.link_token;
    } catch (error: any) {
      console.error('Error creating link token:', error);
      toast.error('Failed to initialize Plaid: ' + error.message);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, [user]);

  const exchangeToken = useCallback(async (publicToken: string) => {
    setIsLoading(true);
    try {
      const { data, error } = await supabase.functions.invoke('plaid-link', {
        body: { action: 'exchange_token', public_token: publicToken },
      });

      if (error) throw error;
      if (data.error) throw new Error(data.error);

      return { accessToken: data.access_token, itemId: data.item_id };
    } catch (error: any) {
      console.error('Error exchanging token:', error);
      toast.error('Failed to connect account: ' + error.message);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const getAccounts = useCallback(async (accessToken: string): Promise<PlaidAccount[] | null> => {
    try {
      const { data, error } = await supabase.functions.invoke('plaid-link', {
        body: { action: 'get_accounts', access_token: accessToken },
      });

      if (error) throw error;
      if (data.error) throw new Error(data.error);

      return data.accounts;
    } catch (error: any) {
      console.error('Error fetching accounts:', error);
      toast.error('Failed to fetch accounts: ' + error.message);
      return null;
    }
  }, []);

  const getTransactions = useCallback(async (accessToken: string) => {
    try {
      const { data, error } = await supabase.functions.invoke('plaid-link', {
        body: { action: 'get_transactions', access_token: accessToken },
      });

      if (error) throw error;
      if (data.error) throw new Error(data.error);

      return data.transactions;
    } catch (error: any) {
      console.error('Error fetching transactions:', error);
      toast.error('Failed to fetch transactions: ' + error.message);
      return null;
    }
  }, []);

  const getHoldings = useCallback(async (accessToken: string): Promise<{ holdings: PlaidHolding[], securities: PlaidSecurity[] } | null> => {
    try {
      const { data, error } = await supabase.functions.invoke('plaid-link', {
        body: { action: 'get_holdings', access_token: accessToken },
      });

      if (error) throw error;
      if (data.error) throw new Error(data.error);

      return { holdings: data.holdings, securities: data.securities };
    } catch (error: any) {
      console.error('Error fetching holdings:', error);
      toast.error('Failed to fetch holdings: ' + error.message);
      return null;
    }
  }, []);

  const getLiabilities = useCallback(async (accessToken: string) => {
    try {
      const { data, error } = await supabase.functions.invoke('plaid-link', {
        body: { action: 'get_liabilities', access_token: accessToken },
      });

      if (error) throw error;
      if (data.error) throw new Error(data.error);

      return data.liabilities;
    } catch (error: any) {
      console.error('Error fetching liabilities:', error);
      toast.error('Failed to fetch liabilities: ' + error.message);
      return null;
    }
  }, []);

  const setPendingConnection = useCallback((institution: { id: string; name: string; type: string } | null) => {
    setPendingInstitution(institution);
  }, []);

  return {
    isLoading,
    linkToken,
    pendingInstitution,
    createLinkToken,
    exchangeToken,
    getAccounts,
    getTransactions,
    getHoldings,
    getLiabilities,
    setPendingConnection,
  };
}

// Custom hook for Plaid Link component
export function usePlaidLinkHandler(
  linkToken: string | null,
  onSuccess: (publicToken: string, metadata: any) => void,
  onExit?: () => void
) {
  const config: PlaidLinkOptions = {
    token: linkToken,
    onSuccess: (public_token, metadata) => {
      onSuccess(public_token, metadata);
    },
    onExit: (err, metadata) => {
      if (err) {
        console.error('Plaid Link error:', err);
      }
      onExit?.();
    },
  };

  const { open, ready } = usePlaidLink(config);

  return { open, ready };
}
