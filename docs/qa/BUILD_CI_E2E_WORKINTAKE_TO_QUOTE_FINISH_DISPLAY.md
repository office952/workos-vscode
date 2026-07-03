# BUILD — CI/E2E Hardening: WorkIntake V2 → QuoteWizard Finish Display Smoke

**Date:** 2026-06-08  
**Build status:** **PASS**  
**Prior builds:** WorkIntake V2 Unified Operator Flow; Color & Vinyl Registry; QuoteWizard Color Finish Display; Operator Polish + Readiness Hardening

## Purpose

Repeatable Playwright smoke for the critical handoff:

```txt
WorkIntake V2 unified page
→ Zone D (RAL return + Oracal 8500 face)
→ readiness CTA
→ QuoteWizard / VolumetricLettersQuoteFlow
→ quote-finish-display
```

Hardening only — no business-logic or pricing changes.

## Context

- WorkIntake V2 captures RAL / Oracal 651 / 8500 with readiness gates.
- QuoteWizard shows **Finisaje și folii** via `quote-finish-display` (`VolumetricFinishDisplayPanel`).
- Unit/component tests already cover display formatting; this build adds live-db E2E coverage.

## Fixture strategy

| Property | Value |
|----------|--------|
| Intake code | `WI-E2E-WORKINTAKE-V2-FINISH-DISPLAY-001` |
| Template | `TPL-VOLUMETRIC-LETTERS` |
| Quote | _none_ (intake-only smoke) |
| Idempotency | Re-run seed updates intake `product_spec_json` in place |

**`WORKINTAKE_V2_FINISH_DISPLAY_SPEC`** (in `seed_commercial_e2e_fixture.py`) pre-seeds:

- SVG parsed + layer confirmed + geometry saved (`letter_perimeter_m`, `letter_face_area_m2`, …)
- `return_depth_mm: 80`, standard white return (colors exercised in UI)
- LED strip + PSU allocation `ok` (`psu_configuration: [100]`, watts fields)
- `visual_chamfer_included`, `illumination_family: front_lit`

The E2E test only selects RAL 9010 + Oracal 8500-010, saves production, opens QuoteWizard, and asserts `quote-finish-display`.

Manifest key: `finish_display_fixture` in `frontend/e2e/.commercial-fixture.json` (gitignored).

## Local run commands

### 1. One-time Playwright browser

```bash
cd frontend
npx playwright install chromium
```

### 2. Seed fixture (from repo root, dev DB)

```powershell
$env:APP_ENV='development'
$env:ENVIRONMENT='development'
$env:DATABASE_URL='sqlite+aiosqlite:///C:/Users/offic/workos/backend/dev.db'
$env:JWT_SECRET_KEY='local-dev-secret-not-for-production'
cd backend
.\.venv\Scripts\python.exe scripts\seed_commercial_e2e_fixture.py
```

### 3. Start backend + frontend (if not already running)

```powershell
# Terminal A — backend :8000
cd backend
.\.venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000

# Terminal B — frontend :3000
cd frontend
pnpm run dev
```

### 4. Run smoke only

```bash
cd frontend
PW_SKIP_WEB_SERVER=1 npm run test:e2e:workintake-finish
```

Or directly:

```bash
PW_SKIP_WEB_SERVER=1 npx playwright test e2e/work-intake-v2-to-quote-finish-display.spec.ts
```

### 5. Unit/component regression (no DB)

```bash
cd frontend
npx vitest run \
  src/components/workos/QuoteWizard.volumetricRouting.test.tsx \
  src/lib/volumetricFinishDisplay.test.ts \
  src/components/workos/workIntakeV2/WorkIntakeV2Flow.test.tsx
```

## CI notes

- No `.github/workflows` in repo at build time — commands documented here only.
- Optional CI job (when added): install Chromium → seed DB → start backend + frontend → run `test:e2e:workintake-finish`.
- Spec skips explicitly when backend unhealthy or fixture missing (no fake pass).

## Files changed

