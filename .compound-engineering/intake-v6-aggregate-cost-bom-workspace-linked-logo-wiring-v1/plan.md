# INTAKE_V6_AGGREGATE_COST_BOM_WORKSPACE_LINKED_LOGO_WIRING_V1 — Plan

**Phase:** PLAN COMPLETE  
**Plan verdict:** READY_FOR_BOUNDED_IMPLEMENTATION  
**Scope verified:** YES  
**Forbidden scope touched:** NO  
**Accepted HEAD:** bee9757

---

## 1. Objective

Wire the **workspace-composed ProductAggregate** (letters + linked logo segments, bee9757) into the **existing read-only Cost BOM adapter** so:

```text
workspace_id
  → ProductDefinition (already workspace-aware in builder)
  → ProductAggregate.build_for_workspace (NOT wired today)
  → AggregateCostBomAdapter.build
  → technical BOM preview (no commercial price, no persistence)
```

Smallest safe change: orchestration fix + bounded adapter module-activation for linked-logo rows already present in aggregate.

---

## 2. Accepted truth

| Rule | Status |
|---|---|
| ProductDefinition is technical compiler | YES — unchanged |
| ProductAggregate consumes PD output | YES — bee9757 |
| `logo-stanga` / `logo-dreapta` separate instances | YES |
| Same template `TPL-VOLUMETRIC-LOGO_v1` twice OK | YES |
| Missing binding → no logo components | YES |
| Missing finish → partial structure + warning, no logo materials/ops | YES |
| ProductAggregate does not calculate commercial price | YES |
| Pricing / Quote / Order / Execution unchanged | YES |

---

## 3. Selected adapter architecture

**Option B/C hybrid — narrow workspace Cost BOM orchestration + reuse existing adapter**

```text
AggregateCostBomBuilderService.build_preview(template, workspace_id=?)
  pd  = ProductDefinitionBuilderService.build_preview(template, workspace_id)
  agg = workspace_id
          ? ProductAggregateService.build_for_workspace(template, workspace_id)
          : ProductAggregateService.build(template)
  return AggregateCostBomAdapter.build(product_definition=pd, aggregate=agg, …)
```

### Why not pure Option A

Adapter already accepts PA — but **builder never passes workspace-composed PA**. Option A is the target **data contract**; Option B/C describes the **orchestration fix**.

### Rejected options

| Option | Reason |
|---|---|
| Cost BOM reads bindings | Duplicate truth; forbidden |
| Cost BOM reads recommendation | Forbidden |
| Cost BOM rebuilds ProductDefinition | Forbidden |
| Cost BOM independently expands linked templates | Duplicate PA logic |
| Cost BOM generates commercial price | Forbidden |
| New parallel product graph | Forbidden |
| Option B new public `/aggregate/.../cost-bom` route | Unnecessary — existing endpoint sufficient |

### Architecture comparison

| Option | Truth duplication | Code size | API impact | Pricing risk | Recommendation |
|---|---:|---:|---:|---:|---|
| A — PA object only (builder fix) | 0 | S | 0 | LOW | **SELECT** |
| B — New orchestration service file | 0 | M | 0 | LOW | Acceptable if builder too large — prefer inline builder change |
| C — Extend preview endpoint | 0 | S | 0 | LOW | Same as A (endpoint exists) |
| Reject: binding read | HIGH | — | — | MED | **REJECT** |
| Reject: commercial price in BOM | MED | — | HIGH | CRITICAL | **REJECT** |

---

## 4. Exact files / functions

### Allowed to modify (implementation)

| File | Change |
|---|---|
| `backend/services/aggregate_cost_bom_adapter.py` | `AggregateCostBomBuilderService.build_preview`; helpers `_effective_active_modules`, `_is_linked_logo_row`, `_component_included_in_bom`; optional partial component handling |
| `backend/tests/test_aggregate_cost_bom_workspace_linked_logo_cost_bom.py` | **NEW** — workspace logo BOM tests (reuse PA fixtures) |
| `backend/tests/test_aggregate_cost_bom_adapter.py` | Update `bom_context` fixture: when `workspace_id` set, use `build_for_workspace` |
| `docs/worklog/realignment/2026-07-12_intake_v6_aggregate_cost_bom_workspace_linked_logo_wiring_v1.md` | Worklog |

### Must NOT modify

ProductDefinition, ProductAggregate composition, binding persistence, frontend, DB schema/migrations/seeds, ProductSystem templates, pricing registry, CommercialPriceProposal, Quote, Order, Execution, `aggregate_cost_bom_price_bridge`, EstimatedInternalCostService (v1 scope).

### Reference-only (read)

| File | Purpose |
|---|---|
| `backend/services/product_aggregate_workspace_composition_service.py` | PA output contract |
| `backend/tests/test_product_aggregate_workspace_linked_logo_composition.py` | Fixture payloads |
| `backend/routers/product_system_cost_bom_preview.py` | Existing endpoint |
| `backend/schemas/aggregate_cost_bom.py` | BOM schema |

