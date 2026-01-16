import { useState, useEffect, useCallback } from 'react';
import { useAuth } from './useAuth';
import { toast } from '@/hooks/use-toast';
import { api } from '@/lib/api';

// Connected account type from backend API
interface ConnectedAccount {
  id: string;
  user_id: string;
  institution_name: string;
  institution_type: string;
  account_name: string;
  account_number_masked: string | null;
  balance: number;
  currency?: string;
  is_connected: boolean;
  connection_status: string;
  last_synced_at: string | null;
  metadata: Record<string, any>;
  created_at: string;
  updated_at: string | null;
}

interface Holding {
  id: string;
  user_id: string;
  account_id: string;
  symbol: string;
  name: string | null;
  quantity: number;
  average_cost: number | null;
  current_price: number | null;
  market_value: number;
  asset_type: string | null;
  unrealized_pnl: number | null;
  unrealized_pnl_percent: number | null;
}

interface Transaction {
  id: string;
  user_id: string;
  account_id: string;
  symbol: string | null;
  transaction_type: string;
  quantity: number | null;
  price: number | null;
  total_amount: number;
  transaction_date: string;
  description: string | null;
}

export function useConnections() {
  const { user } = useAuth();
  const [accounts, setAccounts] = useState<ConnectedAccount[]>([]);
  const [holdings, setHoldings] = useState<Holding[]>([]);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);

  // Fetch all connected accounts for the current user
  const fetchAccounts = useCallback(async () => {
    if (!user) {
      setAccounts([]);
      setLoading(false);
      return;
    }

    try {
      const data = await api.get<ConnectedAccount[]>('/connected-accounts');
      setAccounts(data || []);
    } catch (error) {
      console.error('Error fetching accounts:', error);
      toast({ title: 'Error', description: 'Failed to load connected accounts', variant: 'destructive' });
    } finally {
      setLoading(false);
    }
  }, [user]);

  // Fetch holdings for a specific account or all accounts
  const fetchHoldings = useCallback(async (accountId?: string) => {
    if (!user) return;

    try {
      const endpoint = accountId
        ? `/holdings?account_id=${encodeURIComponent(accountId)}`
        : '/holdings';
      const data = await api.get<Holding[]>(endpoint);
      setHoldings(data || []);
    } catch (error) {
      console.error('Error fetching holdings:', error);
    }
  }, [user]);

  // Fetch transactions for a specific account or all accounts
  const fetchTransactions = useCallback(async (accountId?: string) => {
    if (!user) return;

    try {
      const endpoint = accountId
        ? `/transactions?account_id=${encodeURIComponent(accountId)}`
        : '/transactions';
      const data = await api.get<Transaction[]>(endpoint);
      setTransactions(data || []);
    } catch (error) {
      console.error('Error fetching transactions:', error);
    }
  }, [user]);

  // Disconnect an account
  const disconnectAccount = useCallback(async (accountId: string) => {
    if (!user) return;

    try {
      await api.delete(`/connected-accounts/${accountId}`);
      toast({ title: 'Account Disconnected', description: 'Your account has been unlinked.' });
      await fetchAccounts();
    } catch (error: any) {
      console.error('Error disconnecting account:', error);
      toast({ title: 'Error', description: error.message || 'Failed to disconnect account', variant: 'destructive' });
    }
  }, [user, fetchAccounts]);

  // Sync account data (refresh)
  const syncAccount = useCallback(async (accountId: string) => {
    if (!user) return;

    try {
      await api.post(`/connected-accounts/${accountId}/sync`);
      toast({ title: 'Sync Complete', description: 'Account data has been updated.' });
      await fetchAccounts();
    } catch (error: any) {
      console.error('Error syncing account:', error);
      toast({ title: 'Error', description: 'Failed to sync account', variant: 'destructive' });
    }
  }, [user, fetchAccounts]);

  // Get account by institution ID
  const getAccountByInstitution = useCallback((institutionId: string) => {
    return accounts.find(a => {
      const metadata = a.metadata as { institution_id?: string } | null;
      return metadata?.institution_id === institutionId;
    });
  }, [accounts]);

  // Calculate total net worth from accounts + holdings
  const totalNetWorth = (() => {
    // Sum account balances
    const accountBalance = accounts.reduce((sum, acc) => sum + (acc.balance || 0), 0);

    // If we have account balances, use that
    if (accountBalance > 0) return accountBalance;

    // Otherwise, sum holdings market values (for CSV imports without connected accounts)
    return holdings.reduce((sum, h) => sum + Math.abs(h.market_value || 0), 0);
  })();

  useEffect(() => {
    fetchAccounts();
  }, [fetchAccounts]);

  // Fetch holdings and transactions whenever user changes (not dependent on accounts)
  useEffect(() => {
    if (user) {
      fetchHoldings();
      fetchTransactions();
    }
  }, [user, fetchHoldings, fetchTransactions]);

  return {
    accounts,
    holdings,
    transactions,
    loading,
    totalNetWorth,
    disconnectAccount,
    syncAccount,
    fetchAccounts,
    fetchHoldings,
    fetchTransactions,
    getAccountByInstitution,
  };
}
