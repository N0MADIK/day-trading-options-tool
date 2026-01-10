import { useState, useEffect, useCallback } from 'react';
import { supabase } from '@/integrations/supabase/client';
import { useAuth } from './useAuth';
import { toast } from '@/hooks/use-toast';
import { Tables, TablesInsert } from '@/integrations/supabase/types';

type ConnectedAccount = Tables<'connected_accounts'>;
type Holding = Tables<'holdings'>;
type Transaction = Tables<'transactions'>;

interface TestAccountData {
  holdings: Omit<TablesInsert<'holdings'>, 'user_id' | 'account_id'>[];
  transactions: Omit<TablesInsert<'transactions'>, 'user_id' | 'account_id'>[];
}

// Test data for demo accounts
const testAccountData: Record<string, TestAccountData> = {
  'wells-fargo': {
    holdings: [],
    transactions: [
      { symbol: null, transaction_type: 'deposit', quantity: null, price: null, total_amount: 5000, transaction_date: new Date(Date.now() - 86400000 * 30).toISOString(), description: 'Direct Deposit - Payroll' },
      { symbol: null, transaction_type: 'withdrawal', quantity: null, price: null, total_amount: 1500, transaction_date: new Date(Date.now() - 86400000 * 25).toISOString(), description: 'ATM Withdrawal' },
      { symbol: null, transaction_type: 'deposit', quantity: null, price: null, total_amount: 5000, transaction_date: new Date(Date.now() - 86400000 * 15).toISOString(), description: 'Direct Deposit - Payroll' },
      { symbol: null, transaction_type: 'withdrawal', quantity: null, price: null, total_amount: 2000, transaction_date: new Date(Date.now() - 86400000 * 10).toISOString(), description: 'Transfer to Savings' },
      { symbol: null, transaction_type: 'deposit', quantity: null, price: null, total_amount: 5000, transaction_date: new Date(Date.now() - 86400000 * 1).toISOString(), description: 'Direct Deposit - Payroll' },
    ],
  },
  'vanguard': {
    holdings: [
      { symbol: 'VTI', name: 'Vanguard Total Stock Market ETF', quantity: 150, average_cost: 220.50, current_price: 235.80, market_value: 35370, asset_type: 'etf', unrealized_pnl: 2295, unrealized_pnl_percent: 6.94 },
      { symbol: 'VXUS', name: 'Vanguard Total International Stock ETF', quantity: 100, average_cost: 58.20, current_price: 61.45, market_value: 6145, asset_type: 'etf', unrealized_pnl: 325, unrealized_pnl_percent: 5.58 },
      { symbol: 'BND', name: 'Vanguard Total Bond Market ETF', quantity: 75, average_cost: 74.50, current_price: 72.30, market_value: 5422.50, asset_type: 'etf', unrealized_pnl: -165, unrealized_pnl_percent: -2.95 },
      { symbol: 'VFIAX', name: 'Vanguard 500 Index Fund', quantity: 50, average_cost: 410.00, current_price: 445.20, market_value: 22260, asset_type: 'mutual_fund', unrealized_pnl: 1760, unrealized_pnl_percent: 8.59 },
    ],
    transactions: [
      { symbol: 'VTI', transaction_type: 'buy', quantity: 50, price: 218.00, total_amount: 10900, transaction_date: new Date(Date.now() - 86400000 * 180).toISOString(), description: 'Monthly Investment' },
      { symbol: 'VTI', transaction_type: 'buy', quantity: 50, price: 222.50, total_amount: 11125, transaction_date: new Date(Date.now() - 86400000 * 90).toISOString(), description: 'Monthly Investment' },
      { symbol: 'VTI', transaction_type: 'buy', quantity: 50, price: 221.00, total_amount: 11050, transaction_date: new Date(Date.now() - 86400000 * 30).toISOString(), description: 'Monthly Investment' },
      { symbol: 'VXUS', transaction_type: 'buy', quantity: 100, price: 58.20, total_amount: 5820, transaction_date: new Date(Date.now() - 86400000 * 60).toISOString(), description: 'International Diversification' },
      { symbol: 'BND', transaction_type: 'buy', quantity: 75, price: 74.50, total_amount: 5587.50, transaction_date: new Date(Date.now() - 86400000 * 45).toISOString(), description: 'Bond Allocation' },
      { symbol: 'VTI', transaction_type: 'dividend', quantity: null, price: null, total_amount: 245.50, transaction_date: new Date(Date.now() - 86400000 * 15).toISOString(), description: 'Quarterly Dividend' },
    ],
  },
  'robinhood': {
    holdings: [
      { symbol: 'AAPL', name: 'Apple Inc.', quantity: 25, average_cost: 165.00, current_price: 178.50, market_value: 4462.50, asset_type: 'stock', unrealized_pnl: 337.50, unrealized_pnl_percent: 8.18 },
      { symbol: 'TSLA', name: 'Tesla Inc.', quantity: 10, average_cost: 220.00, current_price: 248.50, market_value: 2485, asset_type: 'stock', unrealized_pnl: 285, unrealized_pnl_percent: 12.95 },
      { symbol: 'NVDA', name: 'NVIDIA Corp.', quantity: 8, average_cost: 450.00, current_price: 495.20, market_value: 3961.60, asset_type: 'stock', unrealized_pnl: 361.60, unrealized_pnl_percent: 10.04 },
      { symbol: 'MSFT', name: 'Microsoft Corp.', quantity: 12, average_cost: 350.00, current_price: 378.90, market_value: 4546.80, asset_type: 'stock', unrealized_pnl: 346.80, unrealized_pnl_percent: 8.26 },
      { symbol: 'GOOGL', name: 'Alphabet Inc.', quantity: 15, average_cost: 130.00, current_price: 141.80, market_value: 2127, asset_type: 'stock', unrealized_pnl: 177, unrealized_pnl_percent: 9.08 },
      { symbol: 'AMC', name: 'AMC Entertainment', quantity: 100, average_cost: 15.00, current_price: 4.85, market_value: 485, asset_type: 'stock', unrealized_pnl: -1015, unrealized_pnl_percent: -67.67 },
    ],
    transactions: [
      { symbol: 'AAPL', transaction_type: 'buy', quantity: 25, price: 165.00, total_amount: 4125, transaction_date: new Date(Date.now() - 86400000 * 120).toISOString(), description: 'Initial Purchase' },
      { symbol: 'TSLA', transaction_type: 'buy', quantity: 10, price: 220.00, total_amount: 2200, transaction_date: new Date(Date.now() - 86400000 * 90).toISOString(), description: 'Limit Order Filled' },
      { symbol: 'NVDA', transaction_type: 'buy', quantity: 8, price: 450.00, total_amount: 3600, transaction_date: new Date(Date.now() - 86400000 * 60).toISOString(), description: 'AI Play' },
      { symbol: 'MSFT', transaction_type: 'buy', quantity: 12, price: 350.00, total_amount: 4200, transaction_date: new Date(Date.now() - 86400000 * 45).toISOString(), description: 'Recurring Investment' },
      { symbol: 'GOOGL', transaction_type: 'buy', quantity: 15, price: 130.00, total_amount: 1950, transaction_date: new Date(Date.now() - 86400000 * 30).toISOString(), description: 'Dip Buy' },
      { symbol: 'AMC', transaction_type: 'buy', quantity: 100, price: 15.00, total_amount: 1500, transaction_date: new Date(Date.now() - 86400000 * 365).toISOString(), description: 'Meme Stock YOLO' },
      { symbol: 'SPY', transaction_type: 'sell', quantity: 20, price: 475.00, total_amount: 9500, transaction_date: new Date(Date.now() - 86400000 * 7).toISOString(), description: 'Profit Taking' },
    ],
  },
};

