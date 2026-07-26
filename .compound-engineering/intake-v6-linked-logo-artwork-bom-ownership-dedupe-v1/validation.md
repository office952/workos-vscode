# INTAKE_V6_LINKED_LOGO_ARTWORK_BOM_OWNERSHIP_DEDUPE_V1 — Validation

**Phase:** VALIDATION COMPLETE  
**Accepted HEAD before:** `0df2c79`  
**Branch:** main

---

## Git boundary checks

| Check | Result |
|---|---|
| `git diff -- frontend` | **none** (unrelated dirty file exists; not staged) |
| EIC rate catalog diff | **none** |
| Numeric 35 RON/m² diff | **none** |
| CPP/pricing diff | **none** |
| Quote/Order/Execution diff | **none** |
| DB/migration diff | **none** |
| Historical data writes | **none** |
| Live reseed | **not executed** |

---

## Targeted pytest batches

| Command | Pass/Fail | Exit | Duration | Notes |
|---|---|---:|---:|---|
| `pytest tests/test_logo_artwork_bom_ownership_dedupe.py -q` | **PASS** | 0 | 1.90s | 13 tests |
| `pytest tests/test_logo_artwork_bom_ownership_dedupe.py tests/test_estimated_internal_cost_logo_operations.py tests/test_aggregate_cost_bom_workspace_linked_logo_cost_bom.py tests/test_estimated_internal_cost_workspace_linked_logo.py -q` | **PASS** | 0 | 7.06s | 62 tests |
| `pytest tests/test_product_aggregate_workspace_linked_logo_composition.py tests/test_intake_v6_layer_binding_persistence.py -q` | **PASS** | 0 | 4.03s | 27 tests |

**Total targeted:** 102 tests, 0 failures.  
**Warnings:** Starlette httpx deprecation; Pydantic ConfigDict deprecation (pre-existing).  
**Hangs:** none.

---

## Runtime probe

Fixture: `confirmed_bindings_payload()`  
Method: `test_runtime_bom_inventory_probe_report` (isolated in-memory DB)

**Expected vs actual:** 1 costable row per artwork concept per segment — **confirmed**.

Totals: 4 artwork materials + 6 artwork operations across two segments.

---

## Cardinality contract

| Concept | Before (per segment) | After (per segment) |
|---|---:|---:|
| print_media | 3 | **1** |
| laminate_media | 3 | **1** |
| logo_face_print | 2 | **1** |
| logo_face_laminate | 2 | **1** |
| logo_finish_application | 2 | **1** |

Cross-segment dedupe: **NO** (logo-stanga and logo-dreapta remain independent).

---

## Downstream

- ProductAggregate cardinality = Cost BOM cardinality for artwork rows.
- EIC material lines follow canonical materials only.
- EIC logo operation lines: 2 print ops (one per segment), all `comp_logo_finish::*`.
- `INTERNAL_OPERATION_RULE_MISSING` still present (rates not configured).
- Letters-only aggregate unchanged.

---

**VALIDATION COMPLETE**
