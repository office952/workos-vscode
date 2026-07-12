# INTAKE_V6_LOGO_OPERATION_INTERNAL_COST_V1 — Research

**Phase:** RESEARCH COMPLETE  
**Accepted HEAD:** 49896b2  
**Branch:** main

---

## 1. Repository preflight

| Check | Result |
|---|---|
| Branch | `main` |
| HEAD | `49896b2` — Wire workspace Cost BOM into Estimated Internal Cost |
| Previous task commit | `bcdd14d` — Cost BOM workspace logo wiring |
| Implementation in this phase | **NO** |

### A. Accepted committed state

- EIC delegates BOM to `AggregateCostBomBuilderService.build_preview` when `workspace_id` present.
- Logo **material** internal cost active via `bom.costable_materials` + namespaced row filter.
- Logo **operation** internal cost **absent** — documented debt from 49896b2.

### B. Unrelated dirty files (not touched)

- `.gitignore`, QA screenshots, unrelated worklogs, `IntakeV6LayersOperatorPanel.tsx`, untracked QA folders.

### C. Exact EIC operation code (today)

| Location | Behavior |
|---|---|
| `estimated_internal_cost_service.py:624–628` | Iterates `bom.costable_operations`; skips QC codes only; **appends nothing** |
| `estimated_internal_cost_service.py:630–659` | Builds **all** operation lines from `RULES_BY_TEMPLATE[template]["operations"]` |
| `_build_operation_line` | `quantity` from payload paths in rule; `subtotal = quantity × internal_unit_cost` |
| `scan_hourly_contamination` | Blocks preview if hourly tokens detected |
| `INTERNAL_QC_OPERATION_CODES` | `qc_letters`, `qc_internal_check`, `qc_banner` excluded |

### D. Exact Cost BOM operation code

| Location | Behavior |
|---|---|
| `aggregate_cost_bom_adapter.py:1034–1095` | Maps `aggregate.operations` → `CostBomCostableOperation` |
| Filters | geometry gate, `non_priced`, `module_inactive` (logo bypass via `_is_aggregate_linked_logo_operation`) |
| Fields emitted | `operation_code`, `label`, `workcenter`, `formula_id`, `component_ref`, `mini_module_code`, `provenance`, `source_template_code`, `pricing_availability`, `required_geometry_keys` |
| **Not emitted** | quantity, minutes, unit_cost, shared flag |

### E. ProductAggregate operation provenance

| Location | Behavior |
|---|---|
| `product_aggregate_service.py:_operations_from_rows` | Builds ops from template `operations_json`; `priced=not non_priced` |
| `product_aggregate_workspace_composition_service.py` | Namespaces logo ops per segment; omits ops when finish not confirmed |
| `_dedupe_operations` | Key: `operation_code\|source_template\|component_ref\|provenance` |
| Logo template seed | ~10 ops per full logo aggregate; `estimatedMinutes: 0`; formula_ids: `logo_area`, `logo_perimeter`, `logo_led_modules` |

### F. Pricing / CPP boundaries

| System | Uses BOM operations? | Relation to EIC |
|---|---|---|
| `aggregate_cost_bom_price_bridge.py` | YES — maps to CostEngine rows with workcenter | Commercial path — **outside EIC** |
| `commercial_price_proposal_service.py` | Uses `commercial_rules_volumetric_v2.RULES_BY_TEMPLATE` | Separate commercial rules — **outside EIC** |
| EIC | Ignores BOM ops; uses `internal_cost_rules_volumetric_v2` | Internal unit costs only |

### G. Unexpected changes

None in accepted HEAD scope.

---

## 2. Source inventory

| File / function | Responsibility | Input | Output | Canonical / legacy | Risk |
|---|---|---|---|---|---|
| `EstimatedInternalCostService.build_preview` | EIC aggregation | BOM + PD payload + `RULES_BY_TEMPLATE` | `EstimatedInternalCostPreview` | Canonical EIC entry | HIGH if dual operation graphs |
| `estimated_internal_cost_service.py:624–628` | BOM op scan (noop) | `bom.costable_operations` | nothing | **Gap** | HIGH |
| `RULES_BY_TEMPLATE` (`internal_cost_rules_volumetric_v2`) | Letters internal op rules | payload geometry paths | operation lines | **Letters canonical for EIC** | HIGH if bypassed without filter |
| `_build_operation_line` | Rule → EIC line | `InternalOperationRule`, payload | `EstimatedInternalCostLine` | Letters path | LOW |
| `AggregateCostBomBuilderService.build_preview` | BOM orchestration | workspace_id, template | `AggregateExpandedCostBom` | Canonical BOM | LOW (forbidden to edit) |
| `AggregateCostBomAdapter.build` | PA → BOM rows | aggregate.operations | `costable_operations` | Canonical costable filter | LOW (forbidden to edit) |
| `_is_aggregate_linked_logo_operation` | Logo op eligibility | PA operation row | bool active | Canonical | LOW |
| `compose_from_product_definition` | Workspace PA merge | PD + letters + logo aggregates | composed operations | Canonical graph | LOW (forbidden to edit) |
| `_dedupe_operations` | PA-level dedupe | operation list | deduped list | Canonical shared semantics | MED if EIC re-dedupes |
| `aggregate_cost_bom_price_bridge` | Commercial engine feed | BOM ops | engine operations | Commercial | Must not leak into EIC |
| `commercial_price_proposal_service` | Client price preview | commercial rules | CPP preview | Commercial | Out of scope |

