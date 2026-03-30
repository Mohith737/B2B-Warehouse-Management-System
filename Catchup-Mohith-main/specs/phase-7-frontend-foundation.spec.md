# specs/phase-7-frontend-foundation.spec.md
# Phase 7 — Frontend Foundation Spec

## Purpose
This phase builds the complete frontend foundation that every other
frontend phase depends on. Nothing feature-specific is built here.
The output is a fully configured, working shell: auth works, routing
works, the sidebar renders correctly per role, all design tokens are
set, and every atom component is built and tested. Phase 8 drops
features into this shell without touching the foundation.

If this phase is done wrong, every subsequent phase pays the price.
Do it right once.

## Scope

### In Scope
frontend/
  vite.config.ts
  index.html
  tsconfig.json
  package.json
  src/
    main.tsx
    App.tsx
    styles/
      globals.scss
      tokens.scss
      overrides.scss
    lib/
      queryClient.ts
      axiosClient.ts
      constants.ts
    stores/
      authStore.ts
      uiStore.ts
      wizardStore.ts
      grnSessionStore.ts
    hooks/
      useAuth.ts
      useNetworkStatus.ts
      useToast.ts
    router/
      index.tsx
      ProtectedRoute.tsx
      RoleRoute.tsx
    components/
      atoms/
        StatusBadge.tsx
        FormInput.tsx
        EmptyState.tsx
        LoadingSkeleton.tsx
        PageTitle.tsx
        ConfirmationBanner.tsx
      layout/
        AppShell.tsx
        Sidebar.tsx
        TopBar.tsx
        sidebarConfig.ts
      auth/
        LoginPage.tsx
        UnauthorizedPage.tsx
    tests/
      atoms/
        StatusBadge.test.tsx
        EmptyState.test.tsx
        LoadingSkeleton.test.tsx
      stores/
        authStore.test.ts
        uiStore.test.ts
      hooks/
        useAuth.test.ts

### Out of Scope
Any feature pages (products, suppliers, POs, GRN, dashboard).
Those are Phase 8 and 9.

## Acceptance Criteria

1.  `npm run dev` starts without errors
2.  `npm run build` produces a clean production build
3.  `npm run lint` passes with zero warnings
4.  `npm test` passes all unit tests
5.  Login page renders, submits credentials to POST /auth/login,
    stores accessToken in authStore (memory only, not localStorage)
6.  After login, user is redirected to role-appropriate default page
7.  Accessing a protected route while unauthenticated redirects to
    /login with the original path saved for post-login redirect
8.  Accessing a route unauthorized for the user's role renders
    UnauthorizedPage not a blank screen
9.  Sidebar renders only nav items the current role can access
10. Sidebar items are driven by sidebarConfig.ts not if-else chains
11. Logout clears authStore, clears sessionStorage, calls queryClient
    .clear(), redirects to /login
12. Toast system shows success/error toasts, deduplicates identical
    messages, never holds more than 3 toasts at once
13. StatusBadge renders correct Carbon Tag variant for all domain
    statuses: PO statuses, GRN statuses, stock levels, tier levels
14. All atoms handle their required states without crashing
15. useNetworkStatus hook disables mutation buttons when offline
16. All unit tests pass
17. No hardcoded color values anywhere — Carbon tokens only
18. No raw HTML equivalents where Carbon components exist

## Tech Stack and Versions

```json
{
  "@carbon/react": "^1.x",
  "react": "^18.x",
  "react-dom": "^18.x",
  "react-router-dom": "^6.x",
  "@tanstack/react-query": "^5.x",
  "zustand": "^4.x",
  "axios": "^1.x",
  "sass": "^1.x",
  "typescript": "^5.x",
  "vite": "^5.x",
  "vitest": "^1.x",
  "@testing-library/react": "^14.x",
  "@testing-library/user-event": "^14.x"
}
```

## Project Structure

```
frontend/
  index.html
  vite.config.ts
  tsconfig.json
  tsconfig.node.json
  package.json
  .env.example
  src/
    main.tsx              — React root, QueryClientProvider, Router
    App.tsx               — Route definitions only
    styles/
      globals.scss        — Body reset, font loading
      tokens.scss         — CSS custom properties from Carbon tokens
      overrides.scss      — Carbon component overrides ONLY
    lib/
      queryClient.ts      — TanStack Query client configuration
      axiosClient.ts      — Axios instance with interceptors
      constants.ts        — API base URL, route paths, config values
    stores/               — Zustand stores
    hooks/                — Custom React hooks
    router/               — Route guards
    components/
      atoms/              — Smallest reusable UI units
      layout/             — AppShell, Sidebar, TopBar
      auth/               — Login and Unauthorized pages
```

