# client/AGENTS.md

# StockBridge Frontend — Rules

## Implementation Order (Never Skip Layers)

types → constants → hooks → components → containers → views → pages → routes

## Layer Rules

- Pages: under 30 lines, wrap one view, no hooks, no logic, no config
- Layouts: never hardcode data — receive via props only
- Routes: URL mappings only — no nav config, no helpers
- Config: lives in features/constants/ not routes/ or containers/

## Design System

- Carbon components only — no raw HTML equivalents
- No hardcoded colors, spacing, or type — tokens only
- No inline SVG — SVGs in src/assets/icons/ only
- Atoms before features — if Carbon doesn't have it, add to design-system first

## State

- JWT never in localStorage or sessionStorage — authStore only
- authStore: NO persist middleware
- wizardStore and grnSessionStore: sessionStorage persist only
- Server state in React Query — not Zustand

## Testing

- All tests under client/tests/ — never co-located in src/
- Every component handles 4 states: loading, empty, error, success
- Page Object Model for all E2E tests

## Process

- Read all relevant files before editing anything
- Implement change completely before writing tests
- Run pnpm fix after every session
- Role-aware UI via NAV_CONFIG not if-else in components