| File | Change |
|------|--------|
| `backend/scripts/seed_commercial_e2e_fixture.py` | `WORKINTAKE_V2_FINISH_DISPLAY_SPEC` + `WI-E2E-WORKINTAKE-V2-FINISH-DISPLAY-001` |
| `frontend/e2e/work-intake-v2-to-quote-finish-display.spec.ts` | New smoke spec |
| `frontend/e2e/helpers/commercialFixture.ts` | `probeFinishDisplayLiveDbFixture()` |
| `frontend/package.json` | `test:e2e:workintake-finish` script |

## Test coverage

| Layer | File | Asserts |
|-------|------|---------|
| E2E smoke | `frontend/e2e/work-intake-v2-to-quote-finish-display.spec.ts` | Zones, no stage-nav, RAL/8500 selection, CTA gating, QuoteWizard, `quote-finish-display` |
| Probe helper | `frontend/e2e/helpers/commercialFixture.ts` | `probeFinishDisplayLiveDbFixture()` |
| Seed | `backend/scripts/seed_commercial_e2e_fixture.py` | `WORKINTAKE_V2_FINISH_DISPLAY_SPEC` + manifest |
| npm script | `test:e2e:workintake-finish` | Single-spec runner |

## E2E flow

1. Probe `/health` + manifest `finish_display_fixture` + DB intake row.
2. `/intake-v2/WI-E2E-WORKINTAKE-V2-FINISH-DISPLAY-001`
3. Assert unified zones; `work-intake-v2-stage-nav` count = 0.
4. CTA enabled (fixture prerequisites).
5. Enable face vinyl → CTA disabled + repair item.
6. Select RAL 9010, Oracal 8500 `010`, save production.
7. CTA enabled → click `work-intake-v2-open-quote-wizard`.
8. `/quotes` — `Cum vrei să calculezi?` + `quote-finish-display`.

## Selectors used

| Area | `data-testid` |
|------|----------------|
| Flow | `work-intake-v2-flow`, `work-intake-v2-zone-*` |
| CTA | `work-intake-v2-open-quote-wizard`, `work-intake-v2-cta-blocker-reason`, `work-intake-v2-repair-face-vinyl-code` |
| Return RAL | `work-intake-v2-return-finish-system`, `work-intake-v2-return-ral-select-*` |
| Face 8500 | `work-intake-v2-face-wrap`, `work-intake-v2-face-vinyl-series`, `work-intake-v2-face-vinyl-select-*` |
| Quote display | `quote-finish-display`, `quote-finish-display-return-detail`, `quote-finish-display-return-approx-note`, `quote-finish-display-face-label`, `quote-finish-display-face-detail` |

## Test results

| Suite | Command | Result |
|-------|---------|--------|
| Vitest regression | `npx vitest run QuoteWizard.volumetricRouting + volumetricFinishDisplay + WorkIntakeV2Flow` | **38/38 PASS** |
| E2E smoke | `PW_SKIP_WEB_SERVER=1 npm run test:e2e:workintake-finish` | **1/1 PASS** (~4s) |

**Environment:** Reused existing backend `:8000` + frontend `:3000`; seed re-run updated manifest with `finish_display_fixture` (`intake_id: 33`).

## Boundary (respected)

- No CostEngine, pricing calculation, or inventory changes.
- No WorkIntake V1, SmartBill, email offer, or order-confirmation changes.
- No palette/registry data edits.
- No QuoteWizard business-logic changes (test IDs already present).

## Remaining risks

- E2E depends on live backend + seeded dev DB; CI must replicate seed + env vars.
- Color registry option test IDs assume subset includes RAL 9010 and Oracal 8500-010.
- Handoff persists via navigation state; full quote creation/pricing not exercised in this smoke.

## Next candidates

- Wire optional GitHub Actions job for `test:e2e:workintake-finish`.
- Extend smoke to assert handoff `product_spec_json` round-trip via API after CTA.
- Combine with commercial-chain-live in a single `test:e2e:commercial-all` script.
