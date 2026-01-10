-- Migration: 005_custom_notification_rules.sql
-- Description: Custom notification rules table for advanced alerts
-- Created: 2026-01-04
--
-- This migration adds the custom_notification_rules table for
-- user-defined alerts and notification triggers

-- Create custom_notification_rules table
CREATE TABLE IF NOT EXISTS public.custom_notification_rules (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  rule_name TEXT NOT NULL,
  rule_type TEXT NOT NULL, -- price_alert, indicator, news, pattern
  indicator_type TEXT, -- rsi, macd, bollinger, etc.
  conditions JSONB NOT NULL DEFAULT '{}'::jsonb,
  frequency TEXT NOT NULL DEFAULT 'immediate', -- immediate, daily, weekly
  urgency_level TEXT NOT NULL DEFAULT 'normal', -- low, normal, high, critical
  is_enabled BOOLEAN DEFAULT true,
  sensitivity DECIMAL(3,1) DEFAULT 5.0,
  quiet_hours_start TIME,
  quiet_hours_end TIME,
  notify_email BOOLEAN DEFAULT true,
  notify_push BOOLEAN DEFAULT false,
  notify_sms BOOLEAN DEFAULT false,
  last_triggered_at TIMESTAMP WITH TIME ZONE,
  trigger_count INTEGER DEFAULT 0,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL
);

-- Enable RLS
ALTER TABLE public.custom_notification_rules ENABLE ROW LEVEL SECURITY;

-- Create updated_at trigger
CREATE TRIGGER update_custom_notification_rules_updated_at 
  BEFORE UPDATE ON public.custom_notification_rules 
  FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

-- RLS Policies
CREATE POLICY "Users can view their own notification rules" 
  ON public.custom_notification_rules FOR SELECT 
  USING (auth.uid() = user_id);

CREATE POLICY "Users can create their own notification rules" 
  ON public.custom_notification_rules FOR INSERT 
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own notification rules" 
  ON public.custom_notification_rules FOR UPDATE 
  USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own notification rules" 
  ON public.custom_notification_rules FOR DELETE 
  USING (auth.uid() = user_id);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_custom_notification_rules_user_id 
  ON public.custom_notification_rules(user_id);
CREATE INDEX IF NOT EXISTS idx_custom_notification_rules_is_enabled 
  ON public.custom_notification_rules(is_enabled) WHERE is_enabled = true;
CREATE INDEX IF NOT EXISTS idx_custom_notification_rules_rule_type 
  ON public.custom_notification_rules(rule_type);
