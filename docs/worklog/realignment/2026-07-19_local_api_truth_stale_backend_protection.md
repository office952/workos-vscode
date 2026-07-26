# Local API truth and stale backend protection

- **Date:** 2026-07-19
- **Branch:** `feature/product-system-active-path-isolation-v1`
- **HEAD initial:** `bf2df42`
- **Verdict:** PASS

## Ports found (pre-flight)

| Port | Role |
|------|------|
| 3000 | Vite FE (intermittent during proof) |
| 8001 | Ghost/stale WorkOS (FinishSetup props=49, no `segmented_background`, no local-compatibility) |
| 8002 | Current-code WorkOS (props=51, local-compatibility COMPATIBLE) |

## Root cause

FE could default/direct to a healthy but stale backend. Stale OpenAPI accepted finish PUTs while stripping unknown fields → silent truth loss.

## Mechanism chosen

1. Public BE `GET /api/v1/system/local-compatibility` (no DB) with contract + capabilities.
2. DEV FE probe at boot + Romanian fail-loud banner.
3. DEV fetch write guard blocks mutating `/api` calls when incompatible/unavailable.
4. DEV API base: explicit `VITE_API_BASE_URL` wins; else same-origin proxy (no hardcoded ghost port).
5. Dev scripts sync `VITE_API_BASE_URL` to configured backend URL (never clear explicit values).
6. `npm run diag:local-listeners` inventories PIDs/ports/compat (never kills).

## Runtime proof

| Case | Evidence |
|------|----------|
| A correct `:8002` | compat JSON + banner absent + CASE 1 segmented E2E PASS |
| B stale `:8001` | HTTP 404 on local-compatibility + banner + write blocked |
| C unavailable | banner "indisponibil" + write blocked |

Screenshots: `docs/qa/local-api-truth-stale-backend-2026-07-19/screenshots/`

## Tests

- `pytest tests/test_system_local_compatibility.py tests/test_system_version.py` → pass
- vitest config/localApi/banner → pass
- Playwright CASE 1 segmented live → pass

## Next

Optional: inject `WORKOS_WORKTREE_FINGERPRINT` for multi-checkout identity beyond git SHA.
