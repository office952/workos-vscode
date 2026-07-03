# WorkOS Frontend

React/Vite operator UI for WorkOS. **Start with the root docs:** [`../README.md`](../README.md) and [`../AGENTS.md`](../AGENTS.md).

## Stack

- React 18, TypeScript, Vite
- shadcn/ui + Tailwind CSS (`@/components/ui`)
- TanStack Query, React Router
- Vitest (unit), Playwright (E2E)

## Key areas

| Area | Path / route |
|------|----------------|
| WorkIntake V2 | `src/components/workos/workIntakeV2/`, route `/intake-v2/:id` |
| QuoteWizard | `src/components/workos/QuoteWizard*`, volumetric finish display |
| ProductSystem | `/product-system` |
| Color registry (RAL / Oracal) | `src/lib/colorRegistry/` |

Active template in V2: **`TPL-VOLUMETRIC-LETTERS`**.

## Commands

From `frontend/` (requires [pnpm](https://pnpm.io) 8.x):

```bash
pnpm install
pnpm run dev          # http://127.0.0.1:3000 — proxies /api → backend :8000
pnpm run validate     # lint + typecheck + build
pnpm run test         # Vitest
pnpm run test:e2e:workintake-finish   # Playwright finish smoke (stack must be running)
```

From repo root:

```bash
npm run validate:frontend
npm run test:frontend
npm run test:e2e:workintake-finish
```

E2E setup: seed via `backend/scripts/seed_commercial_e2e_fixture.py` — see [`../docs/qa/BUILD_COMMERCIAL_E2E_FIXTURE.md`](../docs/qa/BUILD_COMMERCIAL_E2E_FIXTURE.md).

## Layout

```txt
src/
  App.tsx              routes
  components/workos/   operator flows
  lib/                 shared domain helpers (color registry, intake spec, finish display)
  pages/               route entry components
e2e/                   Playwright specs + helpers
```

Path alias `@/` → `src/`.
