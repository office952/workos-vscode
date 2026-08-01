# Worklog — Component-Owned Material Formula Coverage

**Date:** 2026-08-02  
**Status:** PASS WITH WARNINGS  
**Branch:** `feat/capacity-batch-20d-scoped-b-92401`

## Mini-decizie

After `c382f061` at 0/0, Owner authorized formula coverage batch: implement only demonstrated Model A formulas; keep paint unresolved.

## Repo before

HEAD `c382f061` · ahead 0/0 · stash `wip-employee-unrelated` intact · authorize false.

## Eligibility first

`docs/qa/component-owned-material-formula-coverage/FORMULA_ELIGIBILITY_MATRIX.md` written before formula code.

| Formula | Verdict |
|---------|---------|
| `return_wrap_area` | IMPLEMENT_MODEL_A |
| `return_paint_consumption` | SOURCE_MISSING |

## Implementation

- `compute_return_wrap_area_m2` in `shared_edge_cant_rules.py`
- Register `return_wrap_area` in `formula_handlers.py` (no default depth 60)
- Leave `return_paint_consumption` unregistered → honest null
- Tests extended; FE untouched

## Runtime fixture

92401 unchanged (22× legacy_unspecified, null, false zero 0).  
New order fixture **NOT VERIFIED**.

## Boundaries

No inventory / materialize / material_inputs / pricing truth / 92401 rewrite / push.

## Next Owner GO

Material Planning Hints RO (if new freeze shows useful statuses) **or** paint yield authorization.

## Direction score

**99/100%**
