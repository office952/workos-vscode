# QUOTEWIZARD COMMERCIAL PATH AUDIT

Date: 2026-07-01

## 1. Verdict

PASS

QuoteWizard was traced end-to-end across frontend, backend, and runtime-safe DB probe.

High-confidence conclusion:

- QuoteWizard does contain a real backend quote-pricing write path, but it is the generic `QuoteOrchestrator` cost-plus route, not the V6 `CommercialPriceProposal` route.
- QuoteWizard also contains frontend-only preview math for volumetric flow.
- In the current local environment, the volumetric QuoteWizard backend write path is runtime-broken before persistence.
- QuoteWizard does not solve the current V6 commercial blockers and does not replace owner-approved V6 commercial rules.

Final recommendation: `D. OWNER_DECISIONS_STILL_REQUIRED`.

## 2. QuoteWizard Frontend Trace

### Entry points

- Main entry component: `frontend/src/components/workos/QuoteWizard.tsx`
- Volumetric branch entry: `frontend/src/components/workos/VolumetricLettersQuoteFlow.tsx`
- Quotes page launcher: `frontend/src/pages/Quotes.tsx`

### High-level flow

1. `Quotes.tsx` opens `QuoteWizard` from the Oferte page.
2. `QuoteWizard.tsx` loads templates and optional intake metadata.
3. If the selected/preferred template is volumetric letters, `QuoteWizard` exits early into `VolumetricLettersQuoteFlow`.
4. Volumetric flow first runs read-only cost simulation via `costSimulationApi.simulate()`.
5. The right rail shows a local commercial preview using `computeCommercialPreviewBreakdown(...)`.
6. When the gate allows it, the user clicks `Creează ofertă comercială`.
7. That button calls `priceQuote(...)` -> `POST /api/v1/entities/quotes/price`.
8. On success, the backend response is used to refresh the quotes list and open the created quote.
9. The Oferte page then shows totals from persisted quote columns via `mapQuoteFromDB()`.

### Frontend step table

| UI step/component | User input | Calculation source | Backend endpoint called | Response field used | Persisted to DB? | Risk | Useful for V6? |
|---|---|---|---|---|---|---|---|
| `QuoteWizard` step 1 | client name, template | none | template list wrapper via `productTemplatesApi.list(...)` | template rows | no | metadata only | reference only |
| `QuoteWizard` step 2 | quantity, width, height, depth | none | none | local state | no | none | reference only |
| `QuoteWizard` step 3 | quote_input fields | none | optional intake lookup via `intakesApi.list(...)` | intake row / id | no | metadata only | reference only |
| `QuoteWizard` step 4 generic flow | margin, VAT display, discount | backend pricing only | `POST /api/v1/entities/quotes/price` | `result.snapshot.price`, `result.quote_id` | yes, on success | generic cost-plus path, not V6 rules | limited pattern reuse only |
| `VolumetricLettersQuoteFlow` simulate | geometry, finish, PSU, mounting, text, technical override | backend cost simulation | `POST /api/v1/product-system/simulate-cost` | `simulationResult.cost_result`, `simulationResult.readiness`, `simulationResult.blocked_reasons` | no | read-only partial totals can be mistaken for official price | reference only |
| `VolumetricLettersQuoteFlow` sidebar preview | margin, VAT, discount over simulated production cost | frontend-only `computeCommercialPreviewBreakdown(...)` | none | local preview values | no | can be mistaken for official quote total if copied | no |
| `VolumetricLettersQuoteFlow` create commercial quote | same volumetric quote_input + pricing | backend generic quote pricing | `POST /api/v1/entities/quotes/price` | `commercialResult.quote_id`, `commercialResult.quote_code`, `commercialResult.snapshot` | yes, if endpoint succeeds | current local path crashes before write | not as V6 authority |
| `Quotes.tsx` quote cards/detail | none | persisted DB fields only | quotes list/detail wrappers | `grand_total`, `subtotal`, `total_before_vat`, `vat`, `line_items` | already persisted | shows zero until quote row is actually written | yes, display path only |

