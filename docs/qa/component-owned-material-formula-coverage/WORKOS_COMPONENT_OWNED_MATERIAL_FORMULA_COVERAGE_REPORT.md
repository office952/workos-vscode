# WORKOS — Component-Owned Material Formula Coverage Report

**Date:** 2026-08-02  
**Branch:** `feat/capacity-batch-20d-scoped-b-92401`  
**Base:** `c382f061` (upstream material quantity ownership contract)  
**Stamp:** **PASS WITH WARNINGS**  
**Direction:** **99/100%**

---

## Mini decision

After Owner GO on push of `c382f061` (0/0), implement only formulas with demonstrated geometry:

| Formula | Verdict |
|---------|---------|
| `return_wrap_area` | **IMPLEMENT_MODEL_A** |
| `return_paint_consumption` | **SOURCE_MISSING** (no invent) |

Eligibility matrix written **before** formula code (`FORMULA_ELIGIBILITY_MATRIX.md`).

---

## What shipped

1. Pure helper `compute_return_wrap_area_m2` in `shared_edge_cant_rules.py` (same geometry as Oracal pricing row; no default depth for freeze callers).
2. FormulaId `RETURN_WRAP_AREA` + `_handle_return_wrap_area` + registry entry.
3. Tests for derived wrap, missing inputs, inactive finish, mutual exclusion, paint null.
4. QA pack under `docs/qa/component-owned-material-formula-coverage/`.
5. Worklog under `docs/worklog/realignment/`.

## Explicitly not shipped

- Paint yield / coats / tube conversion
- Inventory, procurement, material→op, material_inputs, readiness, materialize
- 92401 rewrite, FE changes, migrations, pricing `/price` ownership
- Product push (local commit only)

---

## Evidence

| Area | Pointer |
|------|---------|
| Eligibility | `FORMULA_ELIGIBILITY_MATRIX.md` |
| Wrap contract | `RETURN_WRAP_AREA_CONTRACT.md` |
| Paint contract | `RETURN_PAINT_CONSUMPTION_CONTRACT.md` |
| Freeze / compat | `FREEZE_AND_COMPATIBILITY.md` |
| Runtime | `RUNTIME_PROOF.md` (92401 legacy; new fixture NOT VERIFIED) |
| Dead pieces | `DEAD_PIECES_CHECK.md` |
| Tests | `test_technical_material_requirement_contract.py`, `test_shared_edge_cant_rules.py::test_compute_return_wrap_area_m2_*` |

Geometry check: `10 m × 1.20 waste × (60+10)/1000 = 0.84 m²`.

---

## Warnings

1. New live freeze fixture not created — unit-level proof only for new contract.
2. Group-level wrap perimeter subset still uses job-level perimeter when finish is globally oracal_wrapped.
3. Paint remains null until Owner authorizes yield.
4. Unrelated pre-existing `test_bond_operation_uses_owner_rate_on_total_graphic_perimeter` can fail when owner rate missing in local env — not part of this change.

---

## Suggested next Owner GO

1. **Material Planning Hints RO** — only after a new freeze shows useful `derived` + `reference_only` mix, **or**
2. Owner decision to authorize paint yield for `return_paint_consumption`.
