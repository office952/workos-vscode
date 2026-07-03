# BUILD — TPL Volumetric Quote Flow E2E Proof

**Date:** 2026-06-09  
**Branch:** `feature/tpl-volumetric-quote-flow-readiness`  
**HEAD before:** `aa4b6da`  
**Base:** `feature/tpl-volumetric-quote-flow-readiness`

---

## Summary

Proof-only build confirming the commercial browser flow for `TPL-VOLUMETRIC-LETTERS`:

Work Intake V2 → finish/color configuration → QuoteWizard handoff → `VolumetricLettersQuoteFlow` → finish display.

**Decision: PASS** — E2E commercial flow proven on local dev stack.

---

## 1. Branch & Safety

| Check | Result |
| ----- | ------ |
| Branch | `feature/tpl-volumetric-quote-flow-readiness` |
| HEAD | `aa4b6da` (clean source — only untracked scratch files) |
| Dirty tracked files | None |
| origin/main touched | No |
| PR #3 touched | No |

---

## 2. Environment

| Component | Value |
| --------- | ----- |
| Frontend | `C:\Users\offic\workos\frontend` — Vite on `127.0.0.1:3000` (PID 14112) |
| Backend | `C:\Users\offic\workos\backend` — uvicorn `main:app` on `127.0.0.1:8000` (PID 10168) |
| Local DB | `C:\Users\offic\workos\backend\dev.db` via `DATABASE_URL=sqlite+aiosqlite:///./dev.db` |
| Playwright Chromium | Installed — Chrome for Testing 145.0.7632.6 (chromium v1208) |

---

## 3. Seeds (local dev only)

### Pricing seed

```powershell
cd C:\Users\offic\workos\backend
$env:DATABASE_URL='sqlite+aiosqlite:///./dev.db'
.\.venv\Scripts\python.exe scripts\seed_volumetric_owner_confirmed_prices.py
```

**Result:** `patched: 0`, `skipped: 19` — all owner-confirmed variant rows already present in `dev.db`.

### Commercial E2E fixture seed

```powershell
cd C:\Users\offic\workos\backend
$env:DATABASE_URL='sqlite+aiosqlite:///./dev.db'
.\.venv\Scripts\python.exe scripts\seed_commercial_e2e_fixture.py
```

**Result:** Fixture manifest written to `frontend/e2e/.commercial-fixture.json`.

| Fixture | Code | ID |
| ------- | ---- | -- |
| Commercial spine | `WI-E2E-COMMERCIAL-001` / `QT-E2E-COMMERCIAL-001` | intake 23 / quote 8 |
| Finish display smoke | `WI-E2E-WORKINTAKE-V2-FINISH-DISPLAY-001` | intake 33 |

### Pricing rows — before / after

**Target variant codes (8):**

- `MAT-PROFIL-LATERAL-LITERE-30MM` → 2.00 EUR/ml
- `MAT-PROFIL-LATERAL-LITERE-60MM` → 3.00 EUR/ml
- `MAT-PROFIL-LATERAL-LITERE-80MM` → 4.00 EUR/ml
- `MAT-PROFIL-LATERAL-LITERE-100MM` → 5.00 EUR/ml
- `MAT-LED-PSU-12V-60W` → 12.00 EUR
- `MAT-LED-PSU-12V-100W` → 16.00 EUR
- `MAT-LED-PSU-12V-160W` → 20.00 EUR
- `MAT-LED-PSU-12V-200W` → 40.00 EUR

**Before seed:** All 8 rows existed as `active` in `inventory_materials` with owner-confirmed `unit_cost` values. Pricing Registry `base_cost` populated for all variants.

**After seed:** No duplicates created. Seed idempotent skip confirmed.

**Intentional “Lipsă” rows (by design, not variant gaps):**

- `MAT-PROFIL-LATERAL-LITERE` — generic template alias; depth variant selected at quote time
- `MAT-LED-PSU-12V` — generic template alias; wattage variant selected at quote time
- Five operation rates (`ELECTRICAL_WIRING`, `LED_ASSEMBLY`, `PREPRESS`, `VINYL_APPLICATION`, `PACKAGING`) — pre-existing gaps unrelated to this proof

Pricing UI summary for `TPL-VOLUMETRIC-LETTERS`: **22 confirmate · 2 review · 7 lipsă** (includes 2 generic material aliases + 5 operation rates).

---

## 4. Validation

| Gate | Result |
| ---- | ------ |
| Backend `test_quote_price_intake_linkage.py` + `test_volumetric_execution_dispatch.py` | **6/6 PASS** |
| Frontend typecheck | **PASS** |
| Frontend lint | **PASS** |
| Frontend build | **PASS** |
| Focused Vitest `WorkIntakeV2Flow.test.tsx` | **36/36 PASS** |
| `VolumetricFinishDisplayPanel.test.tsx` | Not present in repo at proof time |
| `QuoteWizard.test.tsx` | Not present in repo at proof time |

