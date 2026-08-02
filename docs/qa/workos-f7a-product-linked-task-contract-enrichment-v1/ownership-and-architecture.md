# F7A — Ownership and architecture readback

## Architecture docs read (kickoff)

- `AGENTS.md`
- Product Definition / Aggregate / ExecutionPlan contracts under `docs/architecture/` (03, 05, 08 EP, 10 task graph, 12 HR boundary, 14 machines, 18 governance, 21 route, pricing separation)
- U7 / Step 8–9 worklogs for Snapshot V2 freeze/accept/convert, EP preview/persist, materialization audit GET

## Sources of task truth found

| Source | Role | Canonical? |
|--------|------|------------|
| `product_blueprint_dossier.task_rules_json` → `_build_task_contract` | Dossier legacy path | Driver when modular absent |
| Modular `ResolvedProductProcessGraph` → aggregate bridge | Live modular overlay | Driver when modular present |
| Composition-graph synthetic ops | Fill gaps for uncovered ops | Secondary; must not re-introduce aliases |
| Catalog `PROCESS_DEPENDENCY_RULES` | Dep fallback when rule lacks edges | Allowed; not linear invent |
| Commercial / Pricing snapshots | Forbidden as task truth | Ignored by EP preview |

## Canonical task driver

```text
task_contract.task_rules  (after alias collapse)
  → frozen in OrderSnapshotV2.product_aggregate_snapshot
  → collect_effective_task_rules
  → ExecutionPlan V2 planned_tasks
```

No second compiler introduced.

## Alias / provenance behavior

- Module aliases remain on Aggregate `operations[]` for structure/BOM/provenance.
- They are removed from operational `task_rules` when parent priced op exists.
- If only alias exists, it is promoted to parent identity (`alias_promoted_from=…`).
- EP synthetic ops skip alias codes when parent already covered.

## Workcenter ownership

```text
Aggregate operations[].workcenter (+ resolution status/source)
  → frozen Snapshot V2
  → PlannedTaskPreview.machine_requirement.workcenter
```

Forbidden: invent WC after materialize; guess by label; machine hourly pricing; live Intake after freeze.

## DAG strategy

1. Prefer `depends_on_process_ids` on task rules.
2. Else catalog process/preparation dependency rules for priced op.
3. Resolve to present planned task keys only.
4. Cycle → clear edges (fail closed).
5. If zero real edges → **empty deps** + `DAG_PROCESS_DEPENDENCIES_UNRESOLVED` (no linear invent).

Finish filtering remains `_finish_allows_priced_op` (paint vs vinyl etc.).

## Premount / SVG

- Premount: BOM-only default; no invented activation boolean.
- SVG geometry codes: non-operational catalog; WorkOS does not parse SVG/DWG.