### Frontend findings

- `QuoteWizard.tsx` explicitly says: the wizard never computes costs locally for the generic flow; it sends data to `POST /api/v1/entities/quotes/price`.
- That statement is not true for the volumetric sidebar preview. The volumetric flow imports and uses `frontend/src/lib/volumetricCommercialPreview.ts` for local preview math.
- The local volumetric preview is clearly marked as estimate only: `Estimare internă; oferta finală este calculată la creare.`
- The created quote success path depends on the backend response; it does not write quote totals locally.
- `Quotes.tsx` shows persisted totals from quote rows, not simulation preview state.
- Manual override fields do exist in volumetric flow: advanced technical override, margin, discount, mounting system, face finish, template area, PSU, geometry fields.

## 3. Backend Endpoints Called

### Endpoint table

| Endpoint | Router function | Service | Writes DB? | Writes totals? | Pricing source | Can produce non-zero quote? | Safe for V6? | Notes |
|---|---|---|---|---|---|---|---|---|
| `POST /api/v1/product-system/simulate-cost` | `simulate_cost` in `backend/routers/product_system_cost_simulation.py` | `ProductSystemCostSimulationService.simulate` | no | no | `QuoteOrchestrator.build_snapshot()` in read-only mode | no persisted quote; preview only | no as official price source | explicit `persisted=false`, `no_persist=true` |
| `POST /api/v1/entities/quotes/price` | `price_quote` in `backend/routers/quotes.py` | `QuoteOrchestrator.create_with_registry()` + `build_snapshot()` + `QuotesService.create()` | yes | yes | generic cost-engine total cost plus margin/discount/VAT | yes by design | no for V6 as-is | creates new quote row in `status='priced'` |
| `POST /api/v1/entities/quotes/{quote_id}/price` | `price_existing_draft_quote` in `backend/routers/quotes.py` | same generic orchestrator path + in-place update | yes | yes | generic cost-engine total cost plus margin/discount/VAT | yes by design | no for V6 as-is | reprices eligible existing quote |
| template list wrapper | frontend `productTemplatesApi.list(...)` | generated entity client | read-only | no | none | n/a | yes | metadata source only |
| intake lookup wrapper | frontend `intakesApi.list(...)` | generated entity client | read-only | no | none | n/a | yes | metadata source only |

### Backend pricing path traced from QuoteWizard

`QuoteWizard / VolumetricLettersQuoteFlow`

-> `priceQuote(...)`

-> `POST /api/v1/entities/quotes/price`

-> `QuoteOrchestrator.create_with_registry(db)`

-> `QuoteOrchestrator.build_snapshot(...)`

-> cost result built from ProductSystem + CostEngine / aggregate BOM path

-> `_apply_commercial(total_cost, pricing)`

-> `QuotesService.create(...)`

-> persisted `quotes.subtotal`, `quotes.total_before_vat`, `quotes.vat`, `quotes.grand_total`, `quotes.line_items`, `quotes.status='priced'`

### Exact commercial formula used by generic QuoteWizard backend path

From `backend/services/quote_orchestrator.py`:

- `net_before_discount = total_cost * (1 + margin)`
- `net = net_before_discount * (1 - discount)`
- `gross = net * (1 + vat)`

This is cost-plus pricing over `total_cost`, not `CommercialPriceProposal` line pricing.

### Important backend-authority findings

- `POST /api/v1/entities/quotes/price` is backend-authoritative and does write quote totals.
- It does not call `CommercialPriceProposalService`.
- It does not call `intake_v6_priced_quote_dry_run_service`.
- It is not based on V6 commercial rules such as `mp/ml/buc/set/lucrare/service/manual_owner_review`.
- It uses `QuoteOrchestrator` and CostEngine totals, including estimated operation time in the cost trace.

## 4. Runtime / DB Behavior

