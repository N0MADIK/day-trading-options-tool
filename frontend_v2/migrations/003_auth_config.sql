-- Migration: 003_auth_config.sql
-- Description: Authentication configuration notes and helper functions
-- Created: 2026-01-02
--
-- IMPORTANT: Most auth configuration is done via the Supabase Dashboard
-- This file documents the required settings and provides helper functions

/*
=============================================================================
SUPABASE DASHBOARD CONFIGURATION
=============================================================================

Navigate to: Authentication > Settings

1. EMAIL SETTINGS
   - Enable Email sign-up: ON
   - Confirm email: OFF (for development) / ON (for production)
   - Secure email change: ON
   - Double confirm email change: OFF

2. SECURITY SETTINGS
   - Enable new user signups: ON
   - Enable anonymous sign-ins: OFF

3. PASSWORD SETTINGS  
   - Min password length: 8
   - Required characters: lowercase, uppercase, number recommended

4. RATE LIMITS (recommended)
   - Rate limit for email verification: 5 per hour
   - Rate limit for password recovery: 5 per hour

5. MAILER SETTINGS (for production)
   Configure your SMTP settings:
   - Sender email
   - SMTP host, port, username, password

6. URL CONFIGURATION
   - Site URL: Your production URL (e.g., https://yourapp.com)
   - Redirect URLs: Add all valid redirect URLs
   
=============================================================================
*/

-- Helper function to get current user's profile
CREATE OR REPLACE FUNCTION public.get_current_user_profile()
RETURNS TABLE (
  id UUID,
  user_id UUID,
  email TEXT,
  full_name TEXT,
  avatar_url TEXT,
  subscription_tier TEXT,
  created_at TIMESTAMP WITH TIME ZONE
)
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT 
    p.id,
    p.user_id,
    p.email,
    p.full_name,
    p.avatar_url,
    p.subscription_tier,
    p.created_at
  FROM public.profiles p
  WHERE p.user_id = auth.uid()
$$;

-- Helper function to check if current user is admin
CREATE OR REPLACE FUNCTION public.is_admin()
RETURNS BOOLEAN
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT public.has_role(auth.uid(), 'admin')
$$;

-- Helper function to check if current user is premium
CREATE OR REPLACE FUNCTION public.is_premium()
RETURNS BOOLEAN
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT public.has_role(auth.uid(), 'premium')
$$;

-- Grant execute permissions
GRANT EXECUTE ON FUNCTION public.get_current_user_profile() TO authenticated;
GRANT EXECUTE ON FUNCTION public.is_admin() TO authenticated;
GRANT EXECUTE ON FUNCTION public.is_premium() TO authenticated;
