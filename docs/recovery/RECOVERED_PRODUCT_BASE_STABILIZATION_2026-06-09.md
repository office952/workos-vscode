# Recovered Product Base Stabilization — 2026-06-09

**Status: PASS**

This document records the first productive stabilization build on the recovered product base. It supplements (does not replace) the source-of-truth checkpoint:

* [Source of Truth Recovery Checkpoint — 2026-06-09](./SOURCE_OF_TRUTH_RECOVERY_CHECKPOINT_2026-06-09.md)

---

## 1. Branch Created

| Item | Value |
| ---- | ----- |
| **Base branch** | `recovery/frontend-source-of-truth-wip` |
| **New branch** | `integration/recovered-product-base` |
| **HEAD at creation** | `4d27aa4` — docs: record source of truth recovery checkpoint |
| **Folder** | `C:\Users\offic\workos` |

No code or test changes were required during this build. Stabilization passed on the recovered base as-is.

---

## 2. Baseline Validation Results

### Backend (focused pytest)

**57/57 PASS**

| Test file | Result |
| --------- | ------ |
| `tests/test_quote_price_intake_linkage.py` | PASS |
| `tests/test_anaf_client.py` | PASS |
| `tests/test_operational_resource_registry.py` | PASS (7) |
| `tests/test_operational_reports.py` | PASS |
| `tests/test_operational_reality_review.py` | PASS |
| `tests/test_operator_employee_selection.py` | PASS |
| `tests/test_execution_reality_workforce_capture.py` | PASS |
| `tests/test_field_installation_team_allocation.py` | PASS |
| `tests/test_volumetric_execution_dispatch.py` | PASS (3) |

### Frontend

| Check | Result |
| ----- | ------ |
| `pnpm run typecheck` | **PASS** |
| `pnpm run lint` | **PASS** |
| `pnpm run build` | **PASS** (chunk size warnings only) |

### Frontend focused vitest

**758/758 PASS** (99 test files)

Scope:

```
src/pages/ProductSystem*
src/pages/Quotes*
src/pages/WorkIntake*
src/components/workos
src/lib
```

**Known exclusions (intentional, not deleted):**

* `frontend/wip/operational-registry/tabletLiveBridge.test.ts` — WIP scratch with broken import; outside focused scope
* Playwright e2e suites — not run in this build (deferred to next commercial-flow build)
* Full-repo vitest — not run; focused scope chosen to avoid WIP noise

---

## 3. Runtime Verification

Dev stack reused on `:3000` / `:8000` via prior `scripts/start-dev.ps1` session.

| Endpoint | Result |
| -------- | ------ |
| `GET /health` | **200** |
| `GET /api/v1/operational-registry/employees` | **200** |
| `GET /api/v1/operational-reports/summary` | **200** |
| `GET /api/v1/operational-reality/review` | **200** |

| Port | Role | Status |
| ---- | ---- | ------ |
| `:3000` | Product frontend | **PASS** |
| `:8000` | Product backend | **PASS** |
| `:3002` | PR #3 app-layout frontend | **DO NOT USE** |
| `:8001` | Previous hybrid/port runtime | **DO NOT USE** |

---

## 4. Browser Route Smoke (`:3000` only)

| Route | Result | Notes |
| ----- | ------ | ----- |
| `/` | **PASS** | Redirects to `/dashboard` |
| `/dashboard` | **PASS** | Control Tower UI, sidebar nav |
| `/inventory/pricing` | **PASS** | Live DB; `TPL-VOLUMETRIC-LETTERS` visible; 7 missing rates flagged (data, not route failure) |
| `/product-system` | **PASS** | `TPL-VOLUMETRIC-LETTERS` active template listed |
| `/intake` | **PASS** | Work Intake list loads |
| `/quotes` | **PASS** | Quotes list loads |
| `/clients` | **PASS** | Clients workspace loads |
| `/personal` | **PASS** | Personal / Angajați; 5 employees from Live DB |
| `/operator` | **PASS** | Operator view loads |
| `/tablet` | **PASS** (with warning) | Station selector loads; footer shows demo fallback text when `isLive=false`; help requests remain UI demo by design |
| `/reports/operational` | **PASS** | Operational reports page loads |
| `/demo/volumetric-letter-preview` | **PASS** | Volumetric letter preview demo loads |

No 404, error boundary, or missing-route failures observed on checked routes.

---

## 5. Blockers Fixed

**None.** No code or test changes were required.

Prior fix on recovery branch (`b3181d5`) already addressed the operational registry employees 500 via dev-only schema repair.

---

## 6. Commercial Flow Readiness Map

Target flow:

```
Work Intake / SVG / layers → TPL-VOLUMETRIC-LETTERS → Pricing / ProductSystem → QuoteWizard → quote revision / commercial output
```

### 6.1 Work Intake entry

