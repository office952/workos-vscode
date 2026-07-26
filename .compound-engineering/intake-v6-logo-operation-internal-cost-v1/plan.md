# INTAKE_V6_LOGO_OPERATION_INTERNAL_COST_V1 — Plan

**Phase:** PLAN COMPLETE  
**Plan verdict:** READY_FOR_BOUNDED_IMPLEMENTATION  
**Scope verified:** YES  
**Forbidden scope touched:** NO  
**Accepted HEAD:** 49896b2  
**Branch:** main

---

## 1. Objective

Map workspace-linked **logo operations** from canonical Cost BOM `costable_operations` into EstimatedInternalCost operation lines — without duplicating letters `RULES_BY_TEMPLATE`, without commercial hourly rates, and without reading bindings/recommendation.

```text
workspace_id
  → ProductDefinition (existing)
  → ProductAggregate (workspace-composed)
  → AggregateCostBomBuilderService.build_preview
  → bom.costable_operations
  → EstimatedInternalCostService (logo op mapper)
  → estimated_operation_lines (logo contribution)
```

---

## 2. Accepted truth

| Rule | Status |
|---|---|
| PD compiles technical truth | YES — unchanged |
| PA owns composed operation identity | YES — unchanged |
| Cost BOM owns costable-operation filtering | YES — unchanged |
| EIC consumes workspace-aware Cost BOM (materials) | YES — 49896b2 |
| Logo material internal cost active | YES |
| Logo operation internal cost | **TARGET** |
| `RULES_BY_TEMPLATE` letters path | Stays canonical for letters in V1 |
| Commercial pricing / CPP / Quote / Order / Execution | Outside scope |

---

## 3. Current gap

`EstimatedInternalCostService.build_preview` at lines 624–628 iterates `bom.costable_operations` but **never maps them** to `estimated_operation_lines`. All operation cost today comes from `internal_cost_rules_volumetric_v2.RULES_BY_TEMPLATE` (letters only). Logo namespaced operations exist in workspace Cost BOM (via PA composition + adapter) but contribute **zero** internal operation cost.

---

## 4. Selected architecture

**Option A + C hybrid — EIC consumes only namespaced logo `costable_operations` via thin mapper**

### Selected

| Element | Choice |
|---|---|
| Letters operations | **Unchanged** — `RULES_BY_TEMPLATE` loop (lines 630–659) |
| Logo operations | **New** — map filtered `bom.costable_operations` rows |
| Adapter location | Functions in `estimated_internal_cost_service.py` (no new service file required) |
| Rate source | `internal_cost_rules_volumetric_v2` logo operation unit cost table (new) — **NOT** `workcenter_rates` |
| Quantity source | `formula_id` + segment-enriched payload (extend material V1 enrichment) |
| Dedupe | **None in EIC** — one BOM row → one EIC line |

### Architecture comparison

| Option | Scope | Duplication risk | Migration impact | Safety | Recommendation |
|---|---|---:|---:|---:|---|
| A — Logo BOM ops only | S | LOW | S | HIGH | **SELECT** |
| B — All BOM ops | L | **CRITICAL** | L | LOW | **REJECT** |
| C — Thin mapper | S | LOW | S | HIGH | **SELECT** (with A) |
| D — Defer | — | — | — | — | Reject — debt explicitly scheduled |

---

## 5. Rejected options

- Consume **all** `bom.costable_operations` (duplicates letters with `RULES_BY_TEMPLATE`)
- Use `workcenter_rates` / BOM `pricing_availability` for EIC subtotals (hourly commercial contamination)
- Read `layer_bindings[]` or composition recommendation
- Rebuild ProductDefinition or expand linked templates in EIC
- Add logo rules to `RULES_BY_TEMPLATE` letters tuple (mixes canonical paths)
- Modify Cost BOM adapter or PA composition (forbidden)
- Minutes × hourly rate model for logo (not canonical; seed minutes = 0)
- CommercialPriceProposal, Quote, Order, Execution activation

---

## 6. Exact files / functions (implementation)

### Allowed

| File | Change |
|---|---|
| `backend/services/estimated_internal_cost_service.py` | Logo BOM op mapper; replace noop loop 624–628 |
| `backend/data/internal_cost_rules_volumetric_v2.py` | **Optional owner GO** — `LOGO_OPERATION_INTERNAL_RULES` + dev bridge constants |
| `backend/tests/test_estimated_internal_cost_logo_operations.py` | **NEW** — targeted tests |
| `backend/tests/test_estimated_internal_cost_workspace_linked_logo.py` | Extend operation assertions |
| `backend/tests/eic_patched_bom_builder.py` | Unchanged unless workcenter injection needed |
| Compound artifacts + worklog | Required |

### Forbidden

ProductDefinition, ProductAggregate composition, `aggregate_cost_bom_adapter.py`, binding services, frontend, pricing registry, CPP, Quote, Order, Execution, DB/schema/migrations/seeds, ProductSystem templates.

### New helpers (in EIC service)

```python
def _is_linked_logo_bom_operation(op: CostBomCostableOperation) -> bool:
    # source_template_code == TPL-VOLUMETRIC-LOGO_v1 AND "::" in component_ref

def _linked_logo_operation_segment_key(component_ref: str | None) -> str | None: ...

ARTWORK_OWNED_LOGO_OPERATION_CODES = frozenset({
    "logo_face_print",
    "logo_face_laminate",
    "logo_finish_application",
})

def _estimate_logo_operation_quantity(
    op: CostBomCostableOperation,
    payload: dict,
    values: dict,
) -> tuple[float | int | None, list[str]]: ...

def _resolve_logo_operation_internal_rate(operation_code: str) -> tuple[float | None, str, str]: ...
    # from internal_cost_rules logo table — NOT workcenter

def _build_logo_operation_line_from_bom(...) -> EstimatedInternalCostLine: ...
```

### `build_preview` orchestration change

Replace noop loop:

```python
for op in bom.costable_operations:
    if not _is_linked_logo_bom_operation(op):
        continue
    if op.operation_code in INTERNAL_QC_OPERATION_CODES:
        continue
    rate, rule_code, source = _resolve_logo_operation_internal_rate(op.operation_code)
    quantity, op_warnings = _estimate_logo_operation_quantity(op, payload, values)
    # missing rate → INTERNAL_OPERATION_RULE_MISSING blocker
    # missing quantity → INTERNAL_GEOMETRY_MISSING blocker
    # else append _build_logo_operation_line_from_bom(...)
```

**After** logo loop, run existing `RULES_BY_TEMPLATE` letters loop unchanged.

---

## 7. Letters compatibility

| Rule | Enforcement |
|---|---|
| `RULES_BY_TEMPLATE` not modified for letters rules | No edits to `VOLUMETRIC_V2_OPERATION_RULES` entries |
| Letters BOM ops not consumed | `_is_linked_logo_bom_operation` filter |
| Existing EIC preview tests green | Regression bundle mandatory |
| `scan_hourly_contamination` unchanged | Logo lines use `internal_unit_cost` per unit basis, not hourly |

---

## 8. Logo operation mapping

| BOM `operation_code` | `formula_id` | Basis | Quantity source | Artwork area OK? |
|---|---|---|---|---|
| `logo_face_print` | logo_area | m2 | segment artwork finish | **YES** |
| `logo_face_laminate` | logo_area | m2 | segment artwork finish | **YES** |
| `logo_finish_application` | logo_area | m2 | segment artwork finish | **YES** |
| `logo_face_cnc_cut` | logo_area | m2 | segment area from PD linked segment | NO |
| `logo_back_cut` | logo_area | m2 | segment area from PD linked segment | NO |
| `logo_return_forming` | logo_perimeter | ml | segment perimeter from PD | NO |
| `logo_return_bonding` | logo_perimeter | ml | segment perimeter from PD | NO |
| `logo_led_install` | logo_led_modules | piece | `emblem_led_module_count` segment | NO |
| `logo_electrical_test` | logo_led_modules | piece | segment LED count | NO |
| `logo_mounting_template_cut` | logo_area | m2 | segment area | NO |
| `logo_mounting_install` | logo_area | m2 | segment area or fixed 1 | NO |

**Line identity:** `code=f"operation_{op.operation_code}"`, `component_code=op.component_ref`, separate lines per segment.

---

## 9. Time / quantity truth

| Rule | Detail |
|---|---|
| No invented minutes | V1 uses quantity × internal_unit_cost (letters model) |
| No letter-area fallback | `letter_face_area_m2` forbidden for logo ops |
| Artwork area boundary | Only `ARTWORK_OWNED_LOGO_OPERATION_CODES` |
| PD enrichment | Extend `_enrich_payload_artwork_finishes_from_pd` or sibling helper for segment `svg_area_m2`, `svg_perimeter_ml`, LED counts from `pd.linked_template_runtime_segments` |
| BOM wins cardinality | If BOM omits op (partial finish), EIC does not fabricate |
| Missing quantity | `INTERNAL_GEOMETRY_MISSING` — not zero |

---

## 10. Rate ownership

| Source | Use in EIC? |
|---|---|
| `internal_cost_rules_volumetric_v2` logo table | **YES** — `internal_unit_cost` per operation_code |
| `workcenter_rates` / BOM `pricing_availability` | **NO** — diagnostic only |
| `pricing_registry` / commercial rules | **NO** |
| Hardcoded zero fallback | **NO** |

**Interim pattern:** Mirror letters `DEV_BRIDGE_*` constants with `DEV_BRIDGE_LOGO_*` per operation_code (owner numeric GO).

**Missing rate:** `INTERNAL_OPERATION_RULE_MISSING` blocker; status partial/blocked per existing `_compute_status`.

---

## 11. Shared operation semantics

| Operation | Shared? | Evidence | EIC expected |
|---|---|---|---|
| Letters `debitare_fata` vs logo `logo_face_cnc_cut` | NO | Different codes/refs | Letters via RULES only |
| Letters `sablon_montaj_cnc` vs `logo_mounting_template_cut` | NO | Different codes | Separate lines if both present |
| `logo_face_print` stanga vs dreapta | NO | Different `component_ref` | Two lines |
| PA `_dedupe_operations` | Canonical | Same key not repeated | EIC trusts BOM count |
| EIC second dedupe | **FORBIDDEN** | — | One BOM row → one line |

---

## 12. Partial semantics

| Condition | Material state | Operation state | EIC status | Warning |
|---|---|---|---|---|
| Finish partial | Letters OK; logo mats omitted | Logo ops omitted from BOM | `partial` | BOM finish-partial |
| Complete finish; missing op rate | Logo mats may compute | Op blockers | `partial` / `blocked` | Per-op blocker |
| Complete finish; missing op geometry | Mats may compute | Op geometry blockers | `partial` | `INTERNAL_GEOMETRY_MISSING` |
| Missing binding | Letters only | No logo ops | unchanged | — |
| Hourly contamination | — | — | `blocked` | contamination |

Logo material + incomplete operation truth → overall `partial` (extend existing partial guard when logo op blockers present and `not contamination`).

---

## 13. Provenance

Preserve via existing schema:

- `EstimatedInternalCostLine.component_code` ← BOM `component_ref`
- `EstimatedInternalCostLine.source` ← `internal_cost_rules_volumetric_v2:logo_op:{code}` or inventory-style string
- `EstimatedInternalCostPreview.provenance` — extend `aggregate_cost_bom` detail with logo operation count
- `input_summary.workspace_id` — already present

No new public schema fields unless implementation proves indispensable (plan: **avoid**).

---

## 14. Duplicate prevention

1. **Filter:** Only `_is_linked_logo_bom_operation(op)`.
2. **Letters isolation:** Do not consume non-logo BOM operations.
3. **No EIC dedupe** by operation_code alone.
4. **No workcenter rate path** into subtotals.
5. **Artwork boundary** separate from material lines (additive cost, not merged).

---

## 15. Endpoint / service design

**Route:** existing `POST /api/v1/product-system/estimated-internal-cost-preview/{template_code}`  
**Service:** `EstimatedInternalCostService.build_preview` only  
**Writes:** NONE  
**Schema change:** None expected (`EstimatedInternalCostLine` already supports operation lines)

---

## 16. Commercial boundary

Permitted: internal unit costs, blockers, warnings, partial status.  
Forbidden: markup, margin, VAT, discount, commercial hourly, CPP, Quote, Order, Execution, DB writes.

---

## 17. Test plan

### New file: `backend/tests/test_estimated_internal_cost_logo_operations.py`

| # | Test |
|---|---|
| 1 | EIC with workspace uses BOM builder (orchestration regression) |
| 2 | Logo BOM op produces operation line with namespaced `component_code` |
| 3 | Two segments → two lines for same `operation_code` |
| 4 | Letters operation lines unchanged vs template-only baseline |
| 5 | No binding/recommendation imports in EIC service |
| 6 | Artwork op uses finish area; CNC op does not use artwork area alone |
| 7 | Missing rate → `INTERNAL_OPERATION_RULE_MISSING`, not zero |
| 8 | Missing geometry → `INTERNAL_GEOMETRY_MISSING` |
| 9 | Partial finish → no logo operation lines |
| 10 | No commercial fields on preview |
| 11 | `scan_hourly_contamination` not triggered by logo lines |
| 12 | POST endpoint workspace with logo ops (blockers or lines) |

### Regression bundle (must stay green)

