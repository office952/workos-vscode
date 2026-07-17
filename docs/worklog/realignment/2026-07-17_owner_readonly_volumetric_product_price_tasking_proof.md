# Worklog — Owner read-only Product / Price / Tasking proof

| Field | Value |
|-------|-------|
| Task | OWNER_READ_ONLY_VOLUMETRIC_LETTERS_PRODUCT_PRICE_TASKING_PROOF |
| Owner GO | explicit |
| Date | 2026-07-17 |
| Repo | `C:/w/psiso` |
| Branch | `feature/product-system-active-path-isolation-v1` |
| Start HEAD | `1177db8` |
| Feature commit | `258eaa3` |
| Worklog commit | `995dc73` |
| End HEAD | `995dc73` |
| Initial | `OWNER_READ_ONLY_PRODUCT_PRICE_TASKING_PROOF_IN_PROGRESS` |
| Final | `OWNER_READ_ONLY_PRODUCT_PRICE_TASKING_PROOF_COMPLETE_WITH_GUARDS` |

## Decision

Thin **composer** over existing authorities — not a new tasking system.

```text
Intake V6 workspace
→ ProductDefinition preview
→ ProductAggregate.task_contract (modular_resolver → existing task_rules)
→ live materials wire_supply
→ in-memory Snapshot V2
→ Build 4C execution preview
```

Resolver remains process compiler only. Tasking authority remains existing `task_rules` / Build 4C consumers.

## Deliverables

| Piece | Path |
|-------|------|
| Schema | `backend/schemas/owner_readonly_volumetric_proof.py` |
| Service | `backend/services/owner_readonly_volumetric_proof_service.py` |
| API | `GET /api/v1/product-system/owner-readonly-proof/{template}?workspace_id=` |
| Router | `backend/routers/owner_readonly_volumetric_proof.py` |
| Tests | `backend/tests/test_owner_readonly_volumetric_proof.py` |
| FE API | `frontend/src/api/ownerReadonlyVolumetricProof.ts` |
| FE panel | `frontend/src/features/product-system/OwnerReadonlyVolumetricProofPanel.tsx` |
| Mount | Product System product detail when `?owner_proof=1&workspace_id=` |

## Owner verification

1. Confirm Intake V6 workspace for `TPL-VOLUMETRIC-LETTERS_v2` (Montaj: metal bars + cable length).
2. Open:
   `http://127.0.0.1:3000/product-system/products/TPL-VOLUMETRIC-LETTERS_v2?owner_proof=1&workspace_id=<WS>`
3. Or API:
   `GET http://127.0.0.1:8001/api/v1/product-system/owner-readonly-proof/TPL-VOLUMETRIC-LETTERS_v2?workspace_id=<WS>`
4. Expect:
   - `process_graph_source=modular_resolver`
   - task names from Aggregate `task_rules` (vinyl before CNC, channel on metal bars)
   - `wire_supply.quantity` = selected `mains_cable_length_m`
   - `execution_preview_4c.no_write=true`
   - `cable_channel_commercial_guarded` when metal bars

## Tests

```text
pytest tests/test_owner_readonly_volumetric_proof.py
     + process/bridge/4A/4C regressions
→ 107 passed (subset including proof)
```

## Guards

- Cable channel commercial formula still guarded (no invent).
- Panel mounts only when query flags present (no Intake redesign).
- FE Aggregate type still omits full `task_contract` display elsewhere — proof API is the owner surface.

## Next safe step

**Option 1 — OWNER REVIEW OF READ-ONLY PROOF** (then optional read-only price+process walkthrough on a real workspace).