### Safe probe method

A runtime-safe probe was executed on a copied SQLite file, not on the live `backend/dev.db`.

Method:

1. Copy `backend/dev.db` to a temp SQLite file.
2. Point SQLAlchemy to that copy only.
3. Call the real router function `price_quote(...)` with a volumetric payload.
4. Inspect quotes before and after.

Quote `#6` was not touched.

### Probe A — ACP template

- Attempted template: `TPL-ACP-LIGHT-ROUTED`
- Result: template not found in local DB copy
- DB mutation: none

### Probe B — volumetric QuoteWizard path

- Template: `TPL-VOLUMETRIC-LETTERS_v2`
- Endpoint path mirrored: `POST /api/v1/entities/quotes/price`
- Before: zero rows for client `QuoteWizard Audit Client`
- Result: runtime exception before persistence
- After: still zero rows for client `QuoteWizard Audit Client`

Traceback root:

- `routers/quotes.py::price_quote`
- `prepare_aggregate_price_context(...)`
- `aggregate_cost_bom_adapter.py::_check_workcenter_pricing(...)`
- failure: `TypeError: '<=' not supported between instances of 'dict' and 'int'`

Local classification:

- the current local volumetric QuoteWizard backend path is runtime-broken before quote persistence;
- therefore no non-zero quote was written in the safe runtime probe;
- this confirms QuoteWizard volumetric create-price is not currently a proven working commercial path in this environment.

### Persisted quote write semantics when the endpoint does succeed

From `backend/routers/quotes.py` the generic create-price route persists:

- `status = 'priced'`
- `line_items = serialized snapshot wrapper`
- `subtotal = snapshot.price.net`
- `total_before_vat = snapshot.price.net`
- `vat = snapshot.pricing.vat_pct`
- `grand_total = snapshot.price.gross`
- `margin_pct = snapshot.pricing.margin_pct`
- `discount_pct = snapshot.pricing.discount_pct`

This proves the route is meant to write quote totals to DB, even though the local volumetric runtime path currently failed before write.

## 5. Does QuoteWizard Produce Real Non-Zero Quote Totals?

Answer: `PARTIAL / NOT PROVEN FOR VOLUMETRIC IN THIS ENVIRONMENT`.

What is true:

- QuoteWizard does call a backend endpoint that is designed to create a priced quote row with non-zero totals.
- The quotes page consumes persisted quote totals from DB once such a write succeeds.

What is not proven:

- No existing quote in local DB has positive `grand_total`.
- The safe runtime probe for the live volumetric QuoteWizard path crashed before persistence.
- Therefore QuoteWizard did not produce a successful non-zero persisted volumetric quote during this audit.

Conclusion:

- generic mechanism exists;
- local volumetric QuoteWizard runtime path is broken;
- V6 cannot rely on it as current commercial truth.

## 6. Comparison to V6 Blockers

| V6 blocker | Does QuoteWizard have a rule for this? | Basis used there | Backend-authoritative? | Extractable into V6 rules? | What must not be copied |
|---|---|---|---|---|---|
| `COMMERCIAL_BASIS_UNKNOWN` | no explicit commercial rule | generic total-cost markup | partially, but not as commercial-rule basis | no direct extraction | do not infer `ml` vs `m2` from total-cost path |
| `DEBITARE_SPATE_BASIS_ML_VS_M2` | no explicit owner basis decision found | cost-engine / aggregate BOM cost path | backend path exists, but not as commercial basis | no | do not convert internal cut-cost math into client basis decision |
| `SABLON_FOREX_COMMERCIAL_PRICE` | no explicit separate commercial rule found | volumetric flow has `mounting_template_enabled` and `mounting_template_area_m2`, but not owner commercial line logic | frontend captures inputs; backend prices generically | only as input signal, not as rule | do not copy frontend checkbox/area as official commercial line price |
| `AMBALARE_COMMERCIAL_RULE` | no explicit packaging commercial rule found | absorbed inside generic cost/capability model if at all | not as explicit commercial rule | no | do not treat missing packaging line as solved by generic total-cost markup |
| `MONTAJ_COMMERCIAL_RULE` | no explicit mounting commercial rule found | `mounting_system` input exists | input only, not owner-approved commercial pricing contract | no | do not copy mounting inputs as finished commercial rule |
| missing documented unit prices | no documented client unit-price catalog found in QuoteWizard path | uses `total_cost` then markup | backend-authoritative for generic quote row, not for V6 rule catalog | no | do not substitute cost-plus totals for owner-approved `RON/ml`, `RON/m²`, `RON/buc` rules |

