# Task: Cleanup and Verification (Phase 4)

## Context
Use this task list after completing the Component Migration (Phase 3). This phase ensures that the `frontend_v2` application is fully decoupled from Supabase (unless strictly necessary) and that the endpoint integration is robust.

## Goal
Remove legacy code, verify authentication flows, and ensure the "Mock Data" toggle works as expected.

## Todo List

### Legacy Cleanup
- [ ] **Remove Supabase Client**: Delete `src/integrations/supabase` directory if no longer used.
- [ ] **Audit Imports**: Search globally for `@supabase/supabase-js` and ensure no component imports it directly.
- [ ] **Remove Unused Hooks**: If `useMockData.tsx` is no longer used by any active component (and we decided not to keep it for fallbacks), remove it. *Note: Implementation plan says to RETAIN it for testing, so ensure it is just decoupled from main flow.*

### Mock Data Verification
- [ ] **Verify Toggle**: 
    - Set `VITE_USE_MOCKS=true` in `.env`.
    - Restart dev server.
    - Verify app loads generic mock data without backend connection.
    - Set `VITE_USE_MOCKS=false`.
    - Verify app fails/loads real data.

### E2E Verification Checklist
- [ ] **Registration**: Create a new user account.
- [ ] **Login**: Log in with the new account. Check `localStorage` for `token`.
- [ ] **Connectivity**: Ensure "Connected Accounts" page loads without error (even if empty).
- [ ] **Notifications**: Create a custom notification rule and verify it appears in the list.
- [ ] **Logout**: Verify clicking Logout clears token and redirects to Auth.

## Future Steps
- [ ] **Production Build**: Run `npm run build` to ensure type safety and valid build.
- [ ] **Dockerize**: Update `frontend/Dockerfile` (or `frontend_v2/Dockerfile`) to include the new build steps and nginx config.
