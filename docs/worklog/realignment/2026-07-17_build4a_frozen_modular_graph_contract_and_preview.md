# Worklog — Build 4A Frozen Modular Graph Contract and Deterministic Preview

| Field | Value |
|-------|-------|
| Task | BUILD4A_FROZEN_MODULAR_GRAPH_CONTRACT_AND_DETERMINISTIC_PREVIEW |
| Date | 2026-07-17 |
| Repo | `C:/w/psiso` |
| Branch | `feature/product-system-active-path-isolation-v1` |
| Start HEAD | `072a9cd` |
| End HEAD | see commit `feat(execution): validate frozen modular graph fingerprints` |
| Owner GO | `GO_BUILD4A_ONLY` |
| Initial verdict | `BUILD4A_IN_PROGRESS` |
| Final verdict | `BUILD4A_FROZEN_GRAPH_COMPLETE_WITH_GUARDS` |

## Objective

Strengthen the existing QuoteSnapshotV2 / OrderSnapshotV2 package with a normalized read model, layered fingerprints, scenario assertions, task-rule candidates, and zero-write proof. No new snapshot model. No persistence. No Order/ExecutionPlan/task writes.

## Architecture

```
QuoteSnapshotV2 / OrderSnapshotV2 (existing)
  → frozen_modular_graph_service.build_frozen_modular_graph_from_v2
  → FrozenModularGraphPreview (read model + hashes + assertions)
```

- ProductAggregate = hard technical SoT
- ProductDefinition = semantic intent
- CPP lines = commercial fingerprint (not totals-only)
- ActiveScope = modular selection + interface exclusions
- Task candidates ⊆ `task_contract.task_rules` only

## Files changed

| File | Role |
|------|------|
| `backend/schemas/frozen_modular_graph.py` | Read-model schema |
| `backend/services/frozen_modular_graph_service.py` | Canonicalization, fingerprints, assertions |
| `backend/routers/frozen_modular_graph.py` | Read-only preview endpoints |
| `backend/tests/test_frozen_modular_graph_build4a.py` | Unit + live no-write proofs |
| This worklog | Persistent record |

## Endpoints (no-write)

- `POST /api/v1/product-system/frozen-modular-graph/preview/{template_code}` — `build_preview` + normalize
- `POST /api/v1/product-system/frozen-modular-graph/from-snapshot` — pure normalize, no DB
- `GET /api/v1/product-system/frozen-modular-graph/from-order/{order_id}` — read `snapshot_v2_json` only
- `GET /api/v1/product-system/frozen-modular-graph/order-14-compatibility` — health-anchor classify

Never calls freeze, accept, plan from-order, materialize.

## Fingerprints

| Component | Purpose |
|-----------|---------|
| ProductDefinition | semantic truth |
| ProductAggregate | technical truth |
| CPP (line-level) | commercial truth |
| Active Scope | modular selection |
| Geometry | SVG-derived |
| Task Contract | execution candidates |
| Frozen Graph | whole package |

Volatile excluded: `frozen_at`, `converted_at`, ids, `persist_status`, `compiled_at`, etc.

## Four scenarios

| Scenario | Unit fixture | Live preview (seed WS) |
|----------|--------------|------------------------|
| Full / legacy `active=[]` | full product, not empty subset | — |
| FACE | no adhesive/bonding/LED/mount | classified + isolated |
| CANT | no FACE mats/ops/candidates, no adhesive | classified + isolated |
| FACE+CANT | adhesive×1 bonding×1 | semantic interface OK; seed Aggregate may omit technical adhesive (assertion FAILS — no greenwash) |

## Adversarial fix pass

1. Multiplicity counted on raw Aggregate rows (duplicate adhesive fails ×1)
2. face_cant missing adhesive/bonding → assertion **failed**, not auto-pass
3. cant_only asserts no FACE materials
4. Scope list fields included in sortable canonicalization
5. `from-snapshot` has no `db` dependency; AST + count guards

## Remaining guards

1. Seed Aggregate via `build_preview` may omit adhesive/bonding materials/ops for FACE+CANT even when ActiveScope interface is active — Build 4A surfaces this as failed technical assertions (does not invent materials).
2. FE Execution still wires V1 Generate Plan (WRITE_RISK) — not used.
3. Dual V1 `snapshot_line_items` path remains; Order 14 not reinterpreted.
4. Build 4B/4C/4D not started.

## Schema

`NO_SCHEMA_REQUIRED` — Pydantic read model + existing JSON only.

## Tests

```
pytest tests/test_frozen_modular_graph_build4a.py -q
→ 20 passed
```

Regression: Build 3 subset + active scope freeze — passed.

## Exclusions

No freeze persist, Order create, ExecutionPlan persist, task materialization, Intake/PD/Aggregate/CPP generation changes, schema/migration, Mobile, Pricing 7I.

## Next step

Owner review. Separate GO for Build 4B (disposable persistence) and/or 4C (Execution preview from frozen Order). Not materialization.

## Commit status

Committed: `280830c` — `feat(execution): validate frozen modular graph fingerprints`  
Exact-path staging only (5 files). Unrelated dirty tree untouched.

## STOP
