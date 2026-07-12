# INTAKE_V6_ESTIMATED_INTERNAL_COST_WORKSPACE_LINKED_LOGO_WIRING_V1 — Validation

**Phase:** VALIDATION COMPLETE  
**Accepted HEAD before:** bcdd14d  
**Branch:** main

---

## Git checks

| Command | Result |
|---|---|
| `git status --short` | Task files dirty; unrelated dirty files present (frontend, screenshots, worklogs) — not staged |
| `git diff --stat` (unstaged) | 9 files including unrelated; task backend files + compound folder |
| `git diff --check` | Trailing whitespace in unrelated worklog only |

## Forbidden-scope diff confirmation

| Scope | Diff |
|---|---|
| frontend | NO (unrelated `IntakeV6LayersOperatorPanel.tsx` dirty but not staged) |
| ProductDefinition | NO |
| ProductAggregate | NO |
| Cost BOM adapter | NO |
| pricing / CPP | NO |
| Quote/Order/Execution | NO |
| DB/migration/seed | NO |

## Test commands

| Command | Exit | Pass | Duration |
|---|---|---:|---|
| `pytest tests/test_estimated_internal_cost_workspace_linked_logo.py tests/test_estimated_internal_cost_preview.py -q` | 0 | 32 | ~6s |
| `pytest ... tests/test_aggregate_cost_bom_workspace_linked_logo_cost_bom.py tests/test_product_aggregate_workspace_linked_logo_composition.py -q` | 0 | 59 | ~6s |
| `pytest tests/test_product_definition_gradi_composition.py tests/test_intake_v6_layer_binding_persistence.py tests/test_selected_layer_refs_runtime_capture.py tests/test_return_cant_product_truth_bridge.py -q` | 0 | 34 | ~4s |
| `pytest tests/test_estimated_internal_cost_preview.py tests/test_return_cant_pricing_registry_keys.py -q` | 0 | (see run) | — |

**Warnings:** Pydantic ConfigDict deprecation, Starlette httpx deprecation — pre-existing.

**Hangs:** none.

## Runtime / API verification (via TestClient + seeded DB)

Route: `POST /api/v1/product-system/estimated-internal-cost-preview/TPL-VOLUMETRIC-LETTERS_v2`

| Scenario | Method | URL | Request | HTTP | Workspace | Writes | EIC status | Letter mat. | Logo mat. | Logo ops | Commercial |
|---|---|---|---|---:|---|---|---|---|---|---|
| No workspace_id | POST | `.../TPL-VOLUMETRIC-LETTERS_v2` | `{}` or quote_input | 200 | absent | NONE | template contract | yes | none | letters only | NO |
| Letters-only workspace | POST | same | `{workspace_id}` | 200 | letters binding | NONE | ready/partial | yes | none | letters only | NO |
| Two logo complete | POST | same | `{workspace_id, quote_input}` | 200 | confirmed bindings | NONE | ready/partial | yes | print/lam per segment | none | NO |
| Partial finish | POST | same | `{workspace_id}` unconfirmed finish | 200 | partial finish | NONE | **partial** | yes | **none fabricated** | none | NO |
| Missing rates | POST | same | patched empty rates | 200 | workspace | NONE | blockers | varies | blockers | none | NO |

Logo operation lines: **0** in all scenarios (documented debt).

Missing rates: `INTERNAL_MATERIAL_COST_MISSING` / `INTERNAL_GEOMETRY_MISSING` — never zero-cost fallback.

Commercial fields present: **NO** (`commercial_price`, `markup`, `margin`, `vat` absent).

## Assertions not weakened

Existing EIC preview tests remain green with PatchedAggregateCostBomBuilder injection. No snapshot changes.

---

## VALIDATION COMPLETE

Ready for compound review and commit (task files only).