## Environment Variables

```
VITE_API_BASE_URL=http://localhost:8000
VITE_ENVIRONMENT=development
VITE_ENABLE_DEV_TOOLS=true
```

## Auth Flow (Locked)

### Login
1. User submits email + password on LoginPage
2. POST /auth/login with credentials
3. On success: store accessToken in authStore (memory only)
4. Store user id, email, role in authStore
5. Redirect to role-default route (see Routing section)
6. Refresh token is stored in httpOnly cookie by the server —
   the frontend never touches it directly

### Token Refresh
1. axiosClient response interceptor catches 401
2. Calls POST /auth/refresh automatically
3. If refresh succeeds: update accessToken in authStore, retry
   the original request
4. If refresh fails: call authStore.logout(), redirect to /login

### Logout
1. User clicks logout in sidebar or TopBar
2. POST /auth/logout to blacklist the token
3. authStore.logout() — clears all auth state
4. queryClient.clear() — clears all cached queries
5. sessionStorage.clear() — clears wizard and GRN session state
6. Navigate to /login

### Token Storage (Locked — Never Change)
- accessToken: authStore in memory ONLY — never localStorage,
  never sessionStorage, never a cookie set by frontend
- Survives: tab focus changes, React re-renders
- Does NOT survive: page refresh (by design — forces re-auth)
- On refresh: axiosClient interceptor attempts token refresh via
  httpOnly cookie before forcing login

## Routing

### Route Definitions
```
/login                    — public, LoginPage
/unauthorized             — public, UnauthorizedPage
/                         — protected, redirects to role default
/products                 — all roles
/products/:id             — all roles
/suppliers                — manager, admin
/suppliers/:id            — manager, admin
/purchase-orders          — all roles
/purchase-orders/new      — manager, admin
/purchase-orders/:id      — all roles
/grns                     — all roles
/grns/new                 — all roles
/grns/:id                 — all roles
/dashboard                — all roles
/stock-ledger             — all roles
/backorders               — manager, admin
/admin/users              — admin only
/admin/system             — admin only
```

### Role Default Routes
- warehouse_staff → /dashboard
- procurement_manager → /dashboard
- admin → /dashboard

### ProtectedRoute
Checks authStore.isAuthenticated. If false redirect to
/login?redirect={current path}.

### RoleRoute
Accepts `allowedRoles: UserRole[]` prop. If user role not in list
render `<Navigate to="/unauthorized" />`.

## Sidebar Configuration

### sidebarConfig.ts — Locked Pattern
```typescript
export interface SidebarItem {
  label: string
  path: string
  icon: React.ComponentType
  allowedRoles: UserRole[]
  children?: SidebarItem[]
}

export const SIDEBAR_ITEMS: SidebarItem[] = [
  {
    label: 'Dashboard',
    path: '/dashboard',
    icon: Dashboard,
    allowedRoles: ['warehouse_staff', 'procurement_manager', 'admin'],
  },
  {
    label: 'Products',
    path: '/products',
    icon: Catalog,
    allowedRoles: ['warehouse_staff', 'procurement_manager', 'admin'],
  },
  {
    label: 'Suppliers',
    path: '/suppliers',
    icon: Partnership,
    allowedRoles: ['procurement_manager', 'admin'],
  },
  {
    label: 'Purchase Orders',
    path: '/purchase-orders',
    icon: Purchase,
    allowedRoles: ['warehouse_staff', 'procurement_manager', 'admin'],
  },
  {
    label: 'GRN',
    path: '/grns',
    icon: Receipt,
    allowedRoles: ['warehouse_staff', 'procurement_manager', 'admin'],
  },
  {
    label: 'Stock Ledger',
    path: '/stock-ledger',
    icon: DataTable,
    allowedRoles: ['warehouse_staff', 'procurement_manager', 'admin'],
  },
  {
    label: 'Backorders',
    path: '/backorders',
    icon: Warning,
    allowedRoles: ['procurement_manager', 'admin'],
  },
  {
    label: 'Admin',
    path: '/admin/users',
    icon: UserAdmin,
    allowedRoles: ['admin'],
    children: [
      { label: 'Users', path: '/admin/users', icon: User,
        allowedRoles: ['admin'] },
      { label: 'System', path: '/admin/system', icon: Settings,
        allowedRoles: ['admin'] },
    ],
  },
]
```

Sidebar component filters SIDEBAR_ITEMS by current user role.
Zero if-else chains. Zero role checks in JSX.

## Zustand Stores

