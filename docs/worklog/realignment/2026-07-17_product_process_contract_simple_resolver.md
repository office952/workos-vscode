# Worklog — Product Process Contract + Simple Resolver

| Field | Value |
|-------|-------|
| Task | `PRODUCT_PROCESS_CONTRACT_AND_SIMPLE_RESOLVER` |
| Date | 2026-07-17 |
| Branch | `feature/product-system-active-path-isolation-v1` |
| Start HEAD | `ea923c1` |
| End HEAD | (see commit) |
| Initial | `PRODUCT_PROCESS_CONTRACT_BUILD_IN_PROGRESS` |
| Final | `PRODUCT_PROCESS_CONTRACT_AND_RESOLVER_COMPLETE_WITH_GUARDS` |

## Authority map (chosen)

| Concern | Authority |
|---------|-----------|
| component-local truth | `backend/data/product_process/volumetric_letters_v1.py` COMPONENT_CONTRACTS |
| interface truth | INTERFACE_CONTRACTS (same module) |
| process / state / capability / material-role vocabulary | `backend/data/product_process/catalogs.py` |
| machine equipment | existing Utilaje / OperationResourceRequirement (unchanged; capabilities only in contracts) |
| concrete configuration | `ProductProcessResolveInput` (fixture / future ProductDefinition mapping — Intake untouched) |
| compiled technical output | resolver → Aggregate-compatible `task_rules` (+ optional `depends_on_process_ids`) |
| frozen accepted graph | Snapshot V2 in-memory fixture → Build 4A |
| execution preview | Build 4C (prefers `process_depends_on`; sequence fallback only if edges absent) |

## Alternatives evaluated

1. New Process Template entity / BPM — rejected (forbidden, overkill)
2. Only enrich dossier `task_rules_json` — rejected (keeps dual SoT; thin model)
3. Hardcode in ProductAggregateService — rejected (Aggregate must not reinvent)
4. **Chosen:** declarative Python contracts + pure resolver + minimal Aggregate/4A/4C field pass-through

## Files

Created:
- `backend/data/product_process/*`
- `backend/schemas/product_process_contract.py`
- `backend/services/product_process_resolver_service.py`
- `backend/services/product_process_aggregate_bridge.py`
- `backend/tests/test_product_process_contract_resolver.py`
- this worklog

Modified (minimal):
- `backend/schemas/product_aggregate.py` — optional `depends_on_process_ids`, `process_code`
- `backend/schemas/frozen_modular_graph.py` — `depends_on_process_ids` on candidates
- `backend/services/frozen_modular_graph_service.py` — pass-through
- `backend/services/execution_preview_from_frozen_graph_service.py` — real DAG when present

## Tests

```
pytest tests/test_product_process_contract_resolver.py
     tests/test_frozen_modular_graph_build4a.py
     tests/test_execution_preview_from_frozen_build4c.py
→ 70 passed
```

## Runtime proof (service-level)

Three configs (metal / alucobond / no-support): resolve → in-memory Snapshot V2 → frozen graph → Build 4C preview; `process_depends_on` edges; `no_write=true`.

## Not done (guards / out of scope)

- Intake V6 field wiring (cable, service corner, screw finish UI)
- CPP lines for cable/channel/template
- Persist resolver into live Aggregate compile path (bridge helper ready; not hooked into AggregateService)
- Build 4C.1 UI
- Seed / migration / schema
- Rollout other products

## Next safe step

**Option 1 — OWNER REVIEW OF CONTRACT + RESOLVER**

## STOP
