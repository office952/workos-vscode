# 2026-07-17 — UI-TRUTH-01B owner gates, unpause, and CORE implementation

## Objective

Unpause and implement UI-TRUTH-01B CORE: global environment banner reflects `useRuntimeHealth`, not auth-derived `LIVE / DB`.

## Repository gate

- Branch: `feature/product-system-active-path-isolation-v1`
- Start HEAD: `3c149ab` (Wave 7 OWNER_ACCEPTED)
- Runtime: `:3000` / `:8001`
- Closed preserved: Wave 7 · PostJobTruth · UTF-8/G13 · Aggregate task-contract

## Owner decision — APPROVED 2026-07-17

```text
UI-TRUTH-01B = UNPAUSE
G1 PAGINI = CORE
G2 TERMINOLOGIE = MATRIX
G3 CODURI TEHNICE = STRIP
G4 CONSOLIDARE = SUMMARY
DOCS-ONLY COMMIT = DA
IMPLEMENTARE = GO
```

## Root defect

`EnvironmentBanner` mapped `authState === authenticated` → green `LIVE / DB`, inventing backend/DB health from session.

## Runtime truth mapping

| Runtime state | Main Romanian text | Severity | Technical strip |
|---------------|--------------------|----------|-----------------|
| Loading | `Se verifică · Local · DB — se verifică` (env-dependent) | neutral | omitted if empty |
| Backend healthy + DB confirmed | `Local · Backend disponibil · Baza de date confirmată` | positive | status/env/t |
| Backend healthy + DB unverified | `… · Backend disponibil · DB neverificată` | warning | status/env/t |
| Backend warning (live default) | `Staging · Backend cu avertisment · DB neverificată` | warning | `status=warning` |
| Backend unavailable | `… · Backend indisponibil · DB necunoscută/neverificată` | critical | err=… |
| Stale | `… · Backend — stare învechită · …` | warning | `stale=true` |
| Demo | `Mod demo · Date demonstrative` | warning | optional |

Presentation owner: `RuntimeStatusSummary` (`buildRuntimeStatusSummary`).  
Fetch owner: `useRuntimeHealth` only (no second poller in banner).

## Implementation

| File | Role |
|------|------|
| `RuntimeStatusSummary.ts` | Matrix terminology + severity mapping |
| `EnvironmentBanner.tsx` | Hook wiring + strip UI |
| `*.test.ts(x)` | 19 focused tests |
| `terminology_matrix.json` | Minimal 01B label additions |
| Master STATUS/TASK_GRAPH | 01B COMPLETE — PROVEN_V1 (CORE) |

## Tests / build

```text
vitest run RuntimeStatusSummary.test.ts EnvironmentBanner.test.tsx → 19 passed
pnpm run build → PASS
```

## Live smoke (2026-07-17)

| URL | Banner | Severity | Tech strip | LIVE/DB |
|-----|--------|----------|------------|---------|
| `http://127.0.0.1:3000/orders` | Staging · Backend cu avertisment · DB neverificată | warning | status=warning · env=staging | absent |
| `http://127.0.0.1:3000/intake` | same | warning | same pattern | absent |
| `http://127.0.0.1:3000/modules` (Stare runtime) | same global strip; page modules **Neverificat** (empty public checks) | warning | same | absent — no Backend disponibil contradiction |

Env label `Staging` comes from `GET /api/v1/system/version` (`environment=staging`), not invented from auth.

## Modules / Governance

- Harta: **NO NODE CHANGE**; evidence row added for 01B.
- Guvernanță: **NO POLICY CHANGE** (G13 / Romanian-first / frontend projection already cover).

## Exclusions (deferred)

- Header green `Live` connection badge (separate from EnvironmentBanner)
- Mock header `N critical`
- Nav terminology (Work Intake / Product System EN)
- Post-Job EN title
- ModuleChain poller merge into shared hook (01C/01E)
- Diagnostics-gated DB confirm drill-down (01C)

## Commits

1. `docs(ui): approve ui-truth-01b unpause` — planning baseline
2. `feat(ui): render real runtime health banner` — implementation + closure

## Next

**UI-TRUTH-01C** — failure/stale/drill-down — not started.
