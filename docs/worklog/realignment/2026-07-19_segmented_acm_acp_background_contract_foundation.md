# 2026-07-19 — Segmented ACM/ACP background contract foundation

| Field | Value |
|-------|-------|
| Date | 2026-07-19 |
| Branch | `feature/product-system-active-path-isolation-v1` |
| HEAD initial | `f14570e` |
| Scope | Contract foundation: multi-panel assembly, element bindings, joint rules, PD + Aggregate projection |
| GO | PD/Aggregate/contracts/tests/docs — **no** pricing, Execution, UI, DB migration, seeds |

## Documentation correction (mandatory first)

ACM/ACP letter positioning template closed in `MIXED_ACM_ACP_TECHNICAL_TRUTH_AND_OWNERSHIP.md` §13:

- transparent self-adhesive vinyl + transfer tape;
- solid letter shapes remain under Forex 10 mm;
- linear guides / crop marks temporary;
- `paper vs Forex default` removed from open owner decisions for this mounting context.

## Research tracks

| Track | Agent | Result |
|-------|-------|--------|
| SUPPORT / SVG binding | [SUPPORT research](7b9c4e16-3d63-4c54-9b96-d3acff93f351) | Keep MAX_ONE envelope; nest panels |
| PD / Aggregate / interface | [PD Aggregate](253eaed5-4277-4958-b456-855de36ded6b) | Shell-owned config; confirmed-only projection |

## Architecture alternatives

| Option | Decision |
|--------|----------|
| A. Nested `assembly_panels` under one SUPPORT envelope | **Selected** — backwards compatible, panels ≠ products |
| B. New `PANEL_SEGMENT` MULTI geometry role | Deferred — larger SVG binding blast radius |
| C. Soften support cardinality without nested model | Rejected — breaks singular `svg_support_selection` |
| D. Global MULTI SUPPORT_CONTOUR | Rejected — treats panels as parallel shells |
| E. One product per panel | Rejected — owner forbids |

## Selected contract

- Schema: `acm_segmented_background_v1`
- Status: `SINGLE_PANEL` \| `PROPOSED` \| `CONFIRMED` \| `INACTIVE`
- PD: `canonical_values.segmented_background` only when CONFIRMED + operator_confirmed
- Aggregate: `segmented_background_aggregate_projection` guarded (no materials/tasks/execution)
- PROPOSED/INACTIVE → zero effects; optional `segmented_background_proposal` observability only
- Applied crossing → two-stage mount + primary/secondary
- Cutout / acrylic insert crossing → blocker (RO messages)
- Letters ownership not absorbed (`does_not_absorb_letter_ownership`)

## Files changed

- `backend/data/product_system/acm_segmented_background_v1.py` (new)
- `backend/services/acm_segmented_background_service.py` (new)
- `backend/services/product_definition_builder_service.py` (PD wire)
- `backend/services/acp_local_face_module_service.py` (interface panel fields)
- `backend/data/product_system/svg_component_binding_contract.py` (capability + targets; MAX_ONE kept)
- `backend/data/product_system/acp_local_face_modules_v1.py` (capability flag)
- `backend/tests/test_acm_segmented_background_v1.py` (new)
- Docs: MIXED canonical, ACP applied interface, this worklog

## Tests

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_acm_segmented_background_v1.py tests/test_svg_component_binding_contract.py tests/test_acp_local_face_modules_v1.py -q
```

Result: **28 passed**

## Runtime / service proof

Path: `_build_canonical_values([], {"finish_setup": {...}})` via ProductDefinition builder.

| Case | Expected |
|------|----------|
| Empty finish | no segmented keys |
| PROPOSED two panels | proposal marker only; no `segmented_background` |
| CONFIRMED two panels | PD + Aggregate projection; empty materials/tasks |
| Applied crossing | allowed_applied_crossings + two-stage intent |
| Cutout/insert crossing | blockers on Aggregate |

No UI. No Execution. No pricing.

## Deferred gaps

- SVG Analyzer → propose wiring (UI confirm)
- Finish Contract shell
- 220V per panel runtime
- Oracal/CNC task_rules
- Execution materialization of future_task_intent
- LIGHT-ROUTED migrate

## Next step

One coherent build: **operator confirmation path** (finish_setup write + analyzer proposal hook) for segmented background — still without pricing/Execution.