### Blocker conclusion

QuoteWizard does not resolve the V6 blocker class.

It does not provide:

- explicit commercial basis decisions for volumetric client lines;
- owner-approved documented unit prices per V6 commercial module;
- a backend `CommercialPriceProposal` output that can replace V6 commercial rule implementation.

## 7. Reusable Logic for V6

### Classification table

| Classification | File/function | Exact logic | Inputs | Pricing basis | Outputs | Target V6 destination | Test needed |
|---|---|---|---|---|---|---|---|
| `F. USEFUL_BUT_NEEDS_NEUTRAL_SERVICE_EXTRACTION` | `backend/routers/quotes.py::price_quote` | backend persistence guard for priced quote write | template, user_config, pricing, quote_input | generic cost-plus | persisted quote row | V6 write boundary patterns only | route/service test proving V6 source guard |
| `F. USEFUL_BUT_NEEDS_NEUTRAL_SERVICE_EXTRACTION` | `backend/routers/quotes.py::price_existing_draft_quote` | in-place quote revision/update mechanics | quote id + pricing payload | generic cost-plus | updated quote row, revision history | V6 repricing lifecycle pattern only | V6 reprice guard tests |
| `F. USEFUL_BUT_NEEDS_NEUTRAL_SERVICE_EXTRACTION` | `backend/services/product_system_cost_simulation_service.py::simulate` | read-only preview with explicit `persisted=false` trace | template_id, quote_input, pricing, intake_id | generic cost preview | simulation DTO | V6 read-only preview discipline | V6 preview no-persist tests |
| `B. FRONTEND_PREVIEW_ONLY_REFERENCE` | `frontend/src/lib/volumetricCommercialPreview.ts::computeCommercialPreviewBreakdown` | local margin/discount/VAT arithmetic over production cost | production cost, margin, VAT, discount | frontend-only cost-plus preview | preview subtotal/TVA/total | none as authority; UI hint only | none for V6 authority |
| `B. FRONTEND_PREVIEW_ONLY_REFERENCE` | `frontend/src/components/workos/VolumetricLettersQuoteFlow.tsx::CommercialPricingPreviewBreakdown` | displays local estimate from simulation total | simulated production cost | frontend-only | sidebar preview | none | none |
| `E. OLD_GENERIC_QUOTE_PATH_NOT_SAFE_FOR_V6` | `backend/services/quote_orchestrator.py::_apply_commercial` | `total_cost -> markup -> VAT` quote math | total_cost, margin, discount, VAT | cost-plus | net/gross/final | none for V6 commercial truth | only legacy regression coverage |
| `G. NOT_RELEVANT_TO_V6` | `VolumetricLettersQuoteFlow` advanced technical override UI | operator editing convenience | geometry/finish text fields | none | adjusted quote_input | none | none |

### Reusable summary

Reusable for V6:

- backend write-guard patterns;
- explicit read-only preview contract patterns;
- success-path UI refresh/open-created-quote mechanics.

Not reusable as V6 commercial truth:

- cost-plus quote math;
- frontend preview totals;
- aggregate BOM/workcenter-rate dependency as a replacement for commercial rules.

## 8. What Must NOT Be Reused