| File | Role |
| ---- | ---- |
| `frontend/src/pages/WorkIntake.tsx` | V1 intake list |
| `frontend/src/pages/WorkIntakeV2.tsx` | V2 unified intake page (`/intake-v2/:id`) |
| `frontend/src/pages/IntakeDetail.tsx` | V1 detail + ProductSystem section + quote handoff |
| `frontend/src/components/workos/workIntakeV2/WorkIntakeV2Flow.tsx` | V2 multi-stage flow (context → SVG → layers → production → handoff) |
| `frontend/src/App.tsx` | Routes: `/intake`, `/intake/:id`, `/intake-v2/:id` |

### 6.2 SVG / vector / layer mapping

| File | Role |
| ---- | ---- |
| `frontend/src/lib/intakeVectorLayerMapping.ts` | Layer-to-spec mapping |
| `frontend/src/lib/mapSvgGeometryToSpec.ts` | SVG geometry → intake spec |
| `frontend/src/lib/volumetricVectorFastAskMapping.ts` | Fast-ask vector mapping |
| `frontend/src/components/workos/SvgLayerAnalysisPanel.tsx` | Layer analysis UI |
| `backend/services/svg_layer_analysis_service.py` | Backend SVG layer analysis |
| `backend/tests/test_svg_manual_layer_mapping.py` | Layer mapping tests |

### 6.3 Product template — TPL-VOLUMETRIC-LETTERS

| File | Role |
| ---- | ---- |
| `backend/seeds/seed_build4_templates.py` | Template seed |
| `frontend/src/pages/ProductSystem.tsx` | Template editor entry |
| `frontend/src/lib/volumetricIntakeRoute.ts` | Route resolution to volumetric intake |
| `frontend/src/lib/intakeVolumetricSpec.ts` | Volumetric spec model |
| `frontend/src/lib/volumetricQuoteInput.ts` | Quote input builder |
| `frontend/src/components/workos/templateIntakeWorkspace/VolumetricLettersWorkspace.tsx` | Template-specific workspace |
| `backend/services/volumetric_quote_input_policy.py` | Input validation policy |
| `backend/services/volumetric_quote_ready_policy.py` | Quote-ready policy |

### 6.4 Pricing / ProductSystem registry

| File | Role |
| ---- | ---- |
| `frontend/src/pages/Pricing.tsx` | Material Price Registry UI (`/inventory/pricing`) |
| `frontend/src/api/pricingRegistry.ts` | Pricing API client |
| `frontend/src/lib/pricingRegistry.ts` | Registry helpers |
| `backend/routers/pricing_registry.py` | Pricing registry endpoints |
| `backend/routers/product_readiness.py` | Product readiness |
| `backend/routers/product_system_cost_simulation.py` | Cost simulation |

### 6.5 QuoteWizard

| File | Role |
| ---- | ---- |
| `frontend/src/components/workos/QuoteWizard.tsx` | Multi-step pricing wizard |
| `frontend/src/components/workos/VolumetricLettersQuoteFlow.tsx` | TPL-VOLUMETRIC-LETTERS quote flow |
| `frontend/src/pages/Quotes.tsx` | Quotes page + wizard mount |
| `frontend/src/api/quotes.ts` | Quote API + volumetric handoff types |
| `backend/routers/quotes.py` | Quote CRUD / pricing endpoints |

### 6.6 Quote revision / commercial spine

| File | Role |
| ---- | ---- |
| `frontend/src/lib/commercialSpineNavigation.ts` | Navigation between intake → quote → order |
| `frontend/src/lib/quoteRevision.ts` | Revision eligibility + history |
| `frontend/src/lib/quoteCommercialGuidance.ts` | Send / convert / revision guidance |
| `frontend/src/components/workos/QuoteRevisionDialog.tsx` | Revision UI |
| `frontend/src/components/workos/QuoteCommercialActionPanel.tsx` | Commercial actions panel |
| `frontend/src/lib/quoteAcceptanceConversion.ts` | Accept → order conversion |
| `backend/routers/quote_output_snapshots.py` | Output snapshot governance |
| `backend/routers/quote_documents.py` | Quote documents |
| `backend/routers/quote_pdf.py` | PDF generation |

### 6.7 Backend endpoints (commercial spine)

| Router | Purpose |
| ------ | ------- |
| `intake_requests.py` | Intake CRUD |
| `intake_assist.py` | Intake assist |
| `vector_assets.py` | Vector asset storage |
| `pricing_registry.py` | Material/rate registry |
| `quotes.py` | Quote lifecycle |
| `orders.py` | Order conversion |
| `operator_tasks.py` | Execution dispatch |
| `product_blueprint_dossier.py` | Blueprint dossier |

### 6.8 Existing tests covering the flow

