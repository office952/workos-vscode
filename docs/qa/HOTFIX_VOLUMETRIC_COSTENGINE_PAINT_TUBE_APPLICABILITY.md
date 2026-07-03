# HOTFIX: CostEngine paint_tube_count applicability (stock cant)

## Blocker

```
cost_invalid:NEEDS_QUOTE_INPUT@components[4].materials[0]:formula_based line requires quote_input keys ['paint_tube_count'] (formula_id='ceil_quote_input_quantity')
```

## Identified line

| Field | Value |
|-------|-------|
| Template | `TPL-VOLUMETRIC-LETTERS` |
| Component index | `4` → `comp_finisaj_litere` (Finisare — vopsire, asamblare, QC) |
| Material index | `0` → `MAT-VOPSEA-RAL` |
| Formula | `ceil_quote_input_quantity` |
| Formula params | `conditional: paint_finish`, `quote_input_key: paint_tube_count` |
| Unit | `buc` — Vopsea RAL spray tub |

## Root cause

Template seed declared `conditional: "paint_finish"` on `MAT-VOPSEA-RAL`, but `quote_input_line_gate.should_skip_quote_input_gated_line` only evaluated `formula_params.gate` dict keys (mounting, face finish, etc.). The legacy `conditional` flag was **never enforced**, so CostEngine always evaluated the paint material line and required `paint_tube_count` even for stock white/black cant (`volume_finish: "none"`).

Frontend readiness/policy already gated RAL/tubes for stock cant (commit `889d0dd`, `2935f47`) — **CostEngine path was not aligned**.

## Quote input observed (stock cant / IR-MQ47AGDG handoff)

Expected after V2 + QuoteWizard:

- `volume_finish`: `"none"`
- `return_color`: `"white"` or `"black"`
- `paint_tube_count`: absent (stripped by frontend sanitizer)
- `paint_ral_code`: absent

Stale legacy specs may still carry `paint_tube_count` in `product_spec_json`; gate must skip paint line regardless.

## Fix implemented

### A. CostEngine line gate (`quote_input_line_gate.py`)

- Honor `conditional: "paint_finish"` → skip when `is_cant_ral_paint_enabled(qi)` is false.
- Add `gate.volume_finish` / `gate.volume_finish_not` / `gate.paint_finish` support.

### B. Template seed (`seed_build4_templates.py`)

- `MAT-VOPSEA-RAL`: add `gate.volume_finish: paint_after_face_miter_bond` (keeps legacy `conditional` for DB templates already seeded).
- `painting` operation: gate to paint mode only (no RAL labor cost for stock cant).

### C. Frontend payload (`volumetricQuoteFlowState.ts`)

- Stock cant simulate payload sets `volume_finish: "none"` explicitly for CostEngine gate.

## Behavior after fix

### Stock white/black cant

- `MAT-VOPSEA-RAL` skipped (`gate:paint_finish_inactive`), quantity 0, no `NEEDS_QUOTE_INPUT`.
- `painting` operation skipped when `volume_finish !== paint_after_face_miter_bond`.
- Stale `paint_tube_count` in quote_input does not block.

### Paint / RAL mode

- `volume_finish: paint_after_face_miter_bond` → paint material line active.
- Missing `paint_tube_count` → `NEEDS_QUOTE_INPUT` (unchanged).
- With `paint_tube_count` + RAL metadata → normal costing.

## Tests

| Suite | Status |
|-------|--------|
| `test_quote_input_line_gate.py` | Added |
| `test_volumetric_paint_tube_material.py` | Updated stock/paint cases |
| `test_volumetric_quote_input_policy.py` | Existing stock cant warnings |
| Frontend volumetric unit tests | `volume_finish: none` on simulate payload |

## Remaining gaps

- DB templates seeded before this hotfix rely on `conditional` gate handler (no re-seed required).
- CostEngine multi-PSU pricing — future.
- LED strip pricing handoff — future.
- Re-seed `seed_build4_templates` in live DB if `painting` op gate must apply to persisted template JSON (gate handler fixes material line without re-seed).
