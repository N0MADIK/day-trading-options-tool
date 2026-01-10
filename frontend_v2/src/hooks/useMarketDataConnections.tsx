import { useState, useEffect, useCallback } from 'react';
import { supabase } from '@/integrations/supabase/client';
import { useAuth } from './useAuth';
import { toast } from 'sonner';

export interface MarketDataProvider {
  id: string;
  name: string;
  description: string;
  logo: string;
  requiresAuth: boolean;
  authFields?: {
    name: string;
    label: string;
    type: 'text' | 'password';
    placeholder: string;
  }[];
  features: string[];
  docsUrl?: string;
}

export const MARKET_DATA_PROVIDERS: MarketDataProvider[] = [
  {
    id: 'yfinance',
    name: 'Yahoo Finance',
    description: 'Free market data including stocks, ETFs, indices, and cryptocurrencies. Default provider.',
    logo: '📈',
    requiresAuth: false,
    features: ['Real-time quotes', 'Historical data', 'Stock info', 'Market news'],
  },
  {
    id: 'alpaca',
    name: 'Alpaca Markets',
    description: 'Commission-free trading API with real-time and historical market data.',
    logo: '🦙',
    requiresAuth: true,
    authFields: [
      { name: 'api_key', label: 'API Key', type: 'text', placeholder: 'Your Alpaca API Key' },
      { name: 'api_secret', label: 'API Secret', type: 'password', placeholder: 'Your Alpaca API Secret' },
    ],
    features: ['Real-time data', 'Historical bars', 'Trade execution', 'Paper trading'],
    docsUrl: 'https://alpaca.markets/docs/',
  },
  {
    id: 'interactive-brokers',
    name: 'Interactive Brokers',
    description: 'Professional-grade market data and trading for stocks, options, futures, and forex.',
    logo: '🏛️',
    requiresAuth: true,
    authFields: [
      { name: 'account_id', label: 'Account ID', type: 'text', placeholder: 'Your IB Account ID' },
      { name: 'api_key', label: 'API Key', type: 'password', placeholder: 'Your IB API Key' },
    ],
    features: ['Level 2 data', 'Options chains', 'Futures data', 'Global markets'],
    docsUrl: 'https://www.interactivebrokers.com/en/trading/ib-api.php',
  },
  {
    id: 'polygon',
    name: 'Polygon.io',
    description: 'Real-time and historical market data for stocks, options, forex, and crypto.',
    logo: '🔷',
    requiresAuth: true,
    authFields: [
      { name: 'api_key', label: 'API Key', type: 'password', placeholder: 'Your Polygon API Key' },
    ],
    features: ['Tick data', 'Aggregates', 'Reference data', 'WebSocket streaming'],
    docsUrl: 'https://polygon.io/docs/',
  },
  {
    id: 'tradier',
    name: 'Tradier',
    description: 'Brokerage API with market data, trading, and account management.',
    logo: '🔵',
    requiresAuth: true,
    authFields: [
      { name: 'access_token', label: 'Access Token', type: 'password', placeholder: 'Your Tradier Access Token' },
    ],
    features: ['Options data', 'Streaming quotes', 'Order execution', 'Account data'],
    docsUrl: 'https://documentation.tradier.com/',
  },
  {
    id: 'tiingo',
    name: 'Tiingo',
    description: 'Financial data API with end-of-day and intraday stock prices.',
    logo: '📊',
    requiresAuth: true,
    authFields: [
      { name: 'api_key', label: 'API Key', type: 'password', placeholder: 'Your Tiingo API Key' },
    ],
    features: ['EOD prices', 'IEX real-time', 'News feed', 'Fundamentals'],
    docsUrl: 'https://api.tiingo.com/documentation/',
  },
];

export interface MarketDataSubscription {
  id: string;
  user_id: string;
  provider_name: string;
  provider_type: string;
  is_active: boolean;
  subscription_tier: string | null;
  features: string[] | null;
  expires_at: string | null;
  created_at: string;
  updated_at: string;
  has_credentials: boolean;
}

// Simple encryption using base64 + reversal (for demo purposes)
// In production, use proper encryption via edge function
const encryptCredentials = (data: Record<string, string>): string => {
  const jsonStr = JSON.stringify(data);
  const base64 = btoa(jsonStr);
  return base64.split('').reverse().join('');
};

const decryptCredentials = (encrypted: string): Record<string, string> | null => {
  try {
    const base64 = encrypted.split('').reverse().join('');
    const jsonStr = atob(base64);
    return JSON.parse(jsonStr);
  } catch {
    return null;
  }
};

