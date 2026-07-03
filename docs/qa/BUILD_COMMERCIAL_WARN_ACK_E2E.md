# BUILD-COMMERCIAL-WARN-ACK-E2E

**Date:** 2026-06-07  
**Build status:** **PASS**  
**Prior commits:**
- `43635cf` — volumetric commercial spine
- `717b4d7` — quote readiness acknowledgement UX  
**This build commit:** not committed (per user rule)

## Summary

Added focused Playwright coverage for the TPL-VOLUMETRIC-LETTERS warning acknowledgement path using seeded fixture `QT-E2E-COMMERCIAL-WARN-001`. The browser flow proves convert is disabled until inline acknowledgement, then succeeds through order and execution plan **201**.

## Fixture used

| Field | Value |
|-------|--------|
| Quote | `QT-E2E-COMMERCIAL-WARN-001` |
| Intake | `WI-E2E-COMMERCIAL-WARN-001` |
| `readiness_overlay` | `null` |
| `can_create_commercial_quote` | `true` |
| `requires_acknowledgement` | `true` |
| `quote_gate_ack_pending` | `["operations_missing"]` |

Loaded from `frontend/e2e/.commercial-fixture.json` → `warn_fixture` via `probeWarnLiveDbFixture()`.

## Files changed

| File | Change |
|------|--------|
| `frontend/e2e/commercial-chain-warn-ack.spec.ts` | New warn-ack browser E2E |
| `frontend/e2e/helpers/commercialFixture.ts` | `probeWarnLiveDbFixture`, `WarnFixtureManifest`, constants |
| `frontend/package.json` | `test:e2e:commercial-warn-ack` script |
| `docs/qa/BUILD_COMMERCIAL_WARN_ACK_E2E.md` | This doc |
| `docs/qa/BUILD_VOLUMETRIC_QUOTE_WIZARD_ACK_UX.md` | Follow-up note |

## E2E flow covered

1. Probe backend + manifest `warn_fixture` (skip if unavailable)
2. Open `/quotes/QT-E2E-COMMERCIAL-WARN-001`
3. Assert `quote-volumetric-readiness` panel visible
4. Assert status **Requires acknowledgement**
5. Assert `quote-volumetric-readiness-ack-pending` contains `(operations_missing)`
6. Assert `quote-convert-action` **disabled** + ack hint visible
7. Check `#quote_convert_acknowledge_warnings`
8. Assert convert **enabled**
9. Click convert → `/orders/:orderCode`
10. Assert `order-detail-selected`
11. Open `/execution/:orderDbId`
12. Generate plan → **201**, `tasks.length > 0`
13. Assert no `snapshot_incomplete` alert

**No API bypass** — acknowledgement and conversion use real UI controls only.

## Assertions made

| Assertion | Method |
|-----------|--------|
| `readiness_overlay === null` | Manifest probe |
| `requires_acknowledgement === true` | Manifest + UI status |
| `acknowledgement_pending` non-empty | Manifest + `quote-volumetric-readiness-ack-pending` |
| `operations_missing` visible | Ack-pending section `(operations_missing)` |
| Convert disabled before ack | `toBeDisabled()` |
| Convert enabled after ack | `toBeEnabled()` |
| Conversion via UI | `quote-convert-action` click |
| Order auto-select | `order-detail-selected` |
| Execution plan 201 | POST response status + tasks |

## Order / execution coverage

**Covered** — WARN fixture uses the same priced volumetric snapshot as the primary fixture; quote-derived order generates execution plan **201** with tasks after acknowledgement conversion.

## Commands run + exact results

```powershell
$env:DATABASE_URL='sqlite+aiosqlite:///C:/Users/offic/workos/backend/dev.db'
$env:APP_ENV='development'
cd backend
.\.venv\Scripts\python.exe scripts/seed_commercial_e2e_fixture.py
```

**Result:** PASS — `warn_fixture.requires_acknowledgement: true`

```powershell
cd frontend
npm run lint
```

**Result:** PASS

```powershell
$env:PW_SKIP_WEB_SERVER='1'
npm run test:e2e:commercial-live
npm run test:e2e:commercial-warn-ack
```

| Spec | Result |
|------|--------|
| `commercial-chain-live.spec.ts` | **1/1 OK** (5.5s) |
| `commercial-chain-warn-ack.spec.ts` | **1/1 OK** (5.8s) |

**Note:** Re-seed before both specs when WARN quote was already converted in a prior run.

## Remaining gaps

- No combined single npm script for both commercial E2E specs (run separately or `playwright test e2e/commercial-chain-*.spec.ts`)
- FigJam sticky not updated
- Quote list readiness badge still deferred

## No-regression checklist

- [x] WARN fixture from manifest
- [x] `readiness_overlay` null
- [x] `requires_acknowledgement` asserted
- [x] Ack-pending visible
- [x] Convert disabled before acknowledgement
- [x] Convert enabled after acknowledgement
- [x] Real UI conversion (no API bypass)
- [x] Order route + auto-select
- [x] Execution plan 201 + tasks
- [x] Primary commercial-live E2E still passes
- [x] No readiness policy / CostEngine changes

## Suggested next build

Combined `test:e2e:commercial` script + CI job running seed + both specs; optional quote-list readiness chip for pipeline visibility.
