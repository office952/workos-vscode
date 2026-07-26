# INTAKE_V6_ESTIMATED_INTERNAL_COST_WORKSPACE_LINKED_LOGO_WIRING_V1 — Plan

**Phase:** PLAN COMPLETE  
**Plan verdict:** READY_FOR_BOUNDED_IMPLEMENTATION  
**Scope verified:** YES  
**Forbidden scope touched:** NO  
**Accepted HEAD:** bcdd14d

---

## 1. Objective

Wire **EstimatedInternalCost** to consume the **workspace-aware Cost BOM** produced by bcdd14d:

```text
workspace_id
  → ProductDefinition (workspace-aware)
  → workspace ProductAggregate
  → AggregateCostBomBuilderService.build_preview
  → EstimatedInternalCostService.build_preview
  → read-only internal cost preview
```

No commercial pricing, no Quote/Order, no DB writes, no binding/recommendation reads.

---

## 2. Accepted truth

| Rule | Status |
|---|---|
| PD compiles technical truth | YES — unchanged |
| PA canonical technical graph | YES — unchanged |
| Cost BOM consumes PA (bcdd14d) | YES — unchanged in this task |
| EIC consumes Cost BOM | **TARGET** |
| Partial logo → partial BOM, no fabricated rows | YES — propagate |
| CPP / commercial pricing outside | YES |

---

## 3. Selected architecture

**Option A/C hybrid — EIC consumes workspace-aware Cost BOM via builder**

```python
# Replace local aggregate + adapter.build with:
bom = await AggregateCostBomBuilderService(self._db).build_preview(
    template_code,
    workspace_id=workspace_id,
    quote_input=quote_input or payload or None,
)
```

Remove from EIC `build_preview`:

- `aggregate = await self._aggregate_svc.build(template_code)`
- Direct `self._bom_adapter.build(...)` (unless builder injection needed for tests)

**Why:** Single canonical BOM graph; reuses bcdd14d orchestration; no parallel PA/BOM truth.

### Architecture comparison

| Option | Truth duplication | Code size | Contract impact | Commercial risk | Recommendation |
|---|---:|---:|---:|---:|---|
| A — Cost BOM builder input | 0 | S | 0 | LOW | **SELECT** |
| B — EIC consumes PA directly | HIGH | M | MED | MED | Reject |
| C — Thin orchestration wrapper | 0 | S | 0 | LOW | Same as A |
| Reject: binding read | HIGH | — | — | MED | **REJECT** |
| Reject: parallel BOM | HIGH | — | — | MED | **REJECT** |

### Rejected options

- EIC reads `layer_bindings` or recommendation
- EIC calls `build_for_workspace` independently without Cost BOM builder (parallel graph)
- EIC rebuilds ProductDefinition
- EIC activates CommercialPriceProposal or price bridge
- New public route (existing POST sufficient)

---

## 4. Exact files / functions (implementation boundary)

### Allowed to modify (later `/ce-work`)

| File | Change |
|---|---|
| `backend/services/estimated_internal_cost_service.py` | `build_preview`; `_estimate_material_quantity`; optional `_is_linked_logo_bom_material`; `_compute_status` or post-status partial hook |
| `backend/tests/test_estimated_internal_cost_preview.py` | Fixture alignment if needed |
| `backend/tests/test_estimated_internal_cost_workspace_linked_logo.py` | **NEW** — workspace logo EIC tests |
| `docs/worklog/realignment/2026-07-12_intake_v6_estimated_internal_cost_workspace_linked_logo_wiring_v1.md` | Worklog |

### Must NOT modify

Frontend, ProductDefinition, ProductAggregate composition, Cost BOM adapter architecture (bcdd14d), binding persistence, ProductSystem templates, pricing registry, CPP, Quote, Order, Execution, DB schema/migrations/seeds.

### Reference-only

- `backend/services/aggregate_cost_bom_adapter.py` — `AggregateCostBomBuilderService`
- `backend/tests/test_aggregate_cost_bom_workspace_linked_logo_cost_bom.py` — fixtures
- `backend/routers/estimated_internal_cost.py` — endpoint unchanged

---

## 5. Input / output contract

### Public API (unchanged)

```
POST /api/v1/product-system/estimated-internal-cost-preview/TPL-VOLUMETRIC-LETTERS_v2
Body: { "workspace_id": "<uuid>", "quote_input": { ... }, "currency": "RON" }
```

### Internal orchestration

| workspace_id | BOM source |
|---|---|
| present | `AggregateCostBomBuilderService.build_preview(..., workspace_id=…)` |
| absent | `AggregateCostBomBuilderService.build_preview(...)` template-only |

### Output guarantees

| Field | Behavior |
|---|---|
| `input_summary.workspace_id` | Set when provided |
| `estimated_material_lines` | Letters + per-segment logo when BOM has rows + rates |
| `estimated_operation_lines` | Letters rules unchanged; logo ops **v1 debt** |
| `status` | `partial` when BOM partial / logo finish partial; `blocked` on critical missing rates/geometry |
| `internal_blockers` | Explicit missing rates — never silent zero |
| Commercial totals | **None** — internal only |

---

## 6. Material cost semantics

| Material row | Cost source | Quantity source | Missing rate | Partial finish | Dedupe |
|---|---|---|---|---|---|
| Letters (oracal, profile, etc.) | BOM `unit_cost` | existing `_estimate_material_quantity` | blocker | unchanged | by resolved code + component_ref |
| Logo print_media | BOM row | segment area from payload (DEC-EIC-03) | blocker | **omit** (no BOM row) | per `component_ref::segment` |
| Logo laminate_media | BOM row | segment area | blocker | omit | per segment |
| Logo face/return/back | BOM row | segment area or rule path | blocker | omit | per segment |
| Same material code twice | two BOM rows | separate qty | independent | independent | **do not merge** segments |

Rules:

- One BOM costable material → at most one EIC material line.
- Missing finish → no logo BOM rows → no fabricated logo cost.
- `pricing_availability != available` → blocker, not zero.

### EIC material eligibility fix (GAP-3)

Replace:

```python
if mat.mini_module_code and mat.mini_module_code not in active_modules:
    continue
```

With:

```python
if not _is_linked_logo_bom_material(mat):
    if mat.mini_module_code and mat.mini_module_code not in active_modules:
        continue
```

Where `_is_linked_logo_bom_material` mirrors bcdd14d: `source_template_code == TPL-VOLUMETRIC-LOGO_v1` and `::` in `component_ref`.

---

## 7. Operation cost semantics

| Operation | EIC v1 behavior | Notes |
|---|---|---|
| Letters CNC/print/laminate (rules) | unchanged | `RULES_BY_TEMPLATE` + active_modules |
| Logo CNC/print/laminate (BOM ops) | **not in v1 totals** | DEC-EIC-04 debt |
| QC / informational | excluded | existing |
| Missing tariff | blocker/warning via rules | no invented minutes |
| Shared ops | letters rules only | no second dedupe |

**v1 scope:** Logo internal cost contribution primarily via **material lines** (print/laminate media from BOM). Operation rule extension deferred.

---

## 8. Partial cost semantics

| Condition | Cost BOM | EIC rows | EIC status | Warning |
|---|---|---|---|---|
| Letters only | letters BOM | letters materials | unchanged | — |
| Letters + complete logo | full logo mat rows | letters + logo materials | partial/ready per completeness | composition applied |
| Letters + partial logo | partial BOM, no logo mats | letters only | **partial** | finish partial propagated |
| Missing binding | letters-only | letters only | unchanged | — |
| Missing logo rate (complete finish) | row present | blocker for that mat | blocked/partial | explicit blocker |
| Missing geometry (letters) | — | blocker | blocked | existing |

Critical: missing logo rows ≠ zero-cost complete logo.

Implementation:

- Merge `bom.warnings` (already done).
- If `bom.bom_status == "partial"` or `LINKED_SEGMENT_FINISH_PARTIAL` in warnings → cap EIC status at `partial` (do not upgrade to `ready`).

---

## 9. Missing rate behavior

| Case | Behavior |
|---|---|
| Missing inventory unit_cost | `INTERNAL_MATERIAL_COST_MISSING` blocker |
| Missing quantity geometry | `INTERNAL_GEOMETRY_MISSING` blocker |
| Zero rate | treated as missing (existing BOM check) |
| Partial logo | no row → no blocker for absent logo |

Never interpret absent logo material as zero subtotal complete.

---

## 10. Status / readiness

Existing vocabulary: `ready | partial | blocked`.

| Condition | Existing | Required |
|---|---|---|
| BOM partial (logo finish) | may compute blocked | **partial** (DEC-EIC-05) |
| Critical blockers | blocked | unchanged |
| Optional owner decisions | partial | unchanged |
| High completeness | ready | unchanged |

---

## 11. Provenance

| EIC row type | Required | Existing | Plan |
|---|---|---:|---|
| Material line | `component_code`, module, rule source | YES | keep `component_code=mat.component_ref` |
| Logo segment | segment in component_code | partial | namespaced ref preserved |
| Workspace | workspace_id | YES | `input_summary.workspace_id` |
| BOM upstream | aggregate_cost_bom | YES | update provenance detail with workspace flag |

No new public schema fields.

---

## 12. Duplicate prevention

| Layer | Owns |
|---|---|
| ProductAggregate | technical row identity |
| Cost BOM builder | workspace PA + BOM mapping |
| EIC | aggregation from BOM + internal rules |
| CPP | commercial markup (forbidden) |

EIC must not call `aggregate_svc.build` when builder is used.

---

## 13. Endpoint / service plan

| Option | API change | Compatibility | Reuse | Mutation | Recommendation |
|---|---:|---:|---:|---:|---|
| A — existing POST + workspace_id | 0 | HIGH | HIGH | NONE | **SELECT** |
| B — service-only | 0 | LOW for operators | HIGH | NONE | Reject |
| C — new GET route | +1 | MED | MED | NONE | Reject |

