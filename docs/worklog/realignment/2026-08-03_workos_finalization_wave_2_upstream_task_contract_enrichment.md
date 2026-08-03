# WorkOS Finalization Wave 2 — Upstream task contract enrichment

| Field | Value |
| ----- | ----- |
| Date | 2026-08-03 |
| Mini decision | Owner GO `FINALIZATION_WAVE_2` with binding DEC-001…007 and DEC-009=A |
| Branch | `feat/f7i-owner-rate-activation` |
| Starting HEAD | `134eef7e` |
| Final HEAD | see `git rev-parse HEAD` after Wave 2 commit |
| Verdict | `FINALIZATION_WAVE_2 = COMPLETE` |

## Owner GO (binding)

```text
DEC-001 = A  svg_geometry_analysis non-operational
DEC-002 = A  premount BOM-only
DEC-003 = A  parent RETURN canonical
DEC-004 = A  parent painting canonical
DEC-005 = E  ORR registry → compile/aggregate → freeze → EP reads frozen
DEC-006 = A  estimated_minutes null + warning
DEC-007 = B  finish-aware DAG (foil after bonding + assembly)
DEC-009 = A  POST materialize blocked
MATERIALIZATION = CLOSED
SCHEDULING = HOLD
```

## Preflight

```text
PREFLIGHT = PASS
HEAD = 134eef7e
tracked clean; untracked QA leftovers untouched
MULTI_AGENT_AVAILABLE = YES (A–D explore)
```

## Capability inventory

| System | Class |
| ------ | ----- |
| Subagents explore | AVAILABLE_AND_RELEVANT |
| pytest / vitest / eslint / browser | AVAILABLE_AND_RELEVANT |
| Figma / Sentry / Linear / PostHog | AVAILABLE_NOT_NEEDED |

## Current-truth map (audit)

| Question | Answer |
| -------- | ------ |
| Who builds task_rules? | `ProductAggregateService._build_task_contract` + modular bridge |
| Driver | `product_aggregate_snapshot.task_contract.task_rules[]` |
| Alias collapse | `collapse_operational_alias_rules` (ALREADY_PRESENT F7A) |
| WC registry | `operation_resource_requirements` (ORR) — no DB migration |
| WC freeze | Snapshot freeze path + **Wave 2 compile-time stamp on Aggregate.build** |
| EP deps | `_build_dependencies` process/catalog DAG; no linear invent |
| Minutes | null + `PLANNING_MINUTES_SOURCE_REQUIRED` |

## Contradictions / stale

- Docs claiming PD `processes[]` drives EP → stale; task_rules drives V2.
- Catalog `vinyl_application → side_forming` contradicted Owner foil rule → **corrected**.
- DEC-005 historically labeled A; Owner Wave 2 sets **E** (A+D).

## Implementation

### Canonical ownership / aliases
No new collapse engine — F7A policy confirmed by Wave 2 tests.

### Workcenter (DEC-005=E)
`ProductAggregateService.build` now loads ORR and stamps ops at compile. Freeze still re-applies. EP continues to read frozen only (no live re-resolve). Proven: registry remap creates a **new** stamped aggregate without mutating the prior instance.

### Finish-aware DAG (DEC-007=B)
`PROCESS_DEPENDENCY_RULES`:
- `vinyl_application` → `return_face_bonding` + `assembly_letters`
- `assembly_letters` no longer waits on vinyl (avoids cycle)
- `qc_letters` soft-deps vinyl when present
- `face_vinyl_cut` prep may run after `vector_prep` (early parallel)

### Snapshot / EP
Controlled fixture via F7A 8807xx pattern: preview → persist idempotent → audit GET; `operational_tasks=0`; DEC-009 gate enforced; no RETURN/PAINTING module codes in candidates.

### UI (local Step 9B)
TruthPanel shows WC `mapping_source` / `resolution_status` and dependency edge list (backend-owned).

## Tests

- `tests/test_finalization_wave2_upstream_task_contract.py` — green
- F7A + golden DAG + F7I.1 — green
- EP preview/persist/audit/DEC-009/ORR — 109 passed; 1 failure `test_no_migration_needed_for_step_9_3_3` classified **PRE_EXISTING** (Alembic s5* window drift; not introduced by Wave 2)
- FE Step 9B Vitest + lint — green

## Runtime / baselines

| Check | Result |
| ----- | ------ |
| GET pricing/registry | 200 |
| 880811 | total 1847.5 · plan 22 · sha `a59b6c44` |
| 973019 | total 847.5 · plan 21 · sha `2d412e6e` |
| Materialize POST | not called |
| F7I rates | unchanged (regression green) |

## Security

No new mutation surface. IDOR on order-scoped GETs remains pre-existing roadmap item. DEC-009 gate still closed.

## DB

```text
STOP_DB_EXPANSION avoided — ORR + JSON aggregate sufficient
migration = zero
```

## Dead Pieces Check

```text
Dead pieces discovered: none new
Dead pieces touched: none removed
Dead pieces removed: NONE
Why: Step 12 separate GO
Step 12 impact: none
```

## Files changed

- `backend/services/task_dependency_rules_service.py`
- `backend/services/product_aggregate_service.py`
- `backend/tests/test_finalization_wave2_upstream_task_contract.py`
- `frontend/src/api/execution.ts`
- `frontend/src/components/execution/ExecutionPlanV2TruthPanel.tsx`
- `docs/architecture/realignment/21_WORKOS_IMPLEMENTATION_ROUTE.md`
- this worklog

## Exact next step

```text
Do not start Wave 3 automatically.
Wave 3 Readiness Pack is evidence-backed by Wave 2 tests + protected baseline RO.
Keep DEC-009=A until separate Owner GO sets B.
Wave 3 = controlled materialization + idempotency + audit trail + zero sessions/assignment.
```

## Scores

```text
direction alignment score = 90/100
operational completion score = 35/100
```

(L1+L2 strong; L3 still closed by DEC-009=A.)

## Method / opinion

Most ownership/WC/DAG machinery already existed (F7A/DEC-010). Wave 2 closed the real Owner gap on foil sequencing, stamped ORR at Aggregate compile (not only freeze), locked decisions in tests, and surfaced WC provenance in Step 9B — without opening materialization or inventing minutes.