export function useMarketDataConnections() {
  const { user } = useAuth();
  const [subscriptions, setSubscriptions] = useState<MarketDataSubscription[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchSubscriptions = useCallback(async () => {
    if (!user) {
      setSubscriptions([]);
      setLoading(false);
      return;
    }

    try {
      const { data, error } = await supabase
        .from('market_data_subscriptions')
        .select('*')
        .eq('user_id', user.id);

      if (error) throw error;

      // Map to include has_credentials flag
      const mapped = (data || []).map((sub) => ({
        ...sub,
        features: sub.features as string[] | null,
        has_credentials: !!sub.api_key_encrypted,
      }));

      setSubscriptions(mapped);
    } catch (error) {
      console.error('Error fetching market data subscriptions:', error);
    } finally {
      setLoading(false);
    }
  }, [user]);

  useEffect(() => {
    fetchSubscriptions();
  }, [fetchSubscriptions]);

  const connectProvider = useCallback(
    async (providerId: string, credentials?: Record<string, string>) => {
      if (!user) {
        toast.error('Please sign in to connect market data providers');
        return false;
      }

      const provider = MARKET_DATA_PROVIDERS.find((p) => p.id === providerId);
      if (!provider) {
        toast.error('Unknown provider');
        return false;
      }

      try {
        // Check if already connected
        const existing = subscriptions.find((s) => s.provider_name === providerId);
        if (existing) {
          toast.error(`Already connected to ${provider.name}`);
          return false;
        }

        // Encrypt credentials if provided
        let encryptedKey: string | null = null;
        if (credentials && Object.keys(credentials).length > 0) {
          encryptedKey = encryptCredentials(credentials);
        }

        const { error } = await supabase.from('market_data_subscriptions').insert({
          user_id: user.id,
          provider_name: providerId,
          provider_type: provider.requiresAuth ? 'api_key' : 'free',
          is_active: true,
          subscription_tier: provider.requiresAuth ? 'api' : 'free',
          api_key_encrypted: encryptedKey,
          features: provider.features,
        });

        if (error) throw error;

        toast.success(`Connected to ${provider.name}!`);
        await fetchSubscriptions();
        return true;
      } catch (error: any) {
        console.error('Error connecting provider:', error);
        toast.error(`Failed to connect: ${error.message}`);
        return false;
      }
    },
    [user, subscriptions, fetchSubscriptions]
  );

  const disconnectProvider = useCallback(
    async (subscriptionId: string) => {
      if (!user) return false;

      try {
        const sub = subscriptions.find((s) => s.id === subscriptionId);
        
        const { error } = await supabase
          .from('market_data_subscriptions')
          .delete()
          .eq('id', subscriptionId)
          .eq('user_id', user.id);

        if (error) throw error;

        toast.success(`Disconnected from ${sub?.provider_name || 'provider'}`);
        await fetchSubscriptions();
        return true;
      } catch (error: any) {
        console.error('Error disconnecting provider:', error);
        toast.error(`Failed to disconnect: ${error.message}`);
        return false;
      }
    },
    [user, subscriptions, fetchSubscriptions]
  );

  const updateCredentials = useCallback(
    async (subscriptionId: string, credentials: Record<string, string>) => {
      if (!user) return false;

      try {
        const encryptedKey = encryptCredentials(credentials);

        const { error } = await supabase
          .from('market_data_subscriptions')
          .update({
            api_key_encrypted: encryptedKey,
            updated_at: new Date().toISOString(),
          })
          .eq('id', subscriptionId)
          .eq('user_id', user.id);

        if (error) throw error;

        toast.success('Credentials updated successfully');
        await fetchSubscriptions();
        return true;
      } catch (error: any) {
        console.error('Error updating credentials:', error);
        toast.error(`Failed to update: ${error.message}`);
        return false;
      }
    },
    [user, fetchSubscriptions]
  );

  const getProviderStatus = useCallback(
    (providerId: string) => {
      return subscriptions.find((s) => s.provider_name === providerId);
    },
    [subscriptions]
  );

  const getActiveProvider = useCallback(() => {
    // Return the first active subscription, or yfinance as default
    const active = subscriptions.find((s) => s.is_active);
    if (active) return active;
    
    // Check if yfinance is connected
    const yfinance = subscriptions.find((s) => s.provider_name === 'yfinance');
    return yfinance || null;
  }, [subscriptions]);

  const getCredentials = useCallback(
    async (providerId: string): Promise<Record<string, string> | null> => {
      if (!user) return null;

      try {
        const { data, error } = await supabase
          .from('market_data_subscriptions')
          .select('api_key_encrypted')
          .eq('user_id', user.id)
          .eq('provider_name', providerId)
          .maybeSingle();

        if (error || !data?.api_key_encrypted) return null;

        return decryptCredentials(data.api_key_encrypted);
      } catch {
        return null;
      }
    },
    [user]
  );

  return {
    subscriptions,
    loading,
    providers: MARKET_DATA_PROVIDERS,
    connectProvider,
    disconnectProvider,
    updateCredentials,
    getProviderStatus,
    getActiveProvider,
    getCredentials,
    fetchSubscriptions,
  };
}
