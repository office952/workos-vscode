# 2026-08-02 — U7 AppShell role navigation + production home

## Status

```text
U7 = PASS WITH DOCUMENTED PREEXISTING WARNINGS
REMOTE = UNCHANGED (a74912c7)
NO PUSH
Platform Profitability = NOT READY
Production Ready = NU
```

## Scope

Role-aware AppShell IA, canonical Atelier (`/shop-floor`), role homes, UI path guard, day/dark evidence. No F7 / Pricing / Employee Mobile / Execution Detail redesign.

## Initial identity

`C:\w\psiso` @ `a74912c7` = remote; ahead 0; stash `wip-employee-unrelated` intact.

## Architecture readback

U6 scorecard drives U7 priority. F6 service-level truth unchanged. Docs define boundaries; runtime + QA define progress.

## Production-home decision

`CANONICAL_PRODUCTION_HOME = /shop-floor` (Atelier). Control demoted to Management.

## Expected / changed files

- `frontend/src/lib/shellNavigation.ts` (+ tests)
- `frontend/src/lib/rbac.ts`
- `frontend/src/lib/executionFlowUi.ts`
- `frontend/src/components/workos/AppShell.tsx`
- `frontend/src/components/workos/RoleHomeRedirect.tsx` (new)
- `frontend/src/components/workos/ShellPathGuard.tsx` (new)
- `frontend/src/App.tsx`, `Index.tsx`, `ShopFloor.tsx`
- `frontend/src/contexts/AuthContext.tsx` (DEV role override for proof)
- `docs/qa/workos-u7-appshell-role-navigation-production-home-v1/*`

## Tests / runtime

63 targeted FE tests green; tsc clean; screenshots under `screenshots/{day,dark,roles,states}`; baseline 973019 hash unchanged.

## Next

- Functional: Owner A vs B (service-level vs product-linked pilot)
- UI: compact Shop Floor chrome / breadcrumb Atelier wording (optional); not another home fight
- Employee Mobile: final-final

## Direction

~72/100%
