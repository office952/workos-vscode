# 2026-07-17 — UI-TRUTH-01C

## Objective

Implement failure, stale, retry, and drill-down states for runtime health UI. Bounded Dashboard truth cleanup. Preserve Control Center, Wave 7, UTF-8, Modules poller.

## Repository gate

- Branch: `feature/product-system-active-path-isolation-v1`
- Start HEAD: `d845670` (Control Center V1)
- Unpause commit: `d81c5dd`
- Depends: UI-TRUTH-01B COMPLETE — PROVEN_V1

## Owner decision

```text
UI-TRUTH-01C = UNPAUSE
G1 LIVE BADGE = RENAME
G2 CRITICAL = HIDE
G3 MODULES HEALTH = KEEP
G4 DB TRUTH = CONSUME (existing contracts only)
IMPLEMENTARE = GO
```

## Architecture

- Reused `useRuntimeHealth` + `RuntimeStatusSummary` (01B)
- New `RuntimeStatusDetails` for drill-down
- `EnvironmentBanner` — refresh / stale badge / retry label / details toggle
- `fetchDiagnostics: true` with 403 stop-loop (no repeated forbidden polls)
- Public health failure ≠ diagnostics 403
- Dashboard: `Live` → `Date disponibile`
- Shell: `resolveShellCriticalCount(isMockEnabled(), …)` hides mock critical

## Files

- `frontend/src/hooks/useRuntimeHealth.ts` (+ tests)
- `frontend/src/lib/runtimeHealth.ts`
- `frontend/src/types/runtimeStatus.ts`
- `frontend/src/components/workos/RuntimeStatusSummary.ts` (+ tests)
- `frontend/src/components/workos/RuntimeStatusDetails.tsx` (+ tests)
- `frontend/src/components/workos/EnvironmentBanner.tsx` (+ tests)
- `frontend/src/lib/shellAlertTruth.ts` (+ tests)
- `frontend/src/App.tsx`
- `frontend/src/pages/Dashboard.tsx` (+ dataSource test)
- `docs/qa/.../ui_truth_01/terminology_matrix.json`
- Master STATUS / TASK_GRAPH

## Terminology

Reverifică starea · Stare învechită · Reîncearcă · Detalii stare sistem · Nu ai permisiune pentru diagnostice detaliate · Date disponibile · Baza de date confirmată / neverificată

## Tests

```text
vitest: useRuntimeHealth + RuntimeStatusSummary + EnvironmentBanner + RuntimeStatusDetails + shellAlertTruth + Dashboard.dataSource
42 passed
frontend build: PASS
```

## Live verification

| URL | Result |
|-----|--------|
| `/dashboard` | Date disponibile; no Live; no `N critical`; banner refresh+details |
| `/modules` | Spine intact; runtime Backend cu avertisment / DB neverificată (public) |
| Banner vs Modules | Both warning backend; DB differs by source (diagnostics vs public) — explained, not contradiction |
| Details open | Detalii stare sistem region + tech strip |

## Negative-state proof (tests)

- Stale → Stare învechită, not positive
- Unavailable → critical + Reîncearcă + last-known
- Diagnostics 403 → distinct RO message; stop-loop on refresh

## Control Center impact

`NO NODE CHANGE` · ownership/spine unchanged · history still in evidence

## Governance impact

`NO POLICY CHANGE` · G13 intact · frontend remains projection

## Remaining gaps

- Modules poller not unified with banner (KEEP by owner)
- Alerts backend not implemented
- Diagnostics not available to unauthorized users (honest 403)
- UI-TRUTH-01D/E not started

## Commits

- `d81c5dd` — `docs(ui): approve ui-truth-01c implementation`
- (implementation) — `feat(ui): add runtime stale retry and details states`

## Status

`UI-TRUTH-01C = COMPLETE — PROVEN_V1`
