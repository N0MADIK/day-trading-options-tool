# Task: Frontend Component Migration (Phase 3)

## Context
This project is part of migrating the `frontend_v2` application (formerly `finance-flow`) from a serverless/Supabase architecture to a Python FastAPI backend (`day-trading-options-tool/backend`).
The Core Infrastructure (API Client, Auth Hook) has been completed. The goal of this phase is to update the UI components to fetch data from the new backend API endpoints instead of Supabase or Mock Data.

## Goal
Replace all remaining Supabase/Mock data calls in feature pages with `api.ts` calls to the FastAPI backend.

## Todo List

### Authentication UI
- [ ] **Update Auth.tsx**: Refactor `handleSignIn` and `handleSignUp` to handle the simple `{ error }` response from the updated `useAuth` hook. Remove Supabase-specific error parsing if present. <!-- id: 1 -->

### Dashboard & Financial Overview
- [ ] **Migrate Dashboard.tsx**:
    - Replace mock net worth data with `GET /api/v1/net-worth/summary`.
    - Ensure loading states are handled.
- [ ] **Migrate FinancialBreakdown.tsx**:
    - Fetch history from `GET /api/v1/net-worth/history`.

### Connected Accounts
- [ ] **Migrate Connections.tsx**:
    - Fetch installed integrations from `GET /api/v1/connected-accounts` (or similar endpoint for integrations).
- [ ] **Migrate Account.tsx / AccountDetail.tsx**:
    - Fetch user's connected accounts list.
    - Display real balance data.

### Settings & User Profile
- [ ] **Migrate Settings.tsx**:
    - Fetch user profile from `GET /api/v1/profiles/me`.
    - Allow profile updates (PUT).
- [ ] **Migrate CustomNotifications.tsx**:
    - List rules from `GET /api/v1/custom-notification-rules`.
    - Implement Create/Delete/Update using proper API endpoints.

### Market Data
- [ ] **Migrate MarketScanner.tsx**:
    - Connect to `GET /api/v1/market/*` endpoints to replace mock tickers.

## References
- Backend URL: `http://localhost:8000/api/v1` (configured in `.env`)
- API Client: `src/lib/api.ts`
- Auth Hook: `src/hooks/useAuth.tsx`
