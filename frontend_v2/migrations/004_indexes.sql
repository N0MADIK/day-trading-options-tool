-- Migration: 004_indexes.sql
-- Description: Performance indexes for common queries
-- Created: 2026-01-02
--
-- Run this AFTER the initial schema migration for better query performance

-- Indexes for profiles table
CREATE INDEX IF NOT EXISTS idx_profiles_user_id ON public.profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_profiles_email ON public.profiles(email);

-- Indexes for user_roles table
CREATE INDEX IF NOT EXISTS idx_user_roles_user_id ON public.user_roles(user_id);
CREATE INDEX IF NOT EXISTS idx_user_roles_role ON public.user_roles(role);

-- Indexes for connected_accounts table
CREATE INDEX IF NOT EXISTS idx_connected_accounts_user_id ON public.connected_accounts(user_id);
CREATE INDEX IF NOT EXISTS idx_connected_accounts_institution_type ON public.connected_accounts(institution_type);
CREATE INDEX IF NOT EXISTS idx_connected_accounts_is_connected ON public.connected_accounts(is_connected);

-- Indexes for holdings table
CREATE INDEX IF NOT EXISTS idx_holdings_user_id ON public.holdings(user_id);
CREATE INDEX IF NOT EXISTS idx_holdings_account_id ON public.holdings(account_id);
CREATE INDEX IF NOT EXISTS idx_holdings_symbol ON public.holdings(symbol);
CREATE INDEX IF NOT EXISTS idx_holdings_asset_type ON public.holdings(asset_type);

-- Indexes for transactions table
CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON public.transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_transactions_account_id ON public.transactions(account_id);
CREATE INDEX IF NOT EXISTS idx_transactions_symbol ON public.transactions(symbol);
CREATE INDEX IF NOT EXISTS idx_transactions_transaction_type ON public.transactions(transaction_type);
CREATE INDEX IF NOT EXISTS idx_transactions_transaction_date ON public.transactions(transaction_date DESC);

-- Indexes for market_data_subscriptions table
CREATE INDEX IF NOT EXISTS idx_market_data_subscriptions_user_id ON public.market_data_subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_market_data_subscriptions_is_active ON public.market_data_subscriptions(is_active);
CREATE INDEX IF NOT EXISTS idx_market_data_subscriptions_provider_type ON public.market_data_subscriptions(provider_type);

-- Indexes for trading_strategies table
CREATE INDEX IF NOT EXISTS idx_trading_strategies_user_id ON public.trading_strategies(user_id);
CREATE INDEX IF NOT EXISTS idx_trading_strategies_is_active ON public.trading_strategies(is_active);
CREATE INDEX IF NOT EXISTS idx_trading_strategies_strategy_type ON public.trading_strategies(strategy_type);
CREATE INDEX IF NOT EXISTS idx_trading_strategies_next_execution ON public.trading_strategies(next_execution_at)
  WHERE is_active = true AND is_automated = true;

-- Indexes for watchlist table
CREATE INDEX IF NOT EXISTS idx_watchlist_user_id ON public.watchlist(user_id);
CREATE INDEX IF NOT EXISTS idx_watchlist_symbol ON public.watchlist(symbol);

-- Indexes for net_worth_history table
CREATE INDEX IF NOT EXISTS idx_net_worth_history_user_id ON public.net_worth_history(user_id);
CREATE INDEX IF NOT EXISTS idx_net_worth_history_recorded_at ON public.net_worth_history(recorded_at DESC);

-- Indexes for net_worth_goals table
CREATE INDEX IF NOT EXISTS idx_net_worth_goals_user_id ON public.net_worth_goals(user_id);

-- Indexes for notification_settings table
CREATE INDEX IF NOT EXISTS idx_notification_settings_user_id ON public.notification_settings(user_id);

-- Composite indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_holdings_user_symbol ON public.holdings(user_id, symbol);
CREATE INDEX IF NOT EXISTS idx_transactions_user_date ON public.transactions(user_id, transaction_date DESC);
CREATE INDEX IF NOT EXISTS idx_net_worth_history_user_date ON public.net_worth_history(user_id, recorded_at DESC);