---

## 3. Current EIC operation contract

| Question | Answer |
|---|---|
| Does EIC accept `bom.costable_operations` today? | **NO** — loop is empty aside from QC skip |
| Does it ignore them? | **YES** |
| Builds operations only from `RULES_BY_TEMPLATE`? | **YES** (letters template) |
| Letters operation costs duplicated elsewhere in EIC? | **NO** (single RULES path) |
| Requires minutes? | **NO** — uses quantity × `internal_unit_cost` |
| Requires workcenter? | **NO** for costing (workcenter only warned if present in registry) |
| Requires operation rate? | **YES** — `internal_unit_cost` on rule; missing → `INTERNAL_OPERATION_RULE_MISSING` |
| Missing time treated as zero? | **NO** — quantity None → blocker or no subtotal |
| Missing rate treated as zero? | **NO** — explicit blocker |
| Preserves `component_ref`? | On rule-defined lines only (`component_code` from rule) |
| Preserves `source_template_code`? | **NO** on operation lines today |
| Distinguishes shared vs component-specific? | **NO** — not applicable on letters rules path |
| Calculates commercial rate? | **NO** |
| Mutates state? | **NO** |

### Contract gap table

| Contract area | Current behavior | Required behavior | Gap |
|---|---|---|---|
| BOM operation consumption | Ignored | Map namespaced logo BOM ops | **YES** |
| Letters operations | `RULES_BY_TEMPLATE` | Unchanged | None |
| Logo segment identity | N/A | `component_code` = namespaced `component_ref` | **YES** |
| Logo source template | N/A | preserve `TPL-VOLUMETRIC-LOGO_v1` in provenance | **YES** |
| Internal rate | Rules catalog | Logo op code → internal unit cost (not workcenter) | **YES** |
| Quantity | Rule paths / material helper | Logo formula_id + DEC-EIC-03 boundary | **YES** |
| Shared dedupe | N/A | Trust BOM row count; no EIC dedupe | **YES** |
| Partial | Material partial wired | Operation partial/blockers | **YES** |

---

## 4. Cost BOM operation contract

| Field | Present? | Source | Stable? | Required by EIC? | Gap |
|---|---|---|---|---|---|
| `operation_code` | YES | PA / template seed | YES | YES | — |
| `label` | YES | PA | YES | YES | — |
| `component_ref` | YES | PA (namespaced) | YES | YES | — |
| `source_template_code` | YES | PA | YES | YES | — |
| segment key | Derived | `component_ref.split("::")[1]` | YES | YES | — |
| `quantity` | **NO** | — | — | YES for subtotal | **GAP** — EIC must derive |
| `minutes` / time | **NO** | seed `estimatedMinutes: 0` | NO | NO for V1 (qty-based) | Use formula basis not minutes |
| `workcenter` | YES | PA | YES | NO for EIC cost | Must not use as hourly rate |
| `formula_id` | YES | PA | YES | YES (quantity routing) | — |
| rate / tariff | **NO** on row | workcenter_rates for `pricing_availability` only | — | YES (internal catalog) | **GAP** — separate from BOM |
| `priced` flag | PA only | filtered before BOM | YES | Implicit | non-priced skipped in BOM |
| shared classification | **NO** explicit | PA dedupe | Implicit | NO | Trust row cardinality |
| `provenance` | YES | PA | YES | YES | — |
| `pricing_availability` | YES | workcenter check | YES | Diagnostic only | Not EIC rate |
| warnings | BOM-level | aggregate | YES | Propagate | — |

---

## 5. Operation ownership (logo categories)

| Operation (seed code) | PA owns identity? | BOM marks costable? | Time / qty source | Rate source (EIC) | Shared / component | Ready for EIC? |
|---|---|---|---|---|---|---|
| `logo_face_print` | YES | YES if finish confirmed | artwork finish area | internal catalog | COMPONENT_SPECIFIC | YES with rate GO |
| `logo_face_laminate` | YES | YES | artwork finish area | internal catalog | COMPONENT_SPECIFIC | YES |
| `logo_finish_application` | YES | YES | artwork finish area | internal catalog | COMPONENT_SPECIFIC | YES |
| `logo_face_cnc_cut` | YES | YES | segment area geometry | internal catalog ml/m2 | COMPONENT_SPECIFIC | PARTIAL — geometry may block |
| `logo_return_forming` | YES | YES | segment perimeter | internal catalog ml | COMPONENT_SPECIFIC | PARTIAL |
| `logo_return_bonding` | YES | YES | segment perimeter | internal catalog | COMPONENT_SPECIFIC | PARTIAL |
| `logo_back_cut` | YES | YES | segment area | internal catalog | COMPONENT_SPECIFIC | PARTIAL |
| `logo_led_install` | YES | YES | LED module count | internal catalog piece | COMPONENT_SPECIFIC | PARTIAL |
| `logo_electrical_test` | YES | YES | LED module count | internal catalog | COMPONENT_SPECIFIC | PARTIAL |
| `logo_mounting_template_cut` | YES | YES | segment area | internal catalog | COMPONENT_SPECIFIC | PARTIAL |
| `logo_mounting_install` | YES | YES | segment area / fixed | internal catalog | COMPONENT_SPECIFIC | PARTIAL |
| QC / geometry gates | YES | Skipped in BOM | N/A | N/A | INFORMATIONAL | NO |