| Area | Tests |
| ---- | ----- |
| Work Intake V2 | `WorkIntakeV2Flow.test.tsx`, `WorkIntakeV2.test.tsx`, `stageCompletion.test.ts` |
| Layer mapping | `intakeVectorLayerMapping.test.ts`, `mapSvgGeometryToSpec.test.ts` |
| Volumetric routing | `QuoteWizard.volumetricRouting.test.tsx`, `volumetricIntakeRoute.test.ts` |
| Quote flow | `VolumetricLettersQuoteFlow.commercialCreated.test.tsx`, `volumetricQuoteFlowState.test.ts` |
| Quote revision | `quoteRevision.test.ts`, `Quotes.commercialActions.test.tsx` |
| Backend policies | `test_volumetric_quote_input_policy.py`, `test_volumetric_quote_ready_policy.py` |
| Execution dispatch | `test_volumetric_execution_dispatch.py`, `test_volumetric_order_execution_snapshot.py` |
| E2E (present, not run here) | `e2e/work-intake-v2-volumetric.spec.ts`, `e2e/work-intake-v2-to-quote-finish-display.spec.ts` |

### 6.9 Known gaps (deferred, not blockers for this build)

1. **Pricing data gaps** — UI shows 7 missing rates for `TPL-VOLUMETRIC-LETTERS`; route works, data incomplete.
2. **Tablet live mode** — `/tablet` footer may show demo fallback when `isLive=false`; station cards render; help-request UI remains demo by design.
3. **WIP test** — `wip/operational-registry/tabletLiveBridge.test.ts` has broken import.
4. **E2E not executed** — Playwright commercial fixture flow deferred to next build.
5. **Local Alembic stamp** — `dev.db` may read `s42` while columns repaired; production must use migrations.
6. **End-to-end Anne's Store fixture** — `seed_commercial_e2e_fixture.py` + e2e helpers exist; full browser walk not done here.

---

## 7. Active Modules (confirmed on recovered base)

| Module | Route / entry | Status |
| ------ | ------------- | ------ |
| Dashboard | `/dashboard` | PASS |
| ProductSystem | `/product-system` | PASS |
| Pricing Registry | `/inventory/pricing` | PASS |
| Work Intake V1 | `/intake` | PASS |
| Work Intake V2 | `/intake-v2/:id` | Wired; unit tests pass |
| Quotes / QuoteWizard | `/quotes` | PASS |
| Personal / Angajați | `/personal` | PASS |
| Operational registry | API + Personal | PASS |
| Operational reports | `/reports/operational` | PASS |
| Operational reality review | `/execution/reality-review` | PASS |
| Tablet stations | `/tablet` | PASS (demo footer when not live) |
| Volumetric preview demo | `/demo/volumetric-letter-preview` | PASS |

---

## 8. Remaining Warnings

| Warning | Severity | Action |
| ------- | -------- | ------ |
| `origin/main` not product truth | **DO NOT USE** | Branch strategy decision deferred |
| `:3002` / `:8001` not product truth | **DO NOT USE** | Ignore for development |
| Pricing missing rates for volumetric template | **WARNING** | Next build: pricing registry cleanup or fixture seed (owner approval) |
| Tablet `isLive=false` footer | **WARNING** | Verify execution task feed in next operational build |
| WIP scratch files uncommitted | **OK** | Backed up; cleanup deferred |
| App-layout migration | **FUTURE** | Separate architecture build |

---

## 9. Next Recommended Build

**Recommended: A — TPL-VOLUMETRIC-LETTERS quote flow stabilization**

**Why:**

* Recovered base is green for validation, runtime, and route smoke.
* All commercial spine files are present and unit-tested.
* The highest-value next step is proving the full money path end-to-end: Work Intake V2 → SVG/layers → `TPL-VOLUMETRIC-LETTERS` → QuoteWizard → priced quote with finish display.
* Pricing data gaps (7 missing rates) and e2e coverage are the main unknowns — both are directly on the volumetric quote path.
* Other options (B layer confirmation, C pricing cleanup, D commercial documents) are subsets of A.

Suggested sequence for build A:

1. Run Playwright e2e: `work-intake-v2-volumetric.spec.ts`, `work-intake-v2-to-quote-finish-display.spec.ts`
2. Resolve pricing registry gaps blocking preliminary quote calculation
3. Browser smoke: intake-v2 → QuoteWizard handoff with commercial fixture
4. Confirm quote revision / commercial action panel on created quote

---

## 10. PASS Statement

As of **2026-06-09**, branch **`integration/recovered-product-base`** (from recovery @ `4d27aa4`) passes baseline validation (57 backend + 758 frontend focused tests), runtime checks on `:3000/:8000`, and browser smoke on core commercial/operational routes. No blockers required code changes. The recovered product base is ready for **TPL-VOLUMETRIC-LETTERS quote flow stabilization** as the next build.