---

## 5. Input / output contract

### Input (unchanged public API)

```
GET /api/v1/product-system/cost-bom-preview/TPL-VOLUMETRIC-LETTERS_v2?workspace_id={uuid}
```

### Builder internal contract

| Param | PD | Aggregate |
|---|---|---|
| No workspace_id | `build_preview(code)` | `build(code)` |
| With workspace_id | `build_preview(code, workspace_id=…)` | **`build_for_workspace(code, workspace_id)`** |

### Adapter contract (unchanged signature)

```python
AggregateCostBomAdapter.build(
    product_definition: ProductDefinitionPreview,
    aggregate: ProductAggregate,  # MUST be workspace-composed when workspace_id used
    quote_input: dict | None = None,
    material_rates: dict[str, float] | None = None,
    workcenter_rates: dict[str, float] | None = None,
    ...
) -> AggregateExpandedCostBom
```

### Output guarantees

| Field | Behavior |
|---|---|
| `source_context.workspace_id` | Set when workspace PD |
| `costable_components` | Letters + namespaced logo components |
| `costable_materials` | Letters + per-segment logo rows when finish complete |
| `costable_operations` | Same |
| `skipped_items` | module_inactive / geometry_gate / future — not silent drop |
| `warnings` | Includes PA warnings (`LINKED_SEGMENT_FINISH_PARTIAL`, composition applied) |
| `bom_status` | `partial` when geometry/partial logo; `blocked` when critical missing pricing |
| Commercial total fields | **None** |

---

## 6. Material mapping

| Material | Aggregate source | Quantity source | Cost BOM mapping | Partial behavior | Dedupe rule |
|---|---|---|---|---|---|
| Face plexi (letters) | PA letters dossier | PD canonical + geometry keys | `_resolve_material_code` | Unchanged | By material_code + component_ref |
| Print vinyl (logo) | PA logo segment row | formula keys (`logo_area`, segment geometry) | costable_material row | **Omit** when finish partial | Per `component_ref::segment` |
| Laminate (logo) | PA logo segment | same | costable_material | Omit when partial | Per segment |
| Return/cant (letters) | PA lateral module | letters geometry | unchanged | unchanged | letters component_ref |
| Return/cant (logo) | PA logo return module | segment geometry | costable_material | Omit when partial | segment component_ref |
| Backing Forex | letters + logo back | geometry | separate rows | logo omitted if partial | no cross-segment merge |
| LEDs / PSU | letters (+ logo if lit) | module + variant keys | existing variant logic | partial logo: no logo LED rows | definition ≠ double consumption |
| Mounting / consumables | PA parent/child | module active | map if active | partial logo excluded | PA dedupe first |
| Face material (logo) | PA comp_logo_face | segment | map with LOGO template provenance | omit if partial | segment ref |

**Rule:** Quantities come from PA material rows + existing BOM geometry resolution — **no second geometry engine** in this slice.

---

## 7. Operation mapping

| Operation | Class | Aggregate source | Cost BOM behavior | Costable? | Shared? | Partial |
|---|---|---|---|---:|---:|---|
| CNC cutting (letters) | COSTABLE_COMPONENT_OPERATION | PA letters | costable_operations | YES | NO | unchanged |
| CNC/print/laminate (logo) | COSTABLE_COMPONENT_OPERATION | PA logo segment | map per segment | YES | NO | **skip** (absent from PA) |
| Vinyl application | COSTABLE_COMPONENT_OPERATION | PA | map | YES | NO | partial: absent |
| Return forming | COSTABLE_COMPONENT_OPERATION | PA | map | YES | NO | segment-specific |
| Assembly | COSTABLE_COMPONENT_OPERATION | PA | map | YES | sometimes | per component_ref |
| LED install / wiring | COSTABLE_COMPONENT_OPERATION or BLOCKED | PA | map if priced | YES | NO | partial: absent |
| QC / packing | INFORMATIONAL_ONLY or COSTABLE | PA `priced` flag | skip if `priced=False` | varies | NO | unchanged |
| Geometry gates | INFORMATIONAL_ONLY | PA | skipped geometry_gate | NO | — | unchanged |
| Missing tariff ops | BLOCKED_PARTIAL_OPERATION | PA row present | missing_pricing + blocked | NO until rate | — | warning visible |

Classification helper (plan-only, implement inline):

- `priced=False` → skip (existing)
- `geometry_gate` → skip (existing)
- logo op with missing WC rate → `missing_pricing` (existing)

---

## 8. Partial component semantics

