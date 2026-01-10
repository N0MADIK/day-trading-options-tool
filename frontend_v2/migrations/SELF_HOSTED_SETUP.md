# Self-Hosted Supabase Setup Guide

This guide walks you through transitioning from Lovable Cloud to a self-hosted Supabase instance or Supabase.com project.

## Quick Start (5 minutes)

### 1. Create Supabase Project

**Option A: Supabase.com (Managed)**
- Go to [supabase.com](https://supabase.com)
- Create a new project
- Note your project URL and anon key

**Option B: Self-Hosted (Docker)**
```bash
git clone --depth 1 https://github.com/supabase/supabase
cd supabase/docker
cp .env.example .env
docker compose up -d
```

### 2. Run Migrations

In the Supabase SQL Editor (or via psql), run files in this order:

```sql
-- 1. Core schema (required)
\i migrations/001_initial_schema.sql

-- 2. Storage buckets (optional, for file uploads)
\i migrations/002_storage_buckets.sql

-- 3. Auth helpers (required)
\i migrations/003_auth_config.sql

-- 4. Performance indexes (recommended)
\i migrations/004_indexes.sql

-- 5. Custom notifications (required)
\i migrations/005_custom_notification_rules.sql

-- 6. Additional profile fields (required)
\i migrations/006_add_profile_fields.sql
```

### 3. Update Environment Variables

```env
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_PUBLISHABLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6...
VITE_SUPABASE_PROJECT_ID=your-project-ref
```

### 4. Configure Authentication

In Supabase Dashboard → Authentication → Settings:
- Enable Email/Password auth
- Enable auto-confirm (development) OR configure SMTP (production)
- Set redirect URLs

### 5. Regenerate Types

```bash
npx supabase gen types typescript --project-id YOUR_PROJECT_REF > src/integrations/supabase/types.ts
```

---

## File Structure

```
migrations/
├── 001_initial_schema.sql           # Core tables, RLS, functions, triggers
├── 002_storage_buckets.sql          # File storage configuration
├── 003_auth_config.sql              # Auth helpers and documentation
├── 004_indexes.sql                  # Performance indexes
├── 005_custom_notification_rules.sql # Custom alerts table
├── 006_add_profile_fields.sql       # Additional profile columns
├── README.md                        # Complete migration documentation
├── SELF_HOSTED_SETUP.md             # This file
└── BACKEND_TRANSITION_GUIDE.md      # Guide for alternative backends
```

---

## Environment Variables Reference

### Frontend (Required)

| Variable | Description | Where to Find |
|----------|-------------|---------------|
| `VITE_SUPABASE_URL` | Project API URL | Dashboard → Settings → API |
| `VITE_SUPABASE_PUBLISHABLE_KEY` | Anon/public key | Dashboard → Settings → API |
| `VITE_SUPABASE_PROJECT_ID` | Project reference | Dashboard → Settings → General |

### Backend Secrets (Edge Functions)

| Secret | Service | Where to Configure |
|--------|---------|-------------------|
| `PLAID_CLIENT_ID` | Plaid | Dashboard → Edge Functions → Secrets |
| `PLAID_SECRET` | Plaid | Dashboard → Edge Functions → Secrets |
| `PLAID_ENV` | Plaid | Dashboard → Edge Functions → Secrets |
| `SNAPTRADE_CLIENT_ID` | SnapTrade | Dashboard → Edge Functions → Secrets |
| `SNAPTRADE_CONSUMER_KEY` | SnapTrade | Dashboard → Edge Functions → Secrets |

---

## Self-Hosted Configuration

### Docker Compose Environment

Edit `supabase/docker/.env`:

```env
# Database
POSTGRES_PASSWORD=your-super-secret-password

# API
ANON_KEY=your-anon-key
SERVICE_ROLE_KEY=your-service-role-key
JWT_SECRET=your-jwt-secret

# Studio
STUDIO_PORT=3000

# Site URL
SITE_URL=http://localhost:3000
```

### Generate Keys

```bash
# Generate JWT secret
openssl rand -base64 32

# Generate service role key
# Use Supabase CLI or online JWT generator
```

---

## Connecting External Services

### Plaid (Banking Integration)

1. Sign up at [plaid.com](https://plaid.com)
2. Get your API keys from the Plaid Dashboard
3. Add to Edge Function secrets:
   - `PLAID_CLIENT_ID`
   - `PLAID_SECRET`
   - `PLAID_ENV` (sandbox, development, or production)

### SnapTrade (Brokerage Integration)

1. Sign up at [snaptrade.com](https://snaptrade.com)
2. Get your client credentials
3. Add to Edge Function secrets:
   - `SNAPTRADE_CLIENT_ID`
   - `SNAPTRADE_CONSUMER_KEY`

### Market Data Providers

| Provider | Sign Up | Free Tier |
|----------|---------|-----------|
| Alpha Vantage | [alphavantage.co](https://www.alphavantage.co) | 25 req/day |
| Polygon.io | [polygon.io](https://polygon.io) | 5 req/min |
| Alpaca | [alpaca.markets](https://alpaca.markets) | Unlimited (paper) |

---

## Security Checklist

Before going to production:

- [ ] All tables have RLS enabled
- [ ] RLS policies restrict access to owner's data
- [ ] Auth trigger creates user profile on signup
- [ ] SMTP configured for email verification
- [ ] Strong passwords for database
- [ ] API keys stored as secrets (not in code)
- [ ] CORS configured for your domains
- [ ] Rate limiting configured
- [ ] SSL/TLS enabled
- [ ] Backups configured

---

## Verification Steps

After setup, verify each component:

### 1. Database

```sql
-- Check tables exist
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public';

-- Check RLS is enabled
SELECT tablename, rowsecurity FROM pg_tables 
WHERE schemaname = 'public';
```

### 2. Authentication

```bash
# Test signup
curl -X POST "https://YOUR_PROJECT.supabase.co/auth/v1/signup" \
  -H "apikey: YOUR_ANON_KEY" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"testpass123"}'
```

### 3. Edge Functions

```bash
# Test market-data function
curl "https://YOUR_PROJECT.supabase.co/functions/v1/market-data" \
  -H "Authorization: Bearer YOUR_ANON_KEY" \
  -H "Content-Type: application/json" \
  -d '{"symbol":"AAPL"}'
```

---

## Troubleshooting

### "relation does not exist"
Run migrations in order. Some depend on earlier migrations.

### "permission denied for schema public"
Grant permissions:
```sql
GRANT ALL ON SCHEMA public TO postgres, anon, authenticated, service_role;
```

### Edge functions not working
1. Check function is deployed: Dashboard → Edge Functions
2. Check secrets are set: Dashboard → Edge Functions → Secrets
3. Check logs: Dashboard → Edge Functions → Logs

### Auth not working
1. Verify Site URL is set correctly
2. Check redirect URLs include your domain
3. Ensure email templates are configured

---

## Need More Help?

- 📖 Full documentation: [README.md](./README.md)
- 🔄 Backend transition: [BACKEND_TRANSITION_GUIDE.md](./BACKEND_TRANSITION_GUIDE.md)
- 📚 Supabase docs: [docs.supabase.com](https://docs.supabase.com)
- 💬 Supabase Discord: [discord.supabase.com](https://discord.supabase.com)
