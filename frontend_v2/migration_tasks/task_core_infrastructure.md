# Task: Frontend Core Infrastructure (Phase 2)

## Context
This phase establishes the foundational communication layer between `frontend_v2` and the Python FastAPI backend. It involves decoupling the application from the legacy Supabase Auth client and implementing a standard JWT-based authentication flow.

## Goal
Implement the API client, migrate the `useAuth` hook, and update the Login/Register UI to function with the new backend.

## Todo List

### Configuration & Base Implementation
- [x] **Configure Environment**: Set `VITE_API_URL` and `VITE_USE_MOCKS` in `.env.local`. <!-- id: 1 -->
- [x] **Implement API Client**: Create `src/lib/api.ts` with:
    - `fetch` wrapper.
    - Automatic `Authorization: Bearer <token>` header injection.
    - Global error handling (401 Auto-logout). <!-- id: 2 -->

### Authentication Logic (Migration)
- [x] **Migrate useAuth.tsx**: Rewrite the hook to:
    - Remove `@supabase/supabase-js`.
    - Use `api.post("/auth/login")` for `signIn`.
    - Use `api.post("/auth/register")` for `signUp`.
    - Persist user session to `localStorage`. <!-- id: 3 -->

### Authentication UI Integration
- [x] **Update Auth.tsx**: 
    - Modify form handlers to expect `{ error }` return type from new `useAuth`.
    - Remove any Supabase-specific types (`User`, `Session`) if directly imported.
    - Ensure error messages are displayed correctly. <!-- id: 4 -->

### Verification
- [ ] **Verify Registration**: Create a new user account via the UI.
- [ ] **Verify Login**: Log in with credentials and confirm token storage in `localStorage`.
- [ ] **Verify Persistence**: Reload page and ensure session remains active.

## References
- **Completed API Client**: [api.ts](file:///c:/Users/skyfr/Documents/day-trading-options-tool/frontend_v2/src/lib/api.ts)
- **Migrated Hook**: [useAuth.tsx](file:///c:/Users/skyfr/Documents/day-trading-options-tool/frontend_v2/src/hooks/useAuth.tsx)