No POST write semantics change. No persistence.

---

## 14. Commercial pricing boundary

| Layer | Included? |
|---|---:|
| Cost BOM (upstream) | YES — read-only |
| EstimatedInternalCost | YES — target |
| CommercialPriceProposal | NO |
| Quote/Order | NO |

Forbidden: markup, margin, VAT, discount, commercial hourly price, client price, quote creation.

---

## 15. Test plan

New file: `backend/tests/test_estimated_internal_cost_workspace_linked_logo.py`  
Reuse gradi fixtures from Cost BOM / PA tests.

### Orchestration (1–6)

1. `workspace_id` → builder `build_preview` invoked (mock/spy).
2. No `workspace_id` → template-only builder path.
3. No local `aggregate_svc.build(template)` when workspace_id set.
4. No binding service import in EIC module.
5. No recommendation import in EIC module.
6. No PD rebuild inside material quantity helpers.

### Letters-only (7–8)

7. Letters-only workspace EIC ≡ template-only EIC (material line keys).
8. Existing `test_estimated_internal_cost_preview.py` green.

### Logo (9–13)

9. One logo segment → logo material line(s) when rates seeded.
10. Two segments → distinct `component_code` values.
11. Same LOGO template twice → two lines, not merged.
12. Namespaced ids survive eligibility filter.
13. `source`/provenance includes workspace_id.

### Partial (14–20)

14. Missing binding → no logo cost lines.
15. Missing finish → EIC `status=partial`.
16. No print cost fabricated.
17. No laminate cost fabricated.
18. Letters internal cost lines present.
19. No zero subtotal interpreted as complete logo.
20. Finish-partial warning in EIC warnings.

### Missing rates (21–24)

21. Missing logo material rate → blocker explicit.
22. Missing operation rule unchanged (letters).
23. No silent zero unit cost.
24. Status blocked or partial per existing semantics.

### Boundaries (25–35)

25–30. No markup/margin/VAT/hourly/client price/CPP.
31. No Quote/Order side effects.
32. No DB writes.
33. No frontend changes.
34. Cost BOM workspace tests pass (regression).
35. Pricing tests unchanged.

### Regression bundle (36–43)

36. Cost BOM workspace tests  
37. PA workspace tests  
38. PD gradi tests  
39. Binding persistence  
40. selected_layer_refs  
41. return/cant  
42. Existing EIC tests  
43. Existing Cost BOM adapter tests  

### Commands

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_estimated_internal_cost_workspace_linked_logo.py -q
.\.venv\Scripts\python.exe -m pytest tests/test_estimated_internal_cost_preview.py tests/test_aggregate_cost_bom_workspace_linked_logo_cost_bom.py -q
```

---

## 16. Runtime verification

1. Dev stack :8000 / :3000.
2. Gradi workspace with confirmed bindings + finish.
3. `POST /api/v1/product-system/estimated-internal-cost-preview/TPL-VOLUMETRIC-LETTERS_v2` with `workspace_id`.
4. Compare: no workspace_id vs letters-only vs two logos vs partial finish.
5. Report: status, letter lines, logo lines, blockers, warnings, commercial price absent.

---

## 17. Rollback

Revert EIC to direct `aggregate_svc.build` + `_bom_adapter.build`. No migration.

---

## 18. Implementation sequence

1. Import `AggregateCostBomBuilderService`.
2. Replace aggregate + adapter.build block with builder `build_preview`.
3. Add `_is_linked_logo_bom_material(mat)` helper.
4. Fix material loop eligibility (GAP-3).
5. Extend `_estimate_material_quantity` for segment suffix → artwork finish area (DEC-EIC-03).
6. After `_compute_status`, apply partial override from BOM (DEC-EIC-05).
7. Update provenance detail string.
8. Add test module + run targeted pytest.
9. Worklog.

Estimated diff: ~60–120 LOC production + ~250–400 LOC tests.

---

## 19. Review checklist

- [ ] One architecture (Cost BOM builder input)
- [ ] Workspace-aware upstream graph
- [ ] No binding/recommendation read
- [ ] No PD rebuild in EIC
- [ ] No parallel Cost BOM
- [ ] Partial semantics explicit
- [ ] Missing rates explicit
- [ ] No zero-cost false completion
- [ ] Segment identity preserved
- [ ] Provenance preserved
- [ ] Commercial pricing excluded
- [ ] No DB writes / UI
- [ ] Tests specific
- [ ] Rollback documented
- [ ] Owner decisions in decision-log

---

## 20. Forbidden scope check

No implementation in this phase. No changes to Cost BOM architecture, PA, PD, CPP, Quote, Order, Execution, DB, frontend.

---

## Plan review gate

**Verdict: READY_FOR_BOUNDED_IMPLEMENTATION**

Soft owner confirm: DEC-EIC-03 (segment quantity), DEC-EIC-04 (logo operations v1 debt).

**Next command:**

```
/ce-work mode:return-to-caller .compound-engineering/intake-v6-estimated-internal-cost-workspace-linked-logo-wiring-v1/plan.md
```