---

## 6. Operation classification

| Operation | Classification | Notes |
|---|---|---|
| `logo_face_print`, `logo_face_laminate`, `logo_finish_application` | COMPONENT_SPECIFIC | Artwork-owned quantity |
| `logo_face_cnc_cut`, `logo_back_cut`, `logo_return_*` | COMPONENT_SPECIFIC | Segment geometry required |
| `logo_led_install`, `logo_electrical_test` | COMPONENT_SPECIFIC | Piece basis |
| `logo_mounting_*` | COMPONENT_SPECIFIC | May overlap letters sablon conceptually but **different codes** |
| Same op code on stanga + dreapta | COMPONENT_SPECIFIC ×2 | Different `component_ref` — not deduped |
| `svg_geometry_analysis` | INFORMATIONAL_ONLY | BOM skipped |
| Ops when finish partial | BLOCKED_MISSING_TIME | Omitted from PA/BOM — not invented |
| Missing internal rate | BLOCKED_MISSING_RATE | Explicit blocker |
| Missing segment geometry | BLOCKED_MISSING_TIME | `INTERNAL_GEOMETRY_MISSING` |

---

## 7. RULES_BY_TEMPLATE relation

| Operation source | Letters | Logo | Canonical now? | Duplication risk | Recommended |
|---|---|---|---|---|---|
| `internal_cost_rules_volumetric_v2` | YES | NO | Letters YES | LOW if logo filtered | Keep letters |
| `bom.costable_operations` (all) | YES rows exist | YES | BOM canonical graph | **HIGH** if EIC consumes all | **Reject for letters** |
| `bom.costable_operations` (logo only) | NO consumption | YES | **Target** | LOW | **Select** |
| `commercial_rules_volumetric_v2` | CPP only | NO | Commercial | None in EIC | Exclude |

**Later migration:** Unify all operations under BOM consumption only after letters internal rules are ported to BOM-keyed catalog (separate build; not V1).

---

## 8. Duplicate truth audit

| Concept | Source A | Source B | Canonical | Double-count risk | Plan |
|---|---|---|---|---|---|
| Letters operation cost | `RULES_BY_TEMPLATE` | BOM `costable_operations` | RULES for EIC | HIGH if both | Consume letters from RULES only |
| Logo operation cost | BOM (only) | — | BOM | None today | Add BOM → EIC mapper |
| Logo operation identity | PA composition | BOM filter | PA → BOM | LOW | No EIC expansion |
| Logo operation rate | workcenter_rates (BOM avail) | internal catalog (new) | **internal catalog for EIC** | HIGH if workcenter used | Reject workcenter for EIC |
| Print/laminate | Material EIC (done) | Operation EIC (target) | Separate line types | LOW | Op cost additive to material |
| Commercial hourly | price bridge | EIC | Excluded | HIGH | Boundary guard |

---

## 9. Central question answer

**Can EstimatedInternalCost consume workspace-linked logo `costable_operations` directly from Cost BOM while preserving component identity, shared-operation semantics, and internal-rate boundaries?**

**YES — with bounded conditions:**

1. Filter to **namespaced logo rows only** (`_is_linked_logo_bom_operation` mirror of material helper).
2. **Do not** use `workcenter_rates` / `pricing_availability` for EIC subtotals.
3. Derive quantity via `formula_id` + DEC-EIC-03 segment enrichment (no letter-area fallback).
4. Add logo **internal unit cost** catalog (owner-approved interim dev bridge).
5. Trust PA/BOM row cardinality — **no EIC dedupe**.
6. Leave letters on `RULES_BY_TEMPLATE`.

**Verdict driver:** Not blocked by contract or shared semantics; **rate numeric GO** is the only blocking owner decision for meaningful subtotals (structure can ship with blockers).

---

## 10. Architecture readback (confirmed)

```text
workspace
  → ProductDefinitionBuilderService.build_preview
  → ProductAggregateService.build_for_workspace
  → AggregateCostBomBuilderService.build_preview
  → bom.costable_operations (canonical costable filter)
  → EstimatedInternalCostService (logo op mapper + letters RULES_BY_TEMPLATE)
```

- ProductAggregate owns composed operation identity.
- Cost BOM owns costable-operation filtering.
- EstimatedInternalCost owns internal aggregation only.
- EIC must not recreate operation composition, read bindings, read recommendation, or expand linked templates.
