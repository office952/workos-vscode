# 2026-07-17 — UI-TRUTH-01C

## Objective

Implement failure, stale, retry, and drill-down states for runtime health UI. Bounded Dashboard truth cleanup. Preserve Control Center, Wave 7, UTF-8, Modules poller.

## Repository gate

- Branch: `feature/product-system-active-path-isolation-v1`
- Expected HEAD at start: `d845670` (Control Center V1)
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

## Status

**IN IMPLEMENTATION** → closure recorded after PASS.

## Architecture (planned)

- Reuse `useRuntimeHealth` + `RuntimeStatusSummary`
- New `RuntimeStatusDetails` for drill-down
- Extend `EnvironmentBanner` with refresh / retry / details
- Enable diagnostics fetch with 403 stop-loop
- Dashboard: rename Live; AppShell: hide mock critical unless `isMockEnabled()`
