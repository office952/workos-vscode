## TASK

RETIRE_LEGACY_INTAKE_DETAIL_ROUTE_AND_FORCE_INTAKE_V6_V1

## HEAD before work

- `7bc1c7c`

## Safety state

- `git status -sb`: clean tracked worktree; no staged files
- `git diff --cached --name-only`: empty
- `git status --short --untracked-files=no`: empty
- `git diff --check`: clean before edits

## Root cause

- The legacy route [frontend/src/pages/IntakeLegacyRoute.tsx](c:/Users/offic/workos_app_vs/frontend/src/pages/IntakeLegacyRoute.tsx) still rendered `IntakeDetail` for non-volumetric requests.
- The active navigation helper [frontend/src/lib/volumetricIntakeRoute.ts](c:/Users/offic/workos_app_vs/frontend/src/lib/volumetricIntakeRoute.ts) only routed some requests to Intake V6, based on confirmed template / product family, so requests like logo or non-volumetric families could still end up on `/intake/:id`.
- `/intake` request actions in [frontend/src/pages/WorkIntake.tsx](c:/Users/offic/workos_app_vs/frontend/src/pages/WorkIntake.tsx) use `resolveIntakeEditPath(...)`, so the helper was the active entry point into the old route.

## Route/component found

- Legacy route owner:
  - [frontend/src/App.tsx](c:/Users/offic/workos_app_vs/frontend/src/App.tsx)
  - route: `/intake/:id`
- Old component previously rendered:
  - [frontend/src/pages/IntakeLegacyRoute.tsx](c:/Users/offic/workos_app_vs/frontend/src/pages/IntakeLegacyRoute.tsx)
  - fallback: `IntakeDetail`
- Request action from `/intake`:
  - [frontend/src/pages/WorkIntake.tsx](c:/Users/offic/workos_app_vs/frontend/src/pages/WorkIntake.tsx)
  - button `work-intake-primary-edit`

## Fix behavior

- `resolveIntakeEditPath(...)` now routes all active intake request keys (`IR-*`, `WI-*`) to Intake V6:
  - `/intake-v6/{workspaceId or requestId}/operator`
- `IntakeLegacyRoute` is now retired from active rendering and always redirects to the Intake V6 operator route.
- The old label `Instrumentează Comanda` is no longer used for active intake edits; active edit label is `Deschide Intake V6`.

## Files changed

- [frontend/src/lib/volumetricIntakeRoute.ts](c:/Users/offic/workos_app_vs/frontend/src/lib/volumetricIntakeRoute.ts)
- [frontend/src/lib/volumetricIntakeRoute.test.ts](c:/Users/offic/workos_app_vs/frontend/src/lib/volumetricIntakeRoute.test.ts)
- [frontend/src/pages/IntakeLegacyRoute.tsx](c:/Users/offic/workos_app_vs/frontend/src/pages/IntakeLegacyRoute.tsx)
- [frontend/src/pages/IntakeLegacyRoute.test.tsx](c:/Users/offic/workos_app_vs/frontend/src/pages/IntakeLegacyRoute.test.tsx)
- [frontend/src/pages/WorkIntake.routing.test.tsx](c:/Users/offic/workos_app_vs/frontend/src/pages/WorkIntake.routing.test.tsx)
- [docs/worklog/realignment/2026-07-07_retire_legacy_intake_detail_route_v1.md](c:/Users/offic/workos_app_vs/docs/worklog/realignment/2026-07-07_retire_legacy_intake_detail_route_v1.md)

## Tests run

- `pnpm.cmd -C "c:\Users\offic\workos_app_vs\frontend" exec vitest run src/pages/WorkIntake.routing.test.tsx src/pages/IntakeLegacyRoute.test.tsx src/lib/volumetricIntakeRoute.test.ts --reporter=verbose`
  - PASS
- `git diff --check`
  - PASS

## Visual verification

- Attempted `/intake` runtime verification, but backend live data for Work Intake was unavailable in browser at audit time (`Network Error` / `ERR_CONNECTION_REFUSED`).
- Confirmed through focused route tests that:
  - direct `/intake/:id` no longer renders old legacy form
  - request action path resolves to Intake V6
- Additional live check recommended when backend is available:
  - `KING ADVERTISER / IR-MRAO4SCA`

## Forbidden scope confirmation

- No Pricing changes
- No Quote/Order changes
- No Execution changes
- No ProductAggregate / TaskGraph / ExecutionPlan changes
- No DB / seed / migration work
- No Logo root activation
- No ACP root activation
- No Image Analyzer runtime changes

## Next audit recommendation

- `WORKOS_E2E_REGRESSION_SOURCE_CONTRADICTION_AUDIT_V1`