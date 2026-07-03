# TPL-VOLUMETRIC-LETTERS Quote Flow Readiness

**Date:** 2026-06-09  
**Branch:** `feature/tpl-volumetric-quote-flow-readiness`  
**Base:** `integration/recovered-product-base` @ `b8a04ae`

Related recovery docs:

* [Source of Truth Recovery Checkpoint](../recovery/SOURCE_OF_TRUTH_RECOVERY_CHECKPOINT_2026-06-09.md)
* [Recovered Product Base Stabilization](../recovery/RECOVERED_PRODUCT_BASE_STABILIZATION_2026-06-09.md)

---

## 1. Target Commercial Flow

```
Work Intake V2 / SVG layers
  → TPL-VOLUMETRIC-LETTERS template recognition
  → finish / color / material selection (RAL / Oracal)
  → Pricing registry readiness
  → QuoteWizard handoff
  → quote summary / commercial display (VolumetricFinishDisplayPanel)
```

---

## 2. Flow Map

| Segment | Key files | Status |
| ------- | --------- | ------ |
| **Intake entry** | `pages/WorkIntakeV2.tsx`, `workIntakeV2/WorkIntakeV2Flow.tsx` | PASS |
| **SVG / layer analysis** | `SvgLayerAnalysisPanel.tsx`, `lib/intakeVectorLayerMapping.ts`, `lib/mapSvgGeometryToSpec.ts` | PASS |
| **Template** | `TPL-VOLUMETRIC-LETTERS` in ProductSystem, `lib/volumetricIntakeRoute.ts` | PASS |
| **Quote input builder** | `lib/volumetricQuoteInput.ts`, `lib/volumetricQuoteFlowState.ts` | PASS |
| **Finish / color (intake)** | `workIntakeV2/stages/V2ProductionStage.tsx`, `colorRegistry/ColorRegistrySelect.tsx` | **Wired this build** |
| **Finish display (quote)** | `lib/volumetricFinishDisplay.ts`, `VolumetricFinishDisplayPanel.tsx` | PASS (pre-existing) |
| **QuoteWizard handoff** | `QuoteWizard.tsx` → `VolumetricLettersQuoteFlow.tsx` | PASS |
| **Commercial summary** | `VolumetricFinishDisplayPanel` @ `quote-finish-display` | PASS |
| **Pricing registry** | `pages/Pricing.tsx`, `api/pricingRegistry.ts`, `backend/services/pricing_registry_service.py` | PASS route; **7 missing variant rows in local dev.db** |
| **Backend quote** | `routers/quotes.py`, volumetric quote input/ready policies | PASS |

---

## 3. Implemented Wiring (this build)

### ColorRegistrySelect in Work Intake V2 production stage

**Problem:** E2E specs and color registry tests expected `work-intake-v2-return-ral-select` and `work-intake-v2-face-vinyl-select`, but `V2ProductionStage` used plain text inputs. Classification **A** — data + component existed, not wired.

**Fix:** `V2ProductionStage.tsx` now uses `ColorRegistrySelect` for:

| Field | testId | Filter |
| ----- | ------ | ------ |
| RAL return | `work-intake-v2-return-ral-select` | RAL / `return` scope |
| Oracal 651 return | `work-intake-v2-return-oracal-select` | ORACAL 651 / `return` |
| Face vinyl | `work-intake-v2-face-vinyl-select` | ORACAL 651 or 8500 by series |

On selection, persists `code`, `name`, `previewHex` into `product_spec_json` for handoff to QuoteWizard.

**Tests updated:** `WorkIntakeV2Flow.test.tsx` uses color registry picker interactions.

---

## 4. RAL / Oracal Readiness Classification

| Area | Classification | State |
| ---- | -------------- | ----- |
| RAL catalog data | — | `lib/colorRegistry/ralColors.ts` |
| Oracal 651 / 8500 data | — | `lib/colorRegistry/oracalColors.ts` |
| ColorRegistrySelect component | — | Exists |
| Intake RAL picker | **Was A → now wired** | ColorRegistrySelect in V2ProductionStage |
| Intake Oracal face picker | **Was A → now wired** | ColorRegistrySelect in V2ProductionStage |
| Intake Oracal return picker | **Was A → now wired** | ColorRegistrySelect in V2ProductionStage |
| Quote config persistence | **D (partial)** | Handoff via `product_spec_json` fields (`return_ral_*`, `face_vinyl_*`) |
| QuoteWizard finish display | **E (already done)** | `VolumetricFinishDisplayPanel` shows RAL/Oracal + hex swatch |
| Preview demo | — | `/demo/volumetric-letter-preview` |
| Incomplete catalog warning | — | `lookupColorRegistryItem` returns `unknown`; summary warnings in `formatVolumetricFinishSummary` |

**Required behaviors:**

* Selected RAL code/name appears in intake finish summary and `quote-finish-display` — **PASS**
* Selected Oracal series/code/name appears for face vinyl — **PASS**
* Hex preview when available — **PASS** (swatch in finish display panel)
* Approximate RAL note — **PASS** (`showApproxNote` on RAL select + panel note)
* No fake complete catalog claims — **PASS** (search shows count; unknown codes get warnings)

---

## 5. Pricing Gap Audit

### Local dev.db (`TPL-VOLUMETRIC-LETTERS` filter) — updated 2026-06-09 E2E proof

**8 owner-confirmed variant rows verified** in `backend/dev.db` with active EUR `unit_cost`:

| Code | base_cost |
| ---- | --------- |
| `MAT-PROFIL-LATERAL-LITERE-30MM` | 2.00 EUR/ml |
| `MAT-PROFIL-LATERAL-LITERE-60MM` | 3.00 EUR/ml |
| `MAT-PROFIL-LATERAL-LITERE-80MM` | 4.00 EUR/ml |
| `MAT-PROFIL-LATERAL-LITERE-100MM` | 5.00 EUR/ml |
| `MAT-LED-PSU-12V-60W` | 12.00 EUR |
| `MAT-LED-PSU-12V-100W` | 16.00 EUR |
| `MAT-LED-PSU-12V-160W` | 20.00 EUR |
| `MAT-LED-PSU-12V-200W` | 40.00 EUR |

Seed command (idempotent — skipped already-applied rows):

```powershell
cd C:\Users\offic\workos\backend
$env:DATABASE_URL='sqlite+aiosqlite:///./dev.db'
.\.venv\Scripts\python.exe scripts\seed_volumetric_owner_confirmed_prices.py
```

### Intentional “Lipsă” rows (not variant gaps)

| Code | Notes |
| ---- | ----- |
| `MAT-PROFIL-LATERAL-LITERE` | Parent alias — depth variant resolved at quote time |
| `MAT-LED-PSU-12V` | Parent alias — wattage variant resolved at quote time |
| `ELECTRICAL_WIRING`, `LED_ASSEMBLY`, `PREPRESS`, `VINYL_APPLICATION`, `PACKAGING` | Operation rates — pre-existing gaps |

Pricing UI may still show **7 lipsă** (2 generic aliases + 5 operation rates). Variant pricing for quote-time depth/PSU selection is **complete**.

See [BUILD_TPL_VOLUMETRIC_QUOTE_FLOW_E2E_PROOF.md](../qa/BUILD_TPL_VOLUMETRIC_QUOTE_FLOW_E2E_PROOF.md) for full proof record.

---

## 6. Tests Run

| Suite | Result |
| ----- | ------ |
| `WorkIntakeV2Flow.test.tsx` | **PASS** (incl. RAL picker tests) |
| `volumetricFinishDisplay.test.ts` | **PASS** |
| `QuoteWizard.volumetricRouting.test.tsx` | **PASS** |
| `VolumetricLettersQuoteFlow.commercialCreated.test.tsx` | **PASS** |
| Frontend typecheck | **PASS** |
| Frontend lint | **PASS** |
| Backend `test_quote_price_intake_linkage.py` | **PASS** |
| Backend `test_volumetric_execution_dispatch.py` | **PASS** |

### Playwright e2e — updated 2026-06-09

| Spec | Result |
| ---- | ------ |
| `e2e/work-intake-v2-to-quote-finish-display.spec.ts` | **PASS** (headed, 4.2s) |

Prerequisites applied:

1. `pnpm exec playwright install chromium`
2. `python scripts/seed_commercial_e2e_fixture.py` on local `dev.db`

Minor E2E-only fix: face finish summary assertion uses `work-intake-v2-finish-summary` (face detail has no dedicated testId).

---

## 7. Runtime Smoke (`:3000`) — updated 2026-06-09

| Route | Result | Notes |
| ----- | ------ | ----- |
| `/inventory/pricing` | PASS | TPL-VOLUMETRIC-LETTERS; 8 variants priced; 7 lipsă = 2 aliases + 5 ops |
| `/product-system` | PASS | `TPL-VOLUMETRIC-LETTERS` active |
| `/intake-v2/WI-E2E-WORKINTAKE-V2-FINISH-DISPLAY-001` | PASS | RAL / Oracal pickers visible |
| `/quotes` | PASS | Via E2E — QuoteWizard + finish display |

---

## 8. Remaining Owner Decisions

1. Whether generic parent codes (`MAT-PROFIL-LATERAL-LITERE`, `MAT-LED-PSU-12V`) should show as reference-only in Pricing UI instead of “Lipsă”
2. Operation rate gaps (`ELECTRICAL_WIRING`, `LED_ASSEMBLY`, `PREPRESS`, `VINYL_APPLICATION`, `PACKAGING`) — separate pricing workstream
3. CI Playwright browser caching for repeatable e2e in pipeline

---

## 9. Next Recommended Step

**QuoteWizard commercial document readiness** — priced quote → commercial document output with finish display snapshot.

---

## 10. PASS Statement

RAL / Oracal color registry pickers are wired into Work Intake V2 production stage and flow through to QuoteWizard `quote-finish-display`. **E2E proven** on local dev (2026-06-09): `work-intake-v2-to-quote-finish-display.spec.ts` PASS. All 8 depth/PSU variant prices verified in local `dev.db`.