// Institution metadata
const institutionMeta: Record<string, { name: string; type: string; provider: string; balance: number }> = {
  'wells-fargo': { name: 'Wells Fargo', type: 'bank', provider: 'plaid', balance: 12500.75 },
  'vanguard': { name: 'Vanguard', type: 'brokerage', provider: 'snaptrade', balance: 69197.50 },
  'robinhood': { name: 'Robinhood', type: 'brokerage', provider: 'snaptrade', balance: 18067.90 },
};

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
      const { data, error } = await supabase
        .from('connected_accounts')
        .select('*')
        .eq('user_id', user.id)
        .order('created_at', { ascending: false });

      if (error) throw error;
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
      let query = supabase.from('holdings').select('*').eq('user_id', user.id);
      if (accountId) query = query.eq('account_id', accountId);
      
      const { data, error } = await query.order('market_value', { ascending: false });
      if (error) throw error;
      setHoldings(data || []);
    } catch (error) {
      console.error('Error fetching holdings:', error);
    }
  }, [user]);

  // Fetch transactions for a specific account or all accounts
  const fetchTransactions = useCallback(async (accountId?: string) => {
    if (!user) return;

    try {
      let query = supabase.from('transactions').select('*').eq('user_id', user.id);
      if (accountId) query = query.eq('account_id', accountId);
      
      const { data, error } = await query.order('transaction_date', { ascending: false });
      if (error) throw error;
      setTransactions(data || []);
    } catch (error) {
      console.error('Error fetching transactions:', error);
    }
  }, [user]);

  // Connect a new account (with test data for demo)
  const connectAccount = useCallback(async (institutionId: string): Promise<ConnectedAccount | null> => {
    if (!user) {
      toast({ title: 'Error', description: 'You must be logged in to connect accounts', variant: 'destructive' });
      return null;
    }

    const meta = institutionMeta[institutionId];
    if (!meta) {
      toast({ title: 'Error', description: 'Unknown institution', variant: 'destructive' });
      return null;
    }

    try {
      // Create the connected account
      const accountData: TablesInsert<'connected_accounts'> = {
        user_id: user.id,
        institution_name: meta.name,
        institution_type: meta.type,
        account_name: `${meta.name} Account`,
        account_number_masked: `****${Math.floor(1000 + Math.random() * 9000)}`,
        balance: meta.balance,
        is_connected: true,
        connection_status: 'active',
        last_synced_at: new Date().toISOString(),
        metadata: { provider: meta.provider, institution_id: institutionId },
      };

      const { data: account, error: accountError } = await supabase
        .from('connected_accounts')
        .insert(accountData)
        .select()
        .single();

      if (accountError) throw accountError;

      // Insert test holdings and transactions
      const testData = testAccountData[institutionId];
      if (testData && account) {
        // Insert holdings
        if (testData.holdings.length > 0) {
          const holdingsData = testData.holdings.map(h => ({
            ...h,
            user_id: user.id,
            account_id: account.id,
          }));
          await supabase.from('holdings').insert(holdingsData);
        }

        // Insert transactions
        if (testData.transactions.length > 0) {
          const transactionsData = testData.transactions.map(t => ({
            ...t,
            user_id: user.id,
            account_id: account.id,
          }));
          await supabase.from('transactions').insert(transactionsData);
        }
      }

      toast({ title: 'Account Connected', description: `${meta.name} has been successfully linked.` });
      await fetchAccounts();
      return account;
    } catch (error: any) {
      console.error('Error connecting account:', error);
      toast({ title: 'Error', description: error.message || 'Failed to connect account', variant: 'destructive' });
      return null;
    }
  }, [user, fetchAccounts]);

  // Disconnect an account
  const disconnectAccount = useCallback(async (accountId: string) => {
    if (!user) return;

    try {
      // Delete holdings and transactions first (cascade should handle this, but explicit is safer)
      await supabase.from('holdings').delete().eq('account_id', accountId);
      await supabase.from('transactions').delete().eq('account_id', accountId);
      
      // Delete the account
      const { error } = await supabase.from('connected_accounts').delete().eq('id', accountId);
      if (error) throw error;

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
      const { error } = await supabase
        .from('connected_accounts')
        .update({ last_synced_at: new Date().toISOString() })
        .eq('id', accountId);

      if (error) throw error;

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
    connectAccount,
    disconnectAccount,
    syncAccount,
    fetchAccounts,
    fetchHoldings,
    fetchTransactions,
    getAccountByInstitution,
  };
}
