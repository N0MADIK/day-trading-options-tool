-- Migration: 006_add_profile_fields.sql
-- Description: Add additional profile fields for user management
-- Created: 2026-01-04
--
-- This migration adds phone, address, and date_of_birth fields to profiles

-- Add new columns to profiles table
ALTER TABLE public.profiles 
  ADD COLUMN IF NOT EXISTS phone TEXT,
  ADD COLUMN IF NOT EXISTS address TEXT,
  ADD COLUMN IF NOT EXISTS date_of_birth DATE;

-- Create index for phone lookups
CREATE INDEX IF NOT EXISTS idx_profiles_phone ON public.profiles(phone) WHERE phone IS NOT NULL;
