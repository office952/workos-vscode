# Build 3 — Subset activation and output isolation

| Field | Value |
|-------|-------|
| Task | BUILD 3 — SUBSET ACTIVATION AND OUTPUT ISOLATION |
| Date | 2026-07-17 |
| Repo | `C:/w/psiso` |
| Branch | `feature/product-system-active-path-isolation-v1` |
| Start HEAD | `5fbea48` (Build 2 worklog note) |
| End HEAD | *(filled after commit)* |
| Verdict | `BUILD3_SUBSET_ISOLATION_COMPLETE_WITH_GUARDS` |

## Objective

Turn Build 2 modular composition into functional subset modularity:

- full product (golden regression)
- FACE only
- CANT only
- FACE + CANT (interface bonding + adhesive once)

Law: inactive module ⇒ zero requirements / warnings / blockers / materials / measurements / operations / CPP / execution candidates (except explicit provenance dependencies).

## Scope (GO)

- SUBSET ACTIVATION
- ACTIVE SCOPE
- OUTPUT ISOLATION
- FACE+CANT INTERFACE

## Explicit exclusions (no GO)

New products/families, SVG Analyzer redesign, ACM, Logo standalone, sold FINISH/MOUNTING/packaging, Pricing Registry 7I, snapshot freeze, order creation, task materialization, Employee Mobile, schema/migration/seed, formula/price changes.

## Agents (Compound Engineering)

| Agent | Role | Mode |
|-------|------|------|
| A | Scope UI + persistence | read-only research |
| B | Product System contracts | read-only research |
| C | ProductDefinition activation | read-only research |
| D | ProductAggregate filtering | read-only research |
| E | FACE+CANT interface | read-only research |
| F | CPP isolation | read-only research |
| G | Compatibility | read-only research |
| H | Tests | read-only research |
| I | Adversarial | read-only research |
| Writer | Single implementation pass | write |
| Fix | Single fix pass (`offer_scope=null` crash) | write |

## Architecture

Preferred path (no schema):

```text
offer_scope { mode, sold_modules }
  → compile_active_scope
  → composition_excluded_operations + composition_excluded_materials
  → Aggregate filter + live-calc filter + CPP module gates
  → FE presets + sold-scope field visibility + Review summary
```

Interface FACE+CANT:

- materials: `MAT-ADEZIV-CANT-LITERE`, `adhesive_return_to_face`
- ops: `return_face_bonding` / `RETURN_PROFILE_FACE_BONDING`
- active only when sold includes both `FACE` and `RETURN-CANT` (or full-product legacy)
- provenance owner: `interface_face_cant`

Inactive value policy: **Option A — ignore downstream** (values may remain in payload; must not activate modules/outputs). No silent purge; no schema.

## Request modes

| Mode | Sold modules |
|------|----------------|
| `full_product` | `[]` (legacy full graph) |
| `component_subset` | `FACE` / `RETURN-CANT` / `FACE+RETURN-CANT` |

Contract flag: `subset_activation_enabled=true`, version `1.4.0-subset-activation`.

## Component selector (UI)

Same Intake V6 routes. Presets with diacritics:

- Produs complet
- Doar față
- Doar cant
- Față + cant

Visible in analyzer (`IntakeV6OfferScopePanel`) and Review (`IntakeV6OfferScopeReviewSummary`).

## Form contract filtering

Build 2 composition authority kept. Specialized adapters remain. FE sold-scope visibility continues to hide inactive fields; inactive readiness counts use scoped incompleteness helpers.

## Full-product regression

Historical CPP fingerprint unchanged: `debitare_fata quantity = 20.9727`.

Live disposable full-product WS emits adhesive + bonding + face/cant CPP lines (see evidence).

## E2E scenarios (disposable)

Source clone: Build 2 fresh WS `ce44f3f2-1018-4b8c-9011-92a1c402daaf` (read-only).

| Scenario | Workspace ID | Verdict |
|----------|--------------|---------|
| full_product | `9f8b1b6e-780c-4299-9e5f-76f0de324578` | PASS |
| face_only | `c7f8c5d3-7b16-433c-9a73-29fdada3561a` | PASS |
| cant_only | `65cc2218-3703-49c4-ae16-bf55046c7e07` | PASS |
| face_cant | `dc38cf46-7e91-4e15-8b6c-04b9e6d692a4` | PASS |

Evidence: `docs/audits/_evidence/2026-07-17_intake_v6_build3_subset_isolation/`.

Assertions:

- FACE only: no cant CPP, no adhesive, no bonding
- CANT only: no face CPP, no adhesive, no bonding
- FACE+CANT: adhesive present ≤1, face+cant CPP
- Full: adhesive present

UI: presets, Review “Componente active / Nu sunt incluse”, scope switching, hard refresh, responsive 1440/1280/768 — PASS.

## Adversarial findings + fix pass

1. **UI hide vs backend** — countered by Aggregate/live-calc/CPP probes per scenario.
2. **CANT includes adhesive** — fixed by `composition_excluded_materials` + Aggregate/live-calc filters.
3. **`offer_scope: null` crash** — saving `full_product` after clone crashed (`NoneType.get`) because key existed with null value. Fixed in `save_offer_scope_for_intake_v6_workspace` with isinstance guard. Test: `test_offer_scope_null_payload_safe.py`.

## Compatibility

- Historical golden WS untouched
- Build 2 reference WS untouched
- Legacy `active=[]` / full_product passthrough retained
- No snapshot/order/task writes

## Guards / blockers remaining

- Fixture rebuild perimeter `21.1675` ≠ live historical `20.9727` (Build 1 guard; do not equalize)
- Thin seed BOM suite `test_offer_scope_bom_eic_cpp_filter.py` remains environment-thin for FACE identity rows in unit fixture (pre-existing vs live Aggregate); live E2E is authority for Build 3 isolation
- BACK/LIGHTING/TEMPLATE/STRUCTURE/packaging-only subsets still blocked by owner GO
- Ownership of adhesive still physically under `modelare_cant` with interface provenance metadata — full ownership move deferred (compatibility bridge documented)

## Tests

Backend (targeted green):

- `test_intake_v6_build3_subset_isolation.py`
- `test_offer_scope_null_payload_safe.py`
- `test_active_scope_resolver_service.py`
- `test_intake_v6_build2_full_product_composition.py` (subset flag updated for Build 3)
- `test_intake_v6_modular_form.py`
- `test_intake_v6_golden_parity_harness.py` (cant-only spec unskipped)
- `test_product_aggregate_active_scope_filter.py`

Frontend:

- `intakeV6OfferScopePresets.test.ts`
- `IntakeV6OfferScopePanel.test.tsx`
- `resolveReviewTabsFromModularContract.test.ts`

## Commit

Recommended: `feat(intake-v6): isolate component subsets across product spine`

Exact-path staging only.

## Next safe step

Owner review of full-product regression + subset isolation. **Do not start Build 4** (snapshot/execution) without new GO.
