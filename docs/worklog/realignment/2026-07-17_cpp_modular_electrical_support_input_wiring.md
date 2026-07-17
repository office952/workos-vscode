# Worklog — CPP modular electrical / support input wiring

| Field | Value |
|-------|-------|
| Task | CPP_MODULAR_ELECTRICAL_AND_SUPPORT_INPUT_WIRING |
| Owner GO | explicit |
| Date | 2026-07-17 |
| Repo | `C:/w/psiso` |
| Branch | `feature/product-system-active-path-isolation-v1` |
| Start HEAD | `39d2314` |
| Initial | `CPP_MODULAR_ELECTRICAL_SUPPORT_WIRING_IN_PROGRESS` |
| Final | `CABLE_INPUT_WIRING_COMPLETE_TEMPLATE_GUARDED` |

## Lineage

`8c98dae` → `46bfc9b`/`ea923c1` → `6fe5c50`/`baec7a9` → `96343cd`/`08fc832` → `4ccfba6`/`39d2314`

## Chosen architecture

**Option B — typed override on volumetric commercial path**

- Keep `WIRE_SUPPLY_ML_PER_JOB = 5.0` as **legacy default** when typed length absent.
- When `finish_setup.mains_cable_length_m` is valid (2.5–25 step 2.5) → quantity = selected length.
- Invalid typed → skip supply line (do not invent 5 m).
- No global constant deletion; non-volumetric products untouched (this path is volumetric-only).

Rejected: global 5 m replace; resolver-as-pricing; invented channel qty.

## 5 m audit (summary)

| Location | Decision |
|----------|----------|
| `intake_v4_consumables_adhesive_wiring_service.WIRE_SUPPLY_ML_PER_JOB` | KEEP_AS_LEGACY_DEFAULT + REPLACE_ON_MODULAR_PATH when typed present |
| FE question copy “5 m 2x1.5” | DEAD_PIECE / display copy (not qty engine) |
| IntakeDetail “5 ml” text | DEAD_PIECE display |
| Process allow-list includes 5.0 | TEST / valid option, not invent |

## Material / pricing authority

| Concern | Authority |
|---------|-----------|
| Selected length | ProductDefinition / finish_setup typed |
| Quantity | Live materials consumables (`quantity = length`) |
| Material code | `MAT-CABLU-MYYUP-2X15` |
| Unit price seed | owner RON→EUR fallback; registry may override via `_apply_registry_prices` |
| Cable channel | Process role only — **no MAT / no formula** → GUARDED |
| Template | Existing CPP/EIC via `mounting_template_area_m2` — not reinvented |

## Channel / template status

- **Channel:** `CABLE_CHANNEL_COMMERCIAL_FORMULA_GUARDED` warning on metal_bars; zero channel material line.
- **Template:** already priced when enabled + area present; this build does not invent segmentation formulas.

## Files

- `backend/services/intake_v4_consumables_adhesive_wiring_service.py`
- `backend/services/intake_v4_material_breakdown_service.py`
- `backend/tests/test_cpp_modular_electrical_support_input_wiring.py`
- `backend/tests/test_intake_v4_consumables_adhesive_and_wiring.py` (pilot template + float asserts)
- `frontend/.../IntakeV6ReviewStep.tsx` (hint copy)
- `frontend/.../intakeV4QuantityBasisLabels.ts`

## Tests

```text
pytest tests/test_cpp_modular_electrical_support_input_wiring.py
     tests/test_intake_v4_consumables_adhesive_and_wiring.py
     tests/test_intake_v6_modular_process_field_wiring.py
     tests/test_product_process_live_aggregate_bridge.py
     tests/test_product_process_contract_resolver.py
     tests/test_frozen_modular_graph_build4a.py
     tests/test_execution_preview_from_frozen_build4c.py
→ 186 passed
```

## Runtime / UI verification path

| Item | Value |
|------|-------|
| Live path | Review → materials breakdown / logical-list `material.wire_supply` |
| API | `GET /intake-v6/workspaces/{id}/logical-list-read-model` |
| UI | `http://127.0.0.1:3000/intake-v6/<id>` → Review → Montaj → cable length → live calc materials |
| Expect | 2.5 vs 25 changes quantity & subtotal; Alucobond/no-support: no channel line |

## Guards

- Cable channel commercial formula missing (owner GO for qty/SKU).
- Template already separate; no new invent.
- Legacy 5 ml still used when typed absent (observable warning).
- Official commercial_rules CPP catalog still has no dedicated mains-cable rule — money appears on live materials / logical list (existing authority for this consumable).

## Next safe step

**Option 1 — OWNER REVIEW OF CPP ELECTRICAL INPUT WIRING**
