# Wave 3 — `/operator` information model

| Field | Value |
|-------|--------|
| Surface | `/operator` |
| Data source | `GET /api/v1/operator/tasks` — all execution plans |
| Snapshot | 234 tasks / 19 orders |

## Why the page is ~75 k px

The API returns **every operational task from every execution plan**. The UI then renders that snapshot **twice**:

1. `OperatorTaskAssignmentPanel` — all tasks except `done` / `cancelled` → **222** rows
2. `Next Tasks` — `status === assigned || created` → **220** rows

Plus header, eligibility pool, policy banner, blueprint panel, and a per-job timeline at the bottom.

There is no page size, virtualization, active-only default, or time window.

## Mix inventory

| Kind | Present? | Evidence |
|------|----------|----------|
| current / in_progress | YES | 2 tasks; Atelier live job is one of them (`ORD-92400`) |
| historical / other orders | YES | 19 `order_id`s including 23099, 92400–92403, 880750, 973024 |
| completed | YES | 12 `done` (counted in KPI; excluded from assignment list) |
| blocked | NO in this snapshot | `byStatus` has no `blocked` |
| unassigned (no employee) | YES | majority of `assigned` rows; `assigned_employee_id=null` |
| multiple workcenters | YES | print, CNC, assembly, paint, LED, packaging, QC |
| repeated task projections | YES | same `task_id` (`…:painting`) on 23099 / 880750 / 880811; assignment list + Next Tasks duplicate the queued set |
| stale / lab rows | YES | claim-policy / wave fixtures (`T-M06-CLAIM-POLICY`, `ORD-W5INT02-GATE`) sit next to IV6 work |
| polling duplicates | NO | `/operator` does not poll |
| inactive work | YES | queued `assigned` with no `started_at` is the default status |

## Controls

| Control | Value |
|---------|--------|
| FILTERS | none on the list (URL `?orderId=` only biases blueprint default) |
| GROUPING | none (flat assignment + flat Next Tasks) |
| SORTING | plan `order_id ASC` then plan task order |
| TIME_BOUNDARY | **none** |
| STATUS_BOUNDARY | UI splits current / next / done-count; API still returns all |
| HISTORY_BOUNDARY | **none** |
| ACTIVE_ONLY_OPTION | **none** |
| PAGINATION | **none** |
| VIRTUALIZATION | **none** |

## Classification (exactly one)

**OPERATOR_INFORMATION_MODEL = UNBOUNDED**

Not CLEAR (no priority or “now” frame). Not merely DENSE (the height is the unfiltered corpus). OVERLOADED is also true as a UX reading; the structural class is **UNBOUNDED** because the read model has no history/active/time termination.

## Findings (no implementation)

- `NO_PRIORITY_MODEL`
- `NO_TIME_BOUNDARY`
- `HISTORICAL_AND_ACTIVE_MIXED`
- `OVER_FRAGMENTED_TASKS`
- `TECHNICAL_LABELS` (`CONFIRM_GEOMETRY`, `node:root_product:…`, policy `ORDER AND PLAN ALLOWED TASK START BLOCKED`, `JOB-*`)
- `DUPLICATE_TASK_PROJECTION` (assignment panel + Next Tasks; same painting `task_id` across orders)
- `UNBOUNDED_LIST`