| Condition | Aggregate state | BOM rows | Warning | Preview state |
|---|---|---|---|---|
| Complete letters + complete logo | full materials/ops per segment | letters + logo costable rows | composition applied (info) | `ready` or `partial` if geometry gaps |
| Complete letters + partial logo | partial components; no logo mat/ops | letters full; logo components listed; no logo cost lines | `LINKED_SEGMENT_FINISH_PARTIAL` | `partial` |
| Complete letters + missing binding | letters-only aggregate | letters only | none | same as template |
| Letters only workspace | no `::` components | letters only | none | unchanged |
| Missing geometry | PA warnings | rows with missing_geometry keys | geometry warnings | `partial` or `blocked` |
| Missing material mapping | PA row exists | missing_pricing | tariff warning | `blocked` |
| Missing tariff | row exists | missing_pricing entry | explicit | `blocked` |

**Never:** zero-cost complete logo component when finish partial.

Implementation: when `component.status == "partial"` and `"::" in component_id`, include in `costable_components` even if module inactive; materials/ops already absent from PA.

---

## 9. Duplicate prevention

| Concept | Canonical owner | Adapter rule |
|---|---|---|
| Material quantity identity | ProductAggregate row (`component_ref` + `material_code` + `source_template_code`) | One BOM row per PA material row |
| Operation identity | ProductAggregate operation row | One costable op per PA op |
| Module activation | PD letters modules + PA-linked logo modules (effective set) | Do not re-derive from bindings |
| Internal material rate | inventory/pricing dict lookup | Read-only |
| Commercial price | price bridge (forbidden) | Not invoked |

---

## 10. Warnings / readiness

| Warning | Source | BOM impact | Operator? | Technical? |
|---|---|---|---:|---:|
| `LINKED_SEGMENT_FINISH_PARTIAL` | PA | no logo cost lines | YES | YES |
| `WORKSPACE_LINKED_LOGO_COMPOSITION_APPLIED` | PA | logo rows eligible | YES | YES |
| Missing geometry keys | adapter | partial/blocked | YES | YES |
| Missing material rate | adapter | blocked | YES | YES |
| `ACTIVE_MODULE_NO_COST_LINES` | adapter | warning string | YES | YES |

Status mapping:

| Vocabulary | Implementation |
|---|---|
| TECHNICAL_BOM_COMPLETE | `bom_status=ready` |
| TECHNICAL_BOM_PARTIAL | `bom_status=partial` + PA partial warnings |
| TECHNICAL_BOM_BLOCKED | `bom_status=blocked` |
| INTERNAL_COST_* | Out of scope v1 |

---

## 11. Provenance

| BOM row type | Required provenance | Existing support? | Adapter action |
|---|---|---:|---|
| Letter material | `component_ref`, LETTERS template | YES | pass-through |
| Logo material | namespaced `component_ref`, `TPL-VOLUMETRIC-LOGO_v1`, segment in ref | YES | pass-through; don't filter |
| Letter operation | `component_ref`, module | YES | pass-through |
| Logo operation | segment ref + LOGO template | YES | pass-through |
| Costable component | `component_id`, `source_template_code`, `provenance` | YES | include partial logo |

No new public schema fields planned.

---

## 12. Endpoint / service plan

| Option | Public API | Compatibility | Reuse | Mutation | Recommendation |
|---|---:|---:|---:|---:|---|
| A — existing cost-bom-preview + workspace_id | 0 change | HIGH | HIGH | NONE | **SELECT** |
| B — new aggregate/cost-bom route | +1 route | MED | MED | NONE | Reject |
| C — internal service only | 0 | LOW for operators | HIGH | NONE | Reject for v1 |

No POST. No persistence.

---

## 13. Pricing boundary

| Layer | Included? |
|---|---:|
| Technical BOM (this task) | YES |
| Internal cost totals (EIC) | NO — follow-up |
| Commercial pricing | NO |
| Quote/Order/Execution | NO |

Forbidden in implementation: markup, margin, VAT, discount, commercial hourly rate, client price, proposal generation, Quote creation.

---

## 14. Test plan (36 cases)

New file: `backend/tests/test_aggregate_cost_bom_workspace_linked_logo_cost_bom.py`  
Reuse: `_gradi_payload`, `_confirmed_bindings_payload`, `_letters_only_payload` from PA tests (import or shared helper).

### Basic (1–5)

1. Letters-only workspace Cost BOM ≡ template-only BOM (component + material sets).
2. One confirmed logo segment → logo costable materials with segment `component_ref`.
3. Two segments → distinct refs; both present.
4. Same LOGO template twice → two component instances in BOM.
5. Missing binding → no logo BOM rows (same as letters-only).

### Partial (6–10)

6. Missing finish → `LINKED_SEGMENT_FINISH_PARTIAL` in warnings.
7. No print/laminate logo rows when finish partial.
8. Letters BOM still populated.
9. `bom_status` is `partial` (not `ready`).
10. No logo material with `pricing_availability=available` when finish partial.