---

## 5. Playwright E2E

**Spec:** `frontend/e2e/work-intake-v2-to-quote-finish-display.spec.ts`

| Run | Mode | Result |
| --- | ---- | ------ |
| 1 | `--headed` | FAIL — stale testId `work-intake-v2-finish-summary-face-detail` (not in `V2ProductionStage`) |
| 2 | `--headed` (after E2E-only fix) | **PASS** (4.2s) |

### E2E fix (test-only)

Assertion updated to use `work-intake-v2-finish-summary` container (face detail renders as plain `<p>` without dedicated testId).

### Assertions covered

- Work Intake V2 fixture loads (`WI-E2E-WORKINTAKE-V2-FINISH-DISPLAY-001`)
- `TPL-VOLUMETRIC-LETTERS` active in workspace
- RAL return selector visible; RAL 9010 selected
- Oracal 8500 face vinyl selected; roll width 1260 mm
- Finish summary shows RAL 9010 + Oracal 8500-010
- Readiness → “Gata pentru ofertare”
- QuoteWizard CTA enabled → navigates to `/quotes`
- `quote-finish-display` shows RAL 9010 + Oracal 8500-010 translucent
- No duplicate finish display blocks

### Not asserted in E2E (manual / unit coverage)

- `return_oracal_*` fields (test uses RAL return, not Oracal return)
- Direct API readback of `product_spec_json` post-persist (covered by unit tests + E2E UI persistence)

---

## 6. Browser Smoke

| Route | Result | Notes |
| ----- | ------ | ----- |
| `/inventory/pricing` | PASS | `TPL-VOLUMETRIC-LETTERS` filter; all 8 depth/PSU variants priced; generic alias rows show intentional “Lipsă” |
| `/product-system` | PASS | `TPL-VOLUMETRIC-LETTERS` active (1 active template) |
| `/intake-v2/WI-E2E-WORKINTAKE-V2-FINISH-DISPLAY-001` | PASS | RAL / Oracal pickers visible; fixture in pre-color state after re-seed |
| `/intake` | Not separately smoke-tested | E2E covers intake-v2 path |
| `/quotes` | PASS via E2E | QuoteWizard + finish display rendered |
| `/demo/volumetric-letter-preview` | Not smoke-tested this build | Pre-existing demo route |

No console error overlay observed on checked routes.

---

## 7. RAL / Oracal Proof

| Item | Result |
| ---- | ------ |
| Return RAL | E2E: RAL 9010 selected via `work-intake-v2-return-ral-select` |
| Face vinyl | E2E: Oracal 8500-010 selected via `work-intake-v2-face-vinyl-select` |
| Return Oracal | Component wired; E2E uses RAL return path |
| Persisted in `product_spec_json` | Via workspace auto-save (unit tests + E2E handoff preview) |
| Shown in QuoteWizard | E2E: `quote-finish-display-return-detail` + face label/detail |
| Shown in finish display | E2E PASS |

---

## 8. Pricing Proof

| Item | Result |
| ---- | ------ |
| TPL variant pricing warning | **Resolved** for all 8 depth/PSU variants |
| Missing variant rates | **0** among the 8 owner-confirmed codes |
| Seeded variants | All 8 present with owner-confirmed EUR prices |
| Remaining “7 lipsă” UI count | 2 generic material aliases + 5 operation rates (expected) |
| Fixture quote priced | `QT-E2E-COMMERCIAL-001` grand_total = 1104.33 RON |

---

## 9. Files Changed

| File | Change |
| ---- | ------ |
| `frontend/e2e/work-intake-v2-to-quote-finish-display.spec.ts` | E2E assertion fix (face summary testId) |
| `docs/qa/BUILD_TPL_VOLUMETRIC_QUOTE_FLOW_E2E_PROOF.md` | Created (this document) |
| `docs/product-system/TPL_VOLUMETRIC_LETTERS_QUOTE_FLOW_READINESS.md` | Updated E2E proof status |

**Not committed:** `backend/dev.db`, Playwright browser binaries, `frontend/e2e/.commercial-fixture.json` (generated manifest).

---

## 10. Decision

**A. PASS** — TPL Volumetric Quote Flow is E2E proven on local dev.

---

## 11. Next Recommended Step

**A. QuoteWizard commercial document readiness**

---

## 12. Boundary Confirmation

| Boundary | Confirmed |
| -------- | --------- |
| No origin/main touch | Yes |
| No PR #3 touch | Yes |
| No app-layout migration | Yes |
| No CostEngine change | Yes |
| No hardcoded prices | Yes |
| No production migration/seed | Yes |
| No DB reset/clean | Yes |
| No scratch committed | Yes |
| No local DB committed | Yes |
