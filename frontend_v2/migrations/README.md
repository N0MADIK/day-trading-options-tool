# Database Migrations

This folder contains all the SQL migrations and documentation needed to set up, maintain, and transition the database for this project.

## Overview

These migrations are designed to work with [Supabase](https://supabase.com/) (PostgreSQL-based) and can be used to:
- Set up a new Supabase project from scratch
- Transition from Lovable Cloud to self-hosted Supabase
- Migrate to alternative PostgreSQL-compatible backends
- Understand the complete database schema

## Quick Start

```bash
# Run all migrations in order
psql "postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres" \
  -f migrations/001_initial_schema.sql \
  -f migrations/002_storage_buckets.sql \
  -f migrations/003_auth_config.sql \
  -f migrations/004_indexes.sql \
  -f migrations/005_custom_notification_rules.sql \
  -f migrations/006_add_profile_fields.sql
```

## Migration Files

| File | Description | Required |
|------|-------------|----------|
| `001_initial_schema.sql` | Core database schema including all tables, RLS policies, functions, and triggers | ✅ Yes |
| `002_storage_buckets.sql` | Storage bucket configuration for file uploads (avatars, documents) | Optional |
| `003_auth_config.sql` | Authentication configuration notes and helper functions | ✅ Yes |
| `004_indexes.sql` | Performance indexes for common queries | Recommended |
| `005_custom_notification_rules.sql` | Custom notification rules table for advanced alerts | ✅ Yes |
| `006_add_profile_fields.sql` | Additional profile fields (phone, address, DOB) | ✅ Yes |

## Documentation Files

| File | Description |
|------|-------------|
| `README.md` | This file - migration overview and instructions |
| `SELF_HOSTED_SETUP.md` | Quick setup guide for self-hosted Supabase |
| `BACKEND_TRANSITION_GUIDE.md` | Comprehensive guide for migrating to different backends |

## Prerequisites

- A Supabase project (self-hosted or Supabase.com) OR compatible PostgreSQL 14+ database
- Access to SQL Editor, `psql` CLI, or Supabase CLI
- For self-hosting: Docker and Docker Compose (optional)

---

## Setup Instructions

### Option 1: Using Supabase Dashboard (Easiest)

1. Go to your Supabase project dashboard
2. Navigate to **SQL Editor**
3. Run each migration file in numerical order
4. Verify tables are created under **Table Editor**

### Option 2: Using Supabase CLI

```bash
# Install Supabase CLI
npm install -g supabase

# Initialize (if new project)
supabase init

# Link to your project
supabase link --project-ref YOUR_PROJECT_REF

# Copy migrations
mkdir -p supabase/migrations
cp migrations/*.sql supabase/migrations/

# Push to database
supabase db push
```

### Option 3: Using psql Directly

```bash
# Connect to database
psql "postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres"

# Run migrations
\i migrations/001_initial_schema.sql
\i migrations/002_storage_buckets.sql
\i migrations/003_auth_config.sql
\i migrations/004_indexes.sql
\i migrations/005_custom_notification_rules.sql
\i migrations/006_add_profile_fields.sql

# Verify
\dt public.*
```

### Option 4: Docker (Self-Hosted)

```bash
# Start Supabase stack
cd supabase/docker
docker compose up -d

# Run migrations
docker exec -i supabase-db psql -U postgres -d postgres < ../migrations/001_initial_schema.sql
# ... repeat for other migration files
```

---

## Post-Migration Setup

### 1. Configure Authentication

In Supabase Dashboard → Authentication → Settings:

- ✅ Enable Email/Password sign-up
- ✅ Enable Auto-confirm emails (development) OR configure SMTP (production)
- ✅ Set Site URL and Redirect URLs
- ❌ Disable Anonymous sign-ins

### 2. Update Environment Variables

Create/update your `.env` file:

```env
VITE_SUPABASE_URL=https://your-project-ref.supabase.co
VITE_SUPABASE_PUBLISHABLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
VITE_SUPABASE_PROJECT_ID=your-project-ref
```

### 3. Regenerate TypeScript Types

```bash
# Generate types from your database schema
npx supabase gen types typescript --project-id YOUR_PROJECT_REF > src/integrations/supabase/types.ts
```

### 4. Configure External Services

Add secrets for external integrations:

| Service | Secrets Required | Dashboard Location |
|---------|------------------|-------------------|
| Plaid | `PLAID_CLIENT_ID`, `PLAID_SECRET`, `PLAID_ENV` | Edge Function Secrets |
| SnapTrade | `SNAPTRADE_CLIENT_ID`, `SNAPTRADE_CONSUMER_KEY` | Edge Function Secrets |
| Alpaca | `ALPACA_API_KEY`, `ALPACA_API_SECRET` | Edge Function Secrets |

---

## Database Schema Overview

### Entity Relationship Diagram

```
┌─────────────┐      ┌──────────────────┐      ┌─────────────┐
│  auth.users │──────│     profiles     │──────│ user_roles  │
└─────────────┘      └──────────────────┘      └─────────────┘
       │                     │
       │              ┌──────┴──────┐
       │              │             │
       ▼              ▼             ▼
┌─────────────────┐  ┌─────────────┐  ┌────────────────────────┐
│connected_accounts│  │  holdings   │  │ notification_settings  │
└─────────────────┘  └─────────────┘  └────────────────────────┘
       │                   │                      │
       │                   │                      │
       ▼                   ▼                      ▼
┌─────────────────┐  ┌─────────────┐  ┌────────────────────────┐
│  transactions   │  │  watchlist  │  │custom_notification_rules│
└─────────────────┘  └─────────────┘  └────────────────────────┘
```

### Tables Reference

| Table | Purpose | RLS |
|-------|---------|-----|
| `profiles` | User profile information (email, name, avatar) | ✅ |
| `user_roles` | Role assignments (admin, user, premium) | ✅ |
| `connected_accounts` | Linked financial institutions | ✅ |
| `holdings` | Securities and positions | ✅ |
| `transactions` | Trade history and account transactions | ✅ |
| `market_data_subscriptions` | Market data provider configurations | ✅ |
| `trading_strategies` | User-defined trading strategies | ✅ |
| `watchlist` | Stock watchlist with price alerts | ✅ |
| `net_worth_history` | Historical net worth snapshots | ✅ |
| `net_worth_goals` | User financial goals | ✅ |
| `notification_settings` | User notification preferences | ✅ |
| `custom_notification_rules` | Advanced custom alerts | ✅ |

### Database Functions

| Function | Purpose | Security |
|----------|---------|----------|
| `handle_new_user()` | Creates profile, role, settings on signup | DEFINER |
| `has_role(user_id, role)` | Check if user has specific role | DEFINER |
| `update_updated_at_column()` | Auto-update timestamps | DEFINER |
| `get_current_user_profile()` | Get authenticated user's profile | DEFINER |
| `is_admin()` | Check if current user is admin | DEFINER |
| `is_premium()` | Check if current user is premium | DEFINER |

### Triggers

| Trigger | Table | Event | Purpose |
|---------|-------|-------|---------|
| `on_auth_user_created` | `auth.users` | INSERT | Creates initial user records |
| `update_*_updated_at` | Various | UPDATE | Maintains timestamps |

---

## Row Level Security (RLS)

All tables have RLS enabled with the following patterns:

### Standard User Tables
```sql
-- Users can only access their own data
CREATE POLICY "Users can view their own data" ON table_name
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can create their own data" ON table_name
  FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own data" ON table_name
  FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own data" ON table_name
  FOR DELETE USING (auth.uid() = user_id);
```

### System-Managed Tables (profiles, notification_settings)
- No INSERT policy (created by trigger)
- No DELETE policy (managed by cascade)

---

## Troubleshooting

### Migration Fails: "already exists"

```sql
-- Nuclear option - drops ALL data!
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO public;
GRANT ALL ON SCHEMA public TO anon;
GRANT ALL ON SCHEMA public TO authenticated;
GRANT ALL ON SCHEMA public TO service_role;

-- Then re-run migrations
```

### RLS Blocks All Requests

Ensure requests include valid JWT:
```typescript
const { data } = await supabase
  .from('profiles')
  .select('*')
  // User must be authenticated
```

### Trigger Not Firing

```sql
-- Check trigger exists
SELECT * FROM information_schema.triggers 
WHERE trigger_name = 'on_auth_user_created';

-- Check function exists
SELECT proname, prosrc FROM pg_proc 
WHERE proname = 'handle_new_user';
```

### Foreign Key Violation

Ensure referenced records exist:
```sql
-- Check if user exists in auth.users
SELECT id FROM auth.users WHERE id = 'uuid-here';
```

---

## Security Notes

1. **RLS Enabled**: All tables have Row Level Security
2. **SECURITY DEFINER**: Functions with elevated permissions use `search_path = public`
3. **Cascading Deletes**: User deletion removes all associated data
4. **No Direct Auth Access**: Frontend uses `profiles` table for user data
5. **API Keys as Secrets**: Never store API keys in code or database

---

## Backend Transition

For detailed instructions on migrating to different backends (Firebase, AWS, custom), see:

📖 **[BACKEND_TRANSITION_GUIDE.md](./BACKEND_TRANSITION_GUIDE.md)**

---

## External Service Integration

### Financial Services

| Service | Purpose | Documentation |
|---------|---------|---------------|
| [Plaid](https://plaid.com) | Banking connections | [plaid.com/docs](https://plaid.com/docs) |
| [SnapTrade](https://snaptrade.com) | Brokerage connections | [docs.snaptrade.com](https://docs.snaptrade.com) |
| [Alpaca](https://alpaca.markets) | Trading & market data | [alpaca.markets/docs](https://alpaca.markets/docs) |

### Market Data Providers

| Provider | Data Type | Free Tier |
|----------|-----------|-----------|
| Alpha Vantage | Stocks, forex, crypto | 25 req/day |
| Polygon.io | Real-time & historical | 5 req/min |
| IEX Cloud | US stocks | 50k credits/mo |
| Yahoo Finance | Basic quotes | Unofficial |