### authStore (in-memory, no persistence)
```typescript
interface AuthState {
  userId: string | null
  email: string | null
  role: UserRole | null
  accessToken: string | null
  isAuthenticated: boolean
  login: (payload: LoginPayload) => void
  logout: () => void
  setAccessToken: (token: string) => void
}
```

### uiStore (in-memory, no persistence)
```typescript
interface UIState {
  sidebarOpen: boolean
  toasts: Toast[]
  setSidebarOpen: (open: boolean) => void
  addToast: (toast: ToastInput) => void
  removeToast: (id: string) => void
}

interface Toast {
  id: string
  kind: 'success' | 'error' | 'warning' | 'info'
  title: string
  subtitle?: string
}
```

Toast rules:
- Max 3 toasts at once — adding a 4th removes the oldest
- Deduplication: if identical title+kind exists, do not add again
- Auto-dismiss after 5 seconds for success and info
- Error and warning toasts persist until dismissed manually

### wizardStore (sessionStorage persistence)
```typescript
interface WizardState {
  currentStep: number
  supplierId: string | null
  supplierName: string | null
  lines: WizardLine[]
  notes: string
  setStep: (step: number) => void
  updateSupplier: (id: string, name: string) => void
  addLine: (line: WizardLine) => void
  removeLine: (index: number) => void
  updateLine: (index: number, line: Partial<WizardLine>) => void
  setNotes: (notes: string) => void
  resetWizard: () => void
}
```

### grnSessionStore (sessionStorage persistence)
```typescript
interface GRNSessionState {
  selectedPOId: string | null
  selectedPONumber: string | null
  scannedLines: ScannedLine[]
  sessionStarted: boolean
  addScannedLine: (line: ScannedLine) => void
  updateScannedLineQty: (index: number, qty: number) => void
  removeScannedLine: (index: number) => void
  resetSession: () => void
}
```

## React Query Configuration

```typescript
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 3,
      retryDelay: attemptIndex => Math.min(1000 * 2 ** attemptIndex, 30000),
      staleTime: 30_000,
      refetchOnWindowFocus: true,
      refetchIntervalInBackground: false,
    },
    mutations: {
      retry: 0,
    },
  },
})
```

Polling intervals per query (set at usage site not in defaultOptions):
- Dashboard: refetchInterval 30_000 when focused
- Product list: refetchInterval 60_000 when focused
- PO list: refetchInterval 60_000, refetchOnWindowFocus false
- Supplier list: refetchInterval 120_000, refetchOnWindowFocus false
- Stock ledger: no polling, on-demand only
- GRN session check: on mount only

## Axios Client

```typescript
// src/lib/axiosClient.ts
const axiosClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  withCredentials: true,  // required for httpOnly refresh cookie
  headers: { 'Content-Type': 'application/json' },
})

// Request interceptor: attach accessToken from authStore
axiosClient.interceptors.request.use(config => {
  const token = useAuthStore.getState().accessToken
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Response interceptor: handle 401 with token refresh
axiosClient.interceptors.response.use(
  response => response,
  async error => {
    if (error.response?.status === 401 && !error.config._retry) {
      error.config._retry = true
      try {
        const res = await axios.post('/auth/refresh',
          {}, { withCredentials: true })
        useAuthStore.getState().setAccessToken(res.data.data.access_token)
        return axiosClient(error.config)
      } catch {
        useAuthStore.getState().logout()
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)
```

## Atom Components

### StatusBadge
Single component for ALL domain statuses. Accepts `domain` and
`status` props. Returns Carbon `Tag` with correct type and label.

```typescript
interface StatusBadgeProps {
  domain: 'po' | 'grn' | 'stock' | 'tier' | 'backorder'
  status: string
  size?: 'sm' | 'md'
}
```

Status mappings (all locked):
- PO: draft→gray, submitted→blue, acknowledged→cyan,
  shipped→teal, received→green, closed→green, cancelled→red
- GRN: open→blue, completed→green
- Stock: out_of_stock→red, low_stock→orange, in_stock→green
- Tier: Silver→gray, Gold→yellow, Diamond→cyan
- Backorder: open→orange, fulfilled→green, cancelled→red

Never call Carbon Tag directly in feature components.
Always use StatusBadge.

### FormInput
Wrapper around Carbon TextInput with consistent error display.
Accepts all TextInput props plus `error?: string`.

### EmptyState
Role-aware empty state component.
```typescript
interface EmptyStateProps {
  title: string
  description: string
  action?: { label: string; onClick: () => void }
  icon?: React.ComponentType
}
```
Uses Carbon Tile with centered content. No raw div layouts.

