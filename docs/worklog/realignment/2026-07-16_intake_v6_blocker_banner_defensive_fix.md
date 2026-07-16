# 2026-07-16 — Intake V6 blocker banner defensive fix

## Root cause

`GET /api/v1/intake-v6/workspaces/{id}/runtime-capture-read-model` for non-offerable Logo root (`root.allowed=false`) returns fail-closed backbone-shaped blockers:

```json
{ "blocker_code": "LOGO_NOT_OFFERABLE", "severity": "blocked", "message": "...", "blocks": ["quote_preview", ...] }
```

Frontend helpers assumed nested `row.blockers: string[]` (runtime-capture field shape). Missing `blockers` → `TypeError: row.blockers is not iterable`, then `codes is not iterable` in diagnostic entry count → operator white-screen.

## Fix

Single normalization helper `asBlockerCodeList` in `intakeV6OperatorBlockerBannerDisplay.ts`:

- valid string arrays unchanged;
- `undefined` / `null` / non-array → `[]` (no invented codes).

Applied at:

- `collectRuntimeBlockerCodes` / planner collector;
- `buildReviewDiagnosticEntryCount` (same runtime shape consumer).

No backend/API/policy/Logo readiness changes.

## Tests

```text
vitest run
  intakeV6OperatorBlockerBannerDisplay.test.ts
  intakeV6ReviewDiagnosticEntryCount.test.ts
  IntakeV6ReviewOperatorBlockerBanner.test.tsx
→ 21 passed

pnpm run build → pass
```

## Visual smoke

- Workspace: `logo-blocker-banner-smoke-2026-07-16` (deleted after)
- URL: `http://127.0.0.1:3000/intake-v6/logo-blocker-banner-smoke-2026-07-16/operator`
- Configurare: Logo-only guard visible; page stayed interactive after 2.5s hold; `pageerrors: []`
- Evidence: `docs/qa/logo-only-live-smoke-2026-07-16/07_blocker_banner_fix_smoke.png`

## Impact

- `/modules`: **NO IMPACT**
- `/governance`: **NO UPDATE REQUIRED**

## Commit

`fix(intake): prevent blocker banner crash on partial runtime data`