### Materials (11–15)

11. Print media maps for complete logo segment.
12. Laminate maps for complete segment.
13. Stanga vs dreapta quantities/refs disjoint.
14. Duplicate definition rows in PA (post-dedupe) → single BOM row per PA row.
15. Separate consumption preserved (no merged qty across segments).

### Operations (16–20)

16. Logo component-specific ops appear when finish complete.
17. Shared letter ops not duplicated per segment unless PA has separate rows.
18. Non-priced / informational ops in skipped_items.
19. Missing workcenter rate → missing_pricing entry.
20. No invented `estimated_minutes` in BOM output.

### Provenance (21–23)

21. Logo material `component_ref` contains segment key.
22. Logo rows `source_template_code == TPL-VOLUMETRIC-LOGO_v1`.
23. Letter rows trace to `TPL-VOLUMETRIC-LETTERS_v2`.

### Boundaries (24–29)

24. No commercial total / price fields populated.
25. No Quote/Order side effects (unit test — no DB writes beyond fixture).
26. No workspace payload mutation.
27. Builder calls `build_for_workspace` (mock/spy optional; behavioral assertion sufficient).
28. No recommendation service import in changed files.
29. Adapter does not call `ProductDefinitionBuilderService` internally.

### Regression (30–36)

30. `test_product_aggregate_workspace_linked_logo_composition.py` — pass unchanged.
31. `test_product_definition_gradi_composition.py` — pass.
32. `test_intake_v6_layer_binding_persistence.py` — pass.
33. Selected layer refs tests — pass.
34. Return/cant tests — pass.
35. `test_aggregate_cost_bom_adapter.py` — pass (fixture update).
36. No pricing test modifications.

### Run commands

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_aggregate_cost_bom_workspace_linked_logo_cost_bom.py -q
.\.venv\Scripts\python.exe -m pytest tests/test_aggregate_cost_bom_adapter.py tests/test_product_aggregate_workspace_linked_logo_composition.py -q
```

---

## 15. Runtime verification (post-implementation)

1. Seed volumetric v2 + logo template fixtures (test DB).
2. Create gradi workspace with confirmed bindings + finish.
3. `GET /api/v1/product-system/cost-bom-preview/TPL-VOLUMETRIC-LETTERS_v2?workspace_id={id}` — verify logo rows.
4. Repeat with finish partial — verify partial BOM, no print/laminate logo rows.
5. Omit workspace_id — verify unchanged letters BOM.

---

## 16. Rollback

Revert builder orchestration + adapter helpers + new test file. No migration. Endpoint contract unchanged.

---

## 17. Implementation sequence

1. Add `_effective_active_modules(pd, aggregate, quote_input)` in adapter module.
2. Add `_is_namespaced_linked_logo_component(comp)` helper.
3. Update `_material_module_active` / `_operation_module_active` to use effective modules for linked-logo PA rows (`source_template_code == TPL-VOLUMETRIC-LOGO_v1` or provenance linked_segment).
4. Update costable_components loop: include partial namespaced components.
5. Change `AggregateCostBomBuilderService.build_preview` aggregate branch to `build_for_workspace`.
6. Update `bom_context` fixture in existing tests.
7. Add new workspace linked logo Cost BOM test module.
8. Run targeted pytest (section 14).
9. Write worklog.

Estimated diff: ~80–150 lines production + ~200–350 lines tests.

---

## 18. Review checklist

- [ ] One architecture selected (B/C hybrid)
- [ ] ProductAggregate remains canonical BOM input
- [ ] No ProductDefinition recompilation in adapter
- [ ] No binding read
- [ ] No recommendation read
- [ ] Partial logo semantics explicit
- [ ] No fabricated materials
- [ ] Material dedupe explicit
- [ ] Operation dedupe explicit
- [ ] Provenance preserved
- [ ] Commercial pricing excluded
- [ ] No DB writes
- [ ] No UI
- [ ] Tests specific (36 cases)
- [ ] Rollback documented
- [ ] Owner decisions in decision-log.md

---

## 19. Forbidden scope check

| Area | Planned touch? |
|---|---|
| Frontend | NO |
| ProductDefinition | NO |
| ProductAggregate composition | NO |
| Binding persistence | NO |
| DB schema/migrations/seeds | NO |
| ProductSystem templates | NO |
| Commercial pricing / CPP / Quote / Order / Execution | NO |
| EstimatedInternalCost (v1) | NO |

---

## Plan review gate

**Verdict: READY_FOR_BOUNDED_IMPLEMENTATION**

All required checks pass with noted implementation detail DEC-CBOM-06 (default recommended, soft owner confirm).

**Next command:**

```
/ce-work mode:return-to-caller .compound-engineering/intake-v6-aggregate-cost-bom-workspace-linked-logo-wiring-v1/plan.md
```