### LoadingSkeleton
Wraps Carbon SkeletonText and SkeletonPlaceholder.
Accepts `variant: 'table' | 'card' | 'detail' | 'list'`.
Each variant renders the appropriate skeleton shape for its context.

### PageTitle
Renders Carbon Heading with optional breadcrumb.
```typescript
interface PageTitleProps {
  title: string
  breadcrumbs?: Array<{ label: string; href?: string }>
}
```

### ConfirmationBanner
Renders Carbon InlineNotification kind=info with two action buttons.
Used for wizard/GRN session restoration on page mount.

## Layout Components

### AppShell
Root layout. Renders TopBar + Sidebar + main content area.
Sidebar open/closed state from uiStore.sidebarOpen.
Uses Carbon UI Shell: Header, SideNav, Content.

### Sidebar
Reads SIDEBAR_ITEMS, filters by current user role, renders
Carbon SideNav items. Active item highlighted by current path.
No role logic in JSX — filtering done in a useSidebarItems hook.

### TopBar
Carbon Header with:
- StockBridge logo/name on left
- Sidebar toggle button
- User menu on right (email, role badge, logout)

## Login Page

Carbon Form layout. Email and password fields using Carbon
TextInput. Submit button using Carbon Button kind=primary.
Shows Carbon InlineLoading during submission.
On error shows Carbon InlineNotification kind=error.
No redirect loop if already authenticated — redirect to dashboard.

## Unauthorized Page

Not a blank screen. Full page with:
- Carbon Heading: "Access Restricted"
- Description explaining the user's role does not have access
- Carbon Button to go back or go to dashboard
- Shows what role the user has and what roles can access the page

## useNetworkStatus Hook

```typescript
function useNetworkStatus(): { isOnline: boolean }
```

Subscribes to window online/offline events.
Returns current network status.
Used in mutation hooks to disable submit buttons when offline.

## useToast Hook

```typescript
function useToast() {
  return {
    success: (title: string, subtitle?: string) => void
    error: (title: string, subtitle?: string) => void
    warning: (title: string, subtitle?: string) => void
    info: (title: string, subtitle?: string) => void
  }
}
```

Wrapper around uiStore.addToast with deduplication built in.

## useAuth Hook

```typescript
function useAuth() {
  return {
    user: { userId, email, role } | null
    isAuthenticated: boolean
    login: (credentials) => Promise<void>
    logout: () => Promise<void>
  }
}
```

Encapsulates all auth API calls and store updates.
Components never call authStore directly — always through useAuth.

## Test Cases

### StatusBadge.test.tsx
- renders correct Carbon Tag type for each PO status
- renders correct type for each GRN status
- renders correct type for stock levels
- renders correct type for tier levels
- unknown status renders gray tag without crashing

### EmptyState.test.tsx
- renders title and description
- renders action button when action prop provided
- does not render button when no action prop
- renders icon when provided

### LoadingSkeleton.test.tsx
- renders table variant without crashing
- renders card variant without crashing
- renders detail variant without crashing

### authStore.test.ts
- login sets all fields correctly
- logout clears all fields
- isAuthenticated true when accessToken set
- isAuthenticated false after logout
- token never written to localStorage

### uiStore.test.ts
- addToast adds to queue
- addToast with 4th toast removes oldest
- addToast deduplicates identical title+kind
- removeToast removes correct toast
- setSidebarOpen updates state

### useAuth.test.ts
- login calls POST /auth/login with correct payload
- login stores token in authStore not localStorage
- logout calls POST /auth/logout
- logout clears authStore and queryClient cache

## Implementation Notes

- Use `@carbon/react` imports only — never `carbon-components-react`
- Import Carbon icons from `@carbon/icons-react`
- All Carbon theme tokens accessed via CSS custom properties
  defined in tokens.scss — never hardcode hex values
- Use Carbon's `g10` theme (light) as default
- globals.scss imports Carbon styles:
  `@use '@carbon/react'`
- All component files are .tsx not .jsx
- All store files are .ts not .js
- Zustand persist middleware for sessionStorage stores:
  `import { persist, createJSONStorage } from 'zustand/middleware'`
  `storage: createJSONStorage(() => sessionStorage)`
- Dev tools panel (VITE_ENABLE_DEV_TOOLS=true) renders floating
  panel in bottom-right with invalidate/clear cache buttons
- Carbon SideNav requires wrapping in Theme provider with correct
  theme token — do not skip this or colors will be wrong
- axiosClient must have `withCredentials: true` — the refresh token
  is in an httpOnly cookie and will not be sent without this
