# Backend Transition Guide

This comprehensive guide explains how to transition from Lovable Cloud to other backend providers or self-hosted solutions.

## Table of Contents

1. [Overview](#overview)
2. [Supported Backends](#supported-backends)
3. [Migration Strategies](#migration-strategies)
4. [Self-Hosted Supabase](#self-hosted-supabase)
5. [Alternative Backends](#alternative-backends)
6. [Data Migration](#data-migration)
7. [Edge Function Migration](#edge-function-migration)
8. [Authentication Migration](#authentication-migration)
9. [Environment Variables](#environment-variables)
10. [Testing Your Migration](#testing-your-migration)

---

## Overview

This application is built with a backend-agnostic architecture where possible. The core database operations use standard PostgreSQL, and the authentication layer uses industry-standard patterns.

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (React)                        │
├─────────────────────────────────────────────────────────────┤
│                   Supabase Client SDK                        │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────────┐ │
│  │   Auth   │  │ Database │  │ Storage  │  │  Functions  │ │
│  │  (GoTrue)│  │(Postgres)│  │  (S3)    │  │   (Deno)    │ │
│  └──────────┘  └──────────┘  └──────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## Supported Backends

### Primary: Supabase (Self-Hosted or Cloud)
- **Best for**: Full feature parity, minimal code changes
- **Effort**: Low
- **Documentation**: See [Self-Hosted Supabase](#self-hosted-supabase)

### Alternative: Firebase + PostgreSQL
- **Best for**: Google Cloud ecosystem
- **Effort**: Medium
- **Changes required**: Auth layer, storage layer

### Alternative: AWS (Cognito + RDS + S3 + Lambda)
- **Best for**: Enterprise, AWS ecosystem
- **Effort**: High
- **Changes required**: All layers need adaptation

### Alternative: Custom Node.js Backend
- **Best for**: Full control, specific requirements
- **Effort**: High
- **Changes required**: Complete backend rewrite

---

## Migration Strategies

### Strategy 1: Direct Supabase Migration (Recommended)

**When to use**: You want to keep the same functionality with minimal changes.

1. Set up Supabase instance (self-hosted or supabase.com)
2. Run migration SQL files in order
3. Update environment variables
4. Regenerate TypeScript types
5. Test all functionality

### Strategy 2: Database-Only Migration

**When to use**: You want to use a different auth provider but keep PostgreSQL.

1. Export database schema and data
2. Set up new PostgreSQL instance
3. Import schema (modify auth references)
4. Implement new auth layer
5. Update database client code

### Strategy 3: Complete Backend Rewrite

**When to use**: Moving to a completely different stack.

1. Map current schema to new database
2. Implement new API endpoints
3. Create new auth system
4. Build new storage solution
5. Rewrite frontend integration layer

---

## Self-Hosted Supabase

### Option A: Docker Compose (Local/VPS)

```bash
# Clone Supabase repo
git clone --depth 1 https://github.com/supabase/supabase
cd supabase/docker

# Copy environment file
cp .env.example .env

# Generate secure keys
# Edit .env with your configuration

# Start services
docker compose up -d

# Run migrations
docker exec -i supabase-db psql -U postgres -d postgres < migrations/001_initial_schema.sql
docker exec -i supabase-db psql -U postgres -d postgres < migrations/002_storage_buckets.sql
docker exec -i supabase-db psql -U postgres -d postgres < migrations/003_auth_config.sql
docker exec -i supabase-db psql -U postgres -d postgres < migrations/004_indexes.sql
docker exec -i supabase-db psql -U postgres -d postgres < migrations/005_custom_notification_rules.sql
docker exec -i supabase-db psql -U postgres -d postgres < migrations/006_add_profile_fields.sql
```

### Option B: Kubernetes

See the [Supabase Kubernetes Helm Chart](https://github.com/supabase-community/supabase-kubernetes)

### Option C: Supabase.com (Managed)

1. Create project at [supabase.com](https://supabase.com)
2. Run migrations via SQL Editor
3. Update environment variables

---

## Alternative Backends

### Firebase Migration

#### Database Layer
Replace Supabase client with Firebase Firestore or use Cloud SQL for PostgreSQL.

```typescript
// Before (Supabase)
import { supabase } from "@/integrations/supabase/client";
const { data } = await supabase.from('profiles').select('*');

// After (Firebase Firestore)
import { collection, getDocs } from 'firebase/firestore';
import { db } from '@/lib/firebase';
const snapshot = await getDocs(collection(db, 'profiles'));
const data = snapshot.docs.map(doc => doc.data());
```

#### Auth Layer
```typescript
// Before (Supabase)
const { user } = await supabase.auth.signInWithPassword({ email, password });

// After (Firebase)
import { signInWithEmailAndPassword } from 'firebase/auth';
const { user } = await signInWithEmailAndPassword(auth, email, password);
```

### AWS Migration

#### Required Services
- **Amazon Cognito**: User authentication
- **Amazon RDS**: PostgreSQL database
- **Amazon S3**: File storage
- **AWS Lambda**: Serverless functions
- **API Gateway**: REST/GraphQL API

#### Database Schema
The PostgreSQL schema is compatible with Amazon RDS. Remove Supabase-specific functions:
- Replace `auth.uid()` with application-level user ID checks
- Remove RLS policies (implement in API layer)
- Remove Supabase-specific triggers

---

## Data Migration

### Export from Supabase

```bash
# Using pg_dump
pg_dump "postgresql://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres" \
  --schema=public \
  --data-only \
  --file=data_export.sql

# Or export specific tables
pg_dump "postgresql://..." \
  --table=public.profiles \
  --table=public.holdings \
  --table=public.transactions \
  --data-only \
  --file=user_data.sql
```

### Import to New Database

```bash
# Standard PostgreSQL
psql -h localhost -U postgres -d your_database -f data_export.sql

# Amazon RDS
psql -h your-rds-instance.region.rds.amazonaws.com -U postgres -d your_database -f data_export.sql
```

### Data Transformation Script

For backends with different ID formats:

```javascript
// scripts/transform-data.js
const fs = require('fs');

const transformData = (data) => {
  return data.map(row => ({
    ...row,
    // Transform UUID to string ID if needed
    id: row.id.toString(),
    // Convert timestamp format
    created_at: new Date(row.created_at).toISOString(),
    // Map user_id to new auth system
    user_id: userIdMapping[row.user_id] || row.user_id,
  }));
};
```

---

## Edge Function Migration

### Current Edge Functions

| Function | Purpose | Dependencies |
|----------|---------|--------------|
| `market-data` | Fetch live market quotes | Alpaca/Polygon API |
| `trade-execution` | Execute trades via broker | Alpaca API |
| `plaid-link` | Banking connection | Plaid API |
| `snaptrade-link` | Brokerage connection | SnapTrade API |

### Migration to AWS Lambda

```javascript
// supabase/functions/market-data/index.ts → AWS Lambda

// Before (Deno)
Deno.serve(async (req) => {
  const { symbol } = await req.json();
  // ... logic
  return new Response(JSON.stringify(data));
});

// After (Node.js Lambda)
exports.handler = async (event) => {
  const { symbol } = JSON.parse(event.body);
  // ... logic
  return {
    statusCode: 200,
    body: JSON.stringify(data),
  };
};
```

### Migration to Vercel/Netlify Functions

```javascript
// api/market-data.js (Vercel)
export default async function handler(req, res) {
  const { symbol } = req.body;
  // ... logic
  res.status(200).json(data);
}
```

---

## Authentication Migration

### User Data Structure

```typescript
interface User {
  id: string;           // Unique identifier
  email: string;        // User email
  email_verified: boolean;
  created_at: string;   // ISO timestamp
  raw_user_meta_data: {
    full_name?: string;
    avatar_url?: string;
  };
}
```

### Migration Steps

1. **Export Users**
   ```sql
   SELECT id, email, created_at, raw_user_meta_data 
   FROM auth.users;
   ```

2. **Password Handling**
   - Users must reset passwords on new system
   - Or use magic link/passwordless auth during transition

3. **Update Auth Hook**
   ```typescript
   // src/hooks/useAuth.tsx - abstract the auth provider
   interface AuthProvider {
     signIn(email: string, password: string): Promise<User>;
     signUp(email: string, password: string): Promise<User>;
     signOut(): Promise<void>;
     getUser(): User | null;
   }
   ```

---

## Environment Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `VITE_SUPABASE_URL` | Backend API URL | `https://api.example.com` |
| `VITE_SUPABASE_PUBLISHABLE_KEY` | Public API key | `pk_...` |
| `VITE_SUPABASE_PROJECT_ID` | Project identifier | `my-project` |

### Backend Secrets (Edge Functions)

| Secret | Service | Required For |
|--------|---------|--------------|
| `PLAID_CLIENT_ID` | Plaid | Banking integration |
| `PLAID_SECRET` | Plaid | Banking integration |
| `SNAPTRADE_CLIENT_ID` | SnapTrade | Brokerage integration |
| `SNAPTRADE_CONSUMER_KEY` | SnapTrade | Brokerage integration |
| `ALPACA_API_KEY` | Alpaca | Trading, market data |
| `ALPACA_API_SECRET` | Alpaca | Trading, market data |
| `POLYGON_API_KEY` | Polygon.io | Market data |

---

## Testing Your Migration

### Checklist

- [ ] **Authentication**
  - [ ] User can sign up
  - [ ] User can sign in
  - [ ] User can sign out
  - [ ] Password reset works
  - [ ] Session persists on refresh

- [ ] **Database Operations**
  - [ ] Profile loads correctly
  - [ ] Holdings display
  - [ ] Transactions load
  - [ ] Net worth calculates
  - [ ] Goals save and load

- [ ] **Edge Functions**
  - [ ] Market data fetches
  - [ ] Order execution works
  - [ ] Plaid connection works
  - [ ] SnapTrade connection works

- [ ] **Storage**
  - [ ] Avatar upload works
  - [ ] Document upload works
  - [ ] Files download correctly

### Test Script

```bash
#!/bin/bash
# test-migration.sh

echo "Testing authentication..."
curl -X POST "$API_URL/auth/v1/signup" \
  -H "apikey: $ANON_KEY" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"testpass123"}'

echo "Testing database..."
curl "$API_URL/rest/v1/profiles?select=*" \
  -H "apikey: $ANON_KEY" \
  -H "Authorization: Bearer $ACCESS_TOKEN"

echo "Testing edge function..."
curl "$API_URL/functions/v1/market-data" \
  -H "Authorization: Bearer $ANON_KEY" \
  -H "Content-Type: application/json" \
  -d '{"symbol":"AAPL"}'
```

---

## Rollback Plan

If migration fails:

1. **Keep Original Running**: Don't shut down Lovable Cloud until fully tested
2. **DNS Switchback**: Point domain back to original
3. **Data Sync**: Re-sync any data created during failed migration
4. **Document Issues**: Log what failed for next attempt

---

## Support Resources

- **Supabase Self-Hosting**: [docs.supabase.com/guides/self-hosting](https://docs.supabase.com/guides/self-hosting)
- **PostgreSQL Documentation**: [postgresql.org/docs](https://www.postgresql.org/docs/)
- **Deno Deploy (Edge Functions)**: [deno.com/deploy](https://deno.com/deploy)
- **Lovable Documentation**: [docs.lovable.dev](https://docs.lovable.dev)