- `test_estimated_internal_cost_workspace_linked_logo.py`
- `test_estimated_internal_cost_preview.py`
- `test_aggregate_cost_bom_workspace_linked_logo_cost_bom.py`
- `test_product_aggregate_workspace_linked_logo_composition.py`
- `test_product_definition_gradi_composition.py`
- `test_intake_v6_layer_binding_persistence.py`
- `test_selected_layer_refs_runtime_capture.py`
- `test_return_cant_product_truth_bridge.py`
- `test_return_cant_pricing_registry_keys.py`

---

## 18. Runtime verification

`POST /api/v1/product-system/estimated-internal-cost-preview/TPL-VOLUMETRIC-LETTERS_v2`

| Scenario | Logo op lines | Letter ops | Commercial |
|---|---|---|---|
| No workspace | 0 | RULES baseline | NO |
| Letters-only workspace | 0 | unchanged | NO |
| Two logos complete | >0 or blockers | unchanged | NO |
| Partial finish | 0 | unchanged | NO |
| Missing internal rates | blockers | unchanged | NO |

Report: Method, URL, Request, HTTP, Workspace, Writes NONE, line counts, warnings, blockers.

---

## 19. Rollback

Single-commit revert of EIC service + internal_cost_rules logo table + tests. No DB migration. No API contract change. Letters path untouched → low rollback risk.

---

## 20. Implementation sequence (/ce-work)

1. Add logo internal rate table to `internal_cost_rules_volumetric_v2.py` (owner numeric GO or placeholder blockers).
2. Add helpers + constants to `estimated_internal_cost_service.py`.
3. Replace noop BOM op loop with logo mapper.
4. Extend PD payload enrichment for segment geometry (non-artwork ops).
5. Adjust partial status when logo op blockers exist.
6. Add tests + extend workspace linked logo tests.
7. Compound validation/review/worklog/commit.

**Estimated touch:** ~150–220 LOC in EIC + ~80 LOC rules + ~400 LOC tests.

---

## 21. Review checklist (pre-commit)

- [ ] One architecture (A+C)
- [ ] No binding read
- [ ] No recommendation read
- [ ] No PD rebuild beyond existing preview
- [ ] No parallel operation graph
- [ ] Letters costs not duplicated
- [ ] Logo segment identity preserved
- [ ] Shared semantics explicit (no EIC dedupe)
- [ ] Missing minutes/qty explicit
- [ ] Missing rates explicit
- [ ] No zero fallback
- [ ] Artwork area boundary explicit
- [ ] Commercial pricing excluded
- [ ] No DB writes
- [ ] Tests specific
- [ ] Rollback possible

---

## 22. Owner decisions required before /ce-work

| ID | Decision | Block implementation? |
|---|---|---|
| DEC-LOPS-ARCH-01 | Logo BOM ops only + thin mapper | NO |
| DEC-LOPS-01 | Internal rate numeric table (dev bridge OK?) | **YES for meaningful subtotals** — structure OK with blockers |
| DEC-LOPS-02 | Quantity boundary (DEC-EIC-03 extension) | NO |
| DEC-LOPS-03 | All BOM-present logo ops in V1 | NO |
| DEC-LOPS-04 | No EIC dedupe | NO |
| DEC-LOPS-05 | Partial semantics | NO |

**Owner GO recommendation:** Approve architecture + quantity boundary; approve interim dev-bridge logo operation unit costs OR explicitly accept blocker-only previews until 7I.

---

## 23. Forbidden scope check

| Area | Planned touch |
|---|---|
| frontend | NO |
| ProductDefinition | NO |
| ProductAggregate | NO |
| Cost BOM adapter | NO |
| bindings / recommendation | NO |
| pricing registry | NO |
| CPP / Quote / Order / Execution | NO |
| DB / migrations / seeds | NO |

---

## PLAN REVIEW GATE

| Check | Pass |
|---|---|
| One architecture selected | YES — A+C |
| No binding read | YES |
| No recommendation read | YES |
| No PD rebuild | YES |
| No parallel operation graph | YES |
| Letters not duplicated | YES |
| Segment identity preserved | YES |
| Shared semantics explicit | YES |
| Missing truth explicit | YES |
| No zero fallback | YES |
| Artwork boundary explicit | YES |
| Commercial excluded | YES |
| No DB writes | YES |
| Tests specific | YES |
| Rollback possible | YES |

**Plan verdict:** **READY_FOR_BOUNDED_IMPLEMENTATION**

**Central question verdict:** YES — bounded logo BOM consumption is architecturally sound.

---

## 24. Next command

```
/ce-work mode:return-to-caller .compound-engineering/intake-v6-logo-operation-internal-cost-v1/plan.md
```

Owner must confirm **DEC-LOPS-01** numeric rates (or accept blocker-only interim).
