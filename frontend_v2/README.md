# Finance Dashboard (Frontend v2)

A comprehensive personal finance management application built with React, TypeScript, and a FastAPI backend.

## Tech Stack

- **Frontend**: React 18 + TypeScript + Vite
- **Styling**: Tailwind CSS + shadcn/ui components
- **State Management**: React Context + TanStack React Query
- **Backend**: FastAPI (JWT authentication, REST API)
- **Charts**: Recharts + Lightweight Charts

---

## Project Structure

```
src/
├── components/           # Reusable UI components
│   ├── ui/              # shadcn/ui base components (Button, Card, Dialog, etc.)
│   ├── layout/          # Layout components (AppLayout, AppSidebar)
│   ├── connections/     # Account connection components (CSVImport)
│   └── market/          # Market-related components (Charts, Indicators)
├── hooks/               # Custom React hooks
│   ├── useAuth.tsx      # Authentication context (JWT-based)
│   ├── useConnections.tsx # Account/holdings/transactions data
│   ├── useMockData.tsx  # Demo data toggle provider
│   ├── usePlaid.tsx     # Plaid API integration
│   └── useSnapTrade.tsx # SnapTrade API integration
├── pages/               # Route-level page components
├── lib/                 # Utility functions
│   ├── api.ts           # API client with JWT token handling
│   └── utils.ts         # General utilities
└── assets/              # Static assets (images, icons)
```

---

## Frontend Components

### Page Components (`src/pages/`)

Each page is a standalone route component that:
1. Uses hooks to fetch/manage data
2. Renders UI with shadcn/ui components
3. Handles user interactions

| Page | Purpose |
|------|---------|
| `Index.tsx` | Landing page / public home |
| `Dashboard.tsx` | Main dashboard with portfolio overview |
| `Connections.tsx` | Manage connected accounts & CSV imports |
| `FinancialBreakdown.tsx` | Detailed asset allocation & analytics |
| `MarketScanner.tsx` | Market data & technical analysis |
| `Account.tsx` | User profile management |
| `Settings.tsx` | Application settings |
| `Auth.tsx` | Login / signup forms |

### Layout Components (`src/components/layout/`)

- **`AppLayout.tsx`**: Main app wrapper with sidebar + content area
- **`AppSidebar.tsx`**: Navigation sidebar with links and demo data toggle

### UI Components (`src/components/ui/`)

Built on [shadcn/ui](https://ui.shadcn.com/), these are customizable primitives:
- Form inputs: `Button`, `Input`, `Select`, `Checkbox`, `Switch`
- Layout: `Card`, `Dialog`, `Sheet`, `Tabs`, `Accordion`
- Feedback: `Toast`, `Alert`, `Skeleton`, `Progress`
- Data: `Table`, `Badge`, `Avatar`

---

## Custom Hooks & API Patterns

### Authentication (`useAuth`)

Provides JWT-based authentication via React Context. Sessions are persisted to `localStorage`.

```tsx
import { useAuth } from '@/hooks/useAuth';

function MyComponent() {
  const { user, loading, signIn, signUp, signOut } = useAuth();
  
  if (loading) return <Spinner />;
  if (!user) return <LoginPrompt />;
  
  return <Dashboard user={user} />;
}
```

**Methods:**
- `signUp(email, password, fullName?)` - Register new user (auto-logs in on success)
- `signIn(email, password)` - Authenticate user, stores JWT token
- `signOut()` - Clear session from localStorage

### Data Connections (`useConnections`)

Manages connected accounts, holdings, and transactions.

```tsx
import { useConnections } from '@/hooks/useConnections';

function Portfolio() {
  const { 
    accounts,          // Connected financial accounts
    holdings,          // Investment positions
    transactions,      // Transaction history
    loading,
    totalNetWorth,     // Calculated total
    connectAccount,    // Link new account
    disconnectAccount, // Remove account
    syncAccount,       // Refresh account data
  } = useConnections();
  
  return (
    <div>
      <h2>Net Worth: ${totalNetWorth.toLocaleString()}</h2>
      {holdings.map(h => <HoldingCard key={h.id} holding={h} />)}
    </div>
  );
}
```

### Mock Data (`useMockData`)

Global toggle for displaying demo data across all charts and components.

```tsx
import { useMockData } from '@/hooks/useMockData';

function ChartComponent() {
  const { showMockData, MOCK_DATA } = useMockData();
  
  const chartData = showMockData ? MOCK_DATA.netWorthHistory : realData;
  
  return <LineChart data={chartData} />;
}
```

---

## API Call Patterns

All API calls use the `api` client from `@/lib/api.ts` with automatic JWT token injection.

### 1. Basic Query Structure

```tsx
import { api } from '@/lib/api';

const data = await api.get<MyType[]>('/endpoint');
```

### 2. Insert Data

```tsx
const newItem = await api.post<MyType>('/endpoint', {
  symbol: 'AAPL',
  quantity: 10,
  average_cost: 150.00,
});
```

### 3. Update Data

```tsx
const updated = await api.put<MyType>(`/endpoint/${id}`, {
  last_synced_at: new Date().toISOString(),
});
```

### 4. Delete Data

```tsx
await api.delete(`/endpoint/${id}`);
```

### 5. Authentication Endpoints

```tsx
// Login (OAuth2 password flow)
const { access_token } = await api.post<{ access_token: string }>(
  '/auth/login',
  new URLSearchParams({ username: email, password }).toString(),
  { skipAuth: true, headers: { 'Content-Type': 'application/x-www-form-urlencoded' } }
);
```

---

## Type Safety

All database types are auto-generated from the schema:

```tsx
import { Tables, TablesInsert, TablesUpdate } from '@/integrations/supabase/types';

type Holding = Tables<'holdings'>;        // Read type (full row)
type NewHolding = TablesInsert<'holdings'>; // Insert type
type HoldingUpdate = TablesUpdate<'holdings'>; // Update type
```

---

## Error Handling

Consistent error handling with user feedback:

```tsx
import { toast } from '@/hooks/use-toast';

try {
  const { data, error } = await supabase.from('table').select('*');
  if (error) throw error;
  
  toast({ title: 'Success', description: 'Data loaded' });
} catch (error: any) {
  console.error('Error:', error);
  toast({ 
    title: 'Error', 
    description: error.message || 'Something went wrong',
    variant: 'destructive' 
  });
}
```

---

## State Management

### Context Providers

```tsx
// In App.tsx
<AuthProvider>
  <MockDataProvider>
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  </MockDataProvider>
</AuthProvider>
```

### Hook Pattern

Custom hooks encapsulate:
1. State declarations (`useState`)
2. Side effects (`useEffect`)
3. Memoized callbacks (`useCallback`)
4. Data fetching logic

---

## Development

### Local Development

```bash
# Install dependencies
npm install

# Create environment file for local development
echo "VITE_API_URL=http://localhost:8420/api" > .env.local

# Start dev server (connects to local backend)
npm run dev
```

### Running with Docker

When running via docker-compose, the API URL is left empty and API calls go through the nginx proxy:

```bash
# From project root
docker compose up -d --build

# Frontend available at http://localhost:3000
# API calls proxied to backend via nginx
```

## Build

```bash
npm run build   # Build for production
npm run preview # Preview production build locally
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|--------|
| `VITE_API_URL` | Backend API base URL | `/api` (nginx proxy) |
| `VITE_USE_MOCKS` | Enable mock data mode | `false` |