- Do not reuse `frontend/src/lib/volumetricCommercialPreview.ts` as official V6 totals.
- Do not copy the volumetric sidebar preview into quote columns.
- Do not treat `QuoteOrchestrator._apply_commercial(total_cost, pricing)` as the V6 commercial rule engine.
- Do not replace `CommercialPriceProposalService` with aggregate BOM total-cost markup.
- Do not treat `mounting_system`, `mounting_template_enabled`, or technical override fields as solved commercial rules.
- Do not depend on the current volumetric QuoteWizard runtime path for production V6 pricing; the local runtime probe shows it is broken before persistence.
- Do not roll V6 back to V2/V4 placeholder or generic QuoteWizard frontend calculations.

## 9. Final Recommendation

`D. OWNER_DECISIONS_STILL_REQUIRED`

Reason:

1. QuoteWizard does not provide a backend `CommercialPriceProposal` path for V6.
2. The backend path it uses is generic cost-plus pricing, not V6 client-rule pricing.
3. The volumetric QuoteWizard flow also contains frontend-only preview math.
4. The local volumetric create-price runtime path is currently broken before DB persistence.
5. None of the traced QuoteWizard logic resolves the current V6 blockers around commercial basis and documented unit prices.

Secondary classification note:

- there is a generic backend price endpoint that can write quote totals;
- however it is not safe to recommend `C. QUOTEWIZARD_GENERIC_PRICE_ENDPOINT_CAN_BE_ADAPTED` as the primary route until owner-approved V6 commercial rule decisions exist and the pricing source is changed from cost-plus to V6 commercial rules.

## 10. Next Safe Slice

Next safe slice:

1. Fix the runtime defect in the generic volumetric QuoteWizard path only as a traceability/legacy hardening issue if owner wants that path kept alive.
2. Do not route V6 commercial truth through QuoteWizard frontend preview or generic cost-plus quote math.
3. Continue with owner decision capture for V6 commercial rules:
   - debitare spate basis;
   - documented unit prices for critical commercial lines;
   - forex sablon rule;
   - ambalare rule;
   - montaj rule.
4. Keep V6 backend authority in `CommercialPriceProposalService` + `intake_v6_priced_quote_dry_run_service` + guarded V6 write service.
5. If any QuoteWizard backend mechanics are reused, extract only neutral persistence/preview patterns, not pricing formulas.

## 11. Forbidden Confirmation

Confirmed:

- no implementation first
- no rollback to V2/V4
- no V6 dependency on QuoteWizard frontend calculations
- no copied totals
- no fake totals
- no hardcoded totals
- no frontend preview copied into official totals
- no order
- no ProductAggregate implementation work in this slice
- no Task Graph
- no ExecutionPlan
- no Employee Mobile

## 12. Files Inspected

- `frontend/src/components/workos/QuoteWizard.tsx`
- `frontend/src/components/workos/VolumetricLettersQuoteFlow.tsx`
- `frontend/src/api/quotes.ts`
- `frontend/src/api/costSimulation.ts`
- `frontend/src/lib/volumetricCommercialPreview.ts`
- `frontend/src/lib/dataStore.ts`
- `frontend/src/pages/Quotes.tsx`
- `backend/routers/quotes.py`
- `backend/routers/product_system_cost_simulation.py`
- `backend/services/quote_orchestrator.py`
- `backend/services/product_system_cost_simulation_service.py`
- `backend/services/aggregate_cost_bom_price_bridge.py`
- `backend/services/aggregate_cost_bom_adapter.py`
- `backend/services/commercial_price_proposal_service.py`
- `backend/models/quotes.py`

## 13. Runtime Probe Notes

- Live DB was not modified.
- Quote `#6` was not modified.
- Runtime probe used a copied SQLite database.
- Volumetric create-price path on copied DB failed with:
  - `TypeError: '<=' not supported between instances of 'dict' and 'int'`
  - root area: aggregate BOM workcenter pricing check
- No quote row was created in the copied DB during the failed volumetric probe.