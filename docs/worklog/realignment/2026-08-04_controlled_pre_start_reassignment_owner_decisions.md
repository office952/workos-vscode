# Controlled Pre-Start Reassignment — Owner Decisions Only

| Field | Value |
| ----- | ----- |
| Date | 2026-08-04 |
| Task | `CONTROLLED_PRE_START_REASSIGNMENT_OWNER_DECISION_ONLY` |
| Status | **`CONTROLLED_PRE_START_REASSIGNMENT_OWNER_DECISIONS = RECORDED`** |
| Starting HEAD | `dbe76f28` |
| Content commit | `eeb827a9` |
| Final HEAD | `72b32f48` |
| Repo / worktree | `C:\w\psiso` |
| Branch | `feat/f7i-owner-rate-activation` |
| Production / FE / tests / DB changed | **NO** |
| Implementation authorized | **FALSE** |

## Verdict

```text
CONTROLLED_PRE_START_REASSIGNMENT_OWNER_DECISIONS = RECORDED
FINALIZATION_WAVE_8 = PASS
REASSIGNMENT_IMPLEMENTED = NO
UNASSIGNMENT_IMPLEMENTED = NO
IMPLEMENTATION_AUTHORIZED = FALSE
PERSISTED_MUTATIONS = NONE
WAVE_9 = NOT_AUTHORIZED
```

## Repo identity (preflight)

| Item | Value |
| ---- | ----- |
| Root | `C:/w/psiso` |
| Branch | `feat/f7i-owner-rate-activation` |
| Starting HEAD | `dbe76f281f62350ad34382e6463f2b903d7b6be6` |
| Tracked changes | none |
| Untracked leftovers | preexisting `docs/qa/**`, `_qa_backups` — untouched |
| Ancestry | `dbe76f28` OK · Wave 8 impl `06dcefd1` OK · Wave 7 closure ancestry OK |

## Decisions recorded

| ID | Value |
| -- | ----- |
| DEC-REASSIGN-01 | `MANAGER_AND_ADMIN_ONLY` |
| DEC-REASSIGN-02 | `STRICT_PRE_START_ONLY` |
| DEC-REASSIGN-03 | `RETAIN_FULL_ASSIGNMENT_TRANSITION_HISTORY` |
| DEC-REASSIGN-04 | `REASON_CODE_REQUIRED` |
| DEC-REASSIGN-05 | `ALLOWED_ONLY_PRE_START_BY_MANAGER_OR_ADMIN` |
| DEC-REASSIGN-06 | `NOT_REQUIRED_FOR_FIRST_PRE_START_BUILD` |
| DEC-REASSIGN-07 | `EXPECTED_CURRENT_EMPLOYEE_CAS` |
| DEC-REASSIGN-08 | `BLOCK_WHEN_SCHEDULING_OR_RESERVATION_EXISTS` |

Canonical document: `docs/architecture/CONTROLLED_PRE_START_REASSIGNMENT_DECISIONS.md`  
Pointer (no duplicate body): `docs/architecture/ASSIGNMENT_OBSERVABILITY_AND_REASSIGNMENT_POLICY.md` §6.

## Resulting contract (summary)

Manager/admin + distinct permission; pre-start only; no session/schedule/reservation/capacity; expected-current CAS; DEC-015 on new employee inside lock; reason required; full transition history; unassignment under same guards; no employee acknowledgement in first build; Mobile frozen; post-start transfer = future architecture.

## Persistence implications

Implementation readiness must prove whether embedded `tasks_json` can retain append-safe multi-transition history. If not → stop for `OWNER_DECISION_REQUIRED = SCHEMA_CHANGE` / `REASSIGNMENT_PERSISTENCE_MODEL`. No ad-hoc JSON history without audit.

## Authorization implications

Conceptual `execution.task_reassign` / `execution.task_unassign`. Do not reuse `execution.task_assign` as sufficient. Scope: actor + permission + order + plan + task + current/new employee context.

## Observability implications

Future reassignment/unassignment events and privacy boundary documented in the decisions file. No event table created.

## Files changed

| File | Why |
| ---- | --- |
| `docs/architecture/CONTROLLED_PRE_START_REASSIGNMENT_DECISIONS.md` | Canonical Owner decisions |
| `docs/architecture/ASSIGNMENT_OBSERVABILITY_AND_REASSIGNMENT_POLICY.md` | Point to recorded decisions |
| `docs/architecture/ASSIGNMENT_COMMAND_REMEDIATION_DECISIONS.md` | Gate + next candidate pointer |
| `docs/architecture/realignment/21_WORKOS_IMPLEMENTATION_ROUTE.md` | Route pointer — implementation not started |
| this worklog | Evidence |

## Zero mutation

Before = after:

| Field | Value |
| ----- | ----- |
| tasks_json SHA | `00ee947c0b5e2da587c0d0563f1051ca89379d66cfec434e75dbe3883ccfc1f2` |
| updated_at | `2026-08-04 19:16:57.407320` |
| LED employee | 7 |
| assigned / unassigned | 1 / 12 |
| sessions / machines | 0 |
| scheduling | HOLD |

Assignment / plan fields above are unchanged vs preflight. Full `dev.db` file SHA changed (`b67c76f0…` → `0f6a0332…`) with identical size while this docs-only task made **no** assignment API calls — attributed to incidental live local SQLite activity (detached uvicorn on `:8000`), not to reassignment/unassignment. Protected assignment truth remains the Wave 7 LED→7 record.

```text
ASSIGNMENT_REQUESTS = 0
REASSIGNMENT_REQUESTS = 0
UNASSIGNMENT_REQUESTS = 0
SUCCESSFUL_MUTATIONS = 0
```

## Protected baselines / F7I

| Order | Reality |
| ----- | ------- |
| 880811 | present plan 22 — unchanged |
| 973019 | present plan 21 — unchanged |
| 88002 | absent — unchanged |

F7I 15 / 1.5 / 35 / 20 EUR — untouched (no code/data edits).

## Dead Pieces Check

| Piece | Class |
| ----- | ----- |
| `allow_reassign` | `BLOCKED_LEGACY` |
| `clear_plan_task_assignment` | `ACTIVE_LEGACY` |
| direct reassignment helper | `BLOCKED_LEGACY` / `SUPERSEDED` |
| Mobile claim / start_from_available | `BLOCKED_LEGACY` |
| old UI reassignment actions | `UNKNOWN` / not authorized product controls |
| legacy bypass tests | `ACTIVE_LEGACY` |

```text
Dead pieces removed: NONE
```

## Scores

```text
Direction alignment score: 96/100
Operational completion score: 35/100
```

Operational score low by design: decisions only; no reassignment/unassignment build.

## Roadmap checkpoint

```text
Wave 8 PASS retained
One QA assignment retained
Reassignment not implemented
Unassignment not implemented
Machine assignment closed
Sessions closed
Scheduling HOLD
Capacity NOT_STARTED
Employee Mobile FROZEN_FINAL_FINAL
Production rollout NOT_AUTHORIZED
```

## Next step

```text
FUTURE CANDIDATE:
CONTROLLED_PRE_START_REASSIGNMENT_IMPLEMENTATION_READINESS_AUDIT
```

Not started. Awaiting Owner review.
