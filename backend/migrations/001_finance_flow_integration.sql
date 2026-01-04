-- Finance-Flow Integration Migration
-- This migration adds all new tables required for finance-flow frontend compatibility
-- Run this after updating to UUID-based user IDs

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Update users table with profile fields (handles UUID migration)
-- Note: If users table already has integer IDs, you'll need to migrate data first
ALTER TABLE users 
    ADD COLUMN IF NOT EXISTS full_name VARCHAR(255),
    ADD COLUMN IF NOT EXISTS avatar_url VARCHAR(500),
    ADD COLUMN IF NOT EXISTS phone VARCHAR(50),
    ADD COLUMN IF NOT EXISTS address TEXT,
    ADD COLUMN IF NOT EXISTS date_of_birth DATE,
    ADD COLUMN IF NOT EXISTS subscription_tier VARCHAR(50) DEFAULT 'free';

-- User roles table
CREATE TABLE IF NOT EXISTS user_roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL DEFAULT 'user',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, role)
);
CREATE INDEX IF NOT EXISTS idx_user_roles_user_id ON user_roles(user_id);

-- Market data subscriptions table
CREATE TABLE IF NOT EXISTS market_data_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    provider_name VARCHAR(100) NOT NULL,
    provider_type VARCHAR(50) NOT NULL,
    api_key_encrypted TEXT,
    api_secret_encrypted TEXT,
    subscription_tier VARCHAR(50),
    features JSONB DEFAULT '[]',
    is_active BOOLEAN DEFAULT TRUE,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);
CREATE INDEX IF NOT EXISTS idx_market_data_subscriptions_user_id ON market_data_subscriptions(user_id);

-- Net worth history table
CREATE TABLE IF NOT EXISTS net_worth_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    total_net_worth DECIMAL(15, 2) NOT NULL,
    total_assets DECIMAL(15, 2) NOT NULL,
    total_liabilities DECIMAL(15, 2) DEFAULT 0,
    breakdown JSONB DEFAULT '{}',
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_net_worth_history_user_id ON net_worth_history(user_id);
CREATE INDEX IF NOT EXISTS idx_net_worth_history_recorded_at ON net_worth_history(recorded_at);

-- Net worth goals table (one per user)
CREATE TABLE IF NOT EXISTS net_worth_goals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    target_amount DECIMAL(15, 2) NOT NULL,
    target_date TIMESTAMP WITH TIME ZONE,
    notify_on_progress BOOLEAN DEFAULT TRUE,
    notify_threshold_percent DECIMAL(5, 2) DEFAULT 5.00,
    last_notified_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Custom notification rules table
CREATE TABLE IF NOT EXISTS custom_notification_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    rule_name VARCHAR(255) NOT NULL,
    rule_type VARCHAR(50) NOT NULL,
    indicator_type VARCHAR(50),
    conditions JSONB DEFAULT '{}',
    frequency VARCHAR(50) DEFAULT 'immediate',
    urgency_level VARCHAR(50) DEFAULT 'normal',
    is_enabled BOOLEAN DEFAULT TRUE,
    sensitivity DECIMAL(3, 1) DEFAULT 5.0,
    quiet_hours_start TIME,
    quiet_hours_end TIME,
    notify_email BOOLEAN DEFAULT TRUE,
    notify_push BOOLEAN DEFAULT FALSE,
    notify_sms BOOLEAN DEFAULT FALSE,
    last_triggered_at TIMESTAMP WITH TIME ZONE,
    trigger_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);
CREATE INDEX IF NOT EXISTS idx_custom_notification_rules_user_id ON custom_notification_rules(user_id);

-- Notification settings table (one per user)
CREATE TABLE IF NOT EXISTS notification_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    email_notifications BOOLEAN DEFAULT TRUE,
    push_notifications BOOLEAN DEFAULT FALSE,
    price_alerts BOOLEAN DEFAULT TRUE,
    goal_progress_alerts BOOLEAN DEFAULT TRUE,
    weekly_reports BOOLEAN DEFAULT TRUE,
    daily_summary BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Add fields to existing watchlist table (if it exists)
DO $$ 
BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'ticker_watchlist') THEN
        ALTER TABLE ticker_watchlist 
            ADD COLUMN IF NOT EXISTS name VARCHAR(255),
            ADD COLUMN IF NOT EXISTS notes TEXT,
            ADD COLUMN IF NOT EXISTS price_alert_above DECIMAL(15, 4),
            ADD COLUMN IF NOT EXISTS price_alert_below DECIMAL(15, 4);
    END IF;
END $$;

-- Function to check if user has a specific role (replaces Supabase RPC)
CREATE OR REPLACE FUNCTION has_role(_user_id UUID, _role TEXT)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM user_roles 
        WHERE user_id = _user_id AND role = _role
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Grant necessary permissions (adjust as needed for your setup)
-- GRANT EXECUTE ON FUNCTION has_role TO authenticated;
