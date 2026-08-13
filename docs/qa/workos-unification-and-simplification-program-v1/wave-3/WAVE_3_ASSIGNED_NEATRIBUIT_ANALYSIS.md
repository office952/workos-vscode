# Wave 3 — `assigned · Neatribuit`

Visible on `/operator` assignment rows, e.g. Painting `JOB-23099 · assigned · Neatribuit`.

## Classification (exactly one)

**ASSIGNED_NEATRIBUIT_ROOT_CLASS = FRONTEND_LABEL_COMPOSITION**

Underneath: **VALID_DISTINCT_FACTS**. Not a backend contradiction.

| Candidate | Why not |
|-----------|---------|
| BACKEND_CONTRADICTION | Backend `status=assigned` means “not started” (no `started_at`). `assigned_employee_id=null` is a second field. Both are consistent. |
| FRONTEND_LABEL_COMPOSITION | **YES** — one string concatenates English lifecycle key + Romanian “no employee” |
| STALE_READ_MODEL | Live GET matches the row |
| MISSING_EMPLOYEE_REFERENCE | Employee is honestly null; the bug is the English word “assigned”, not a missing join |
| VALID_DISTINCT_FACTS | True as the **data** reading; the **root class** of the visible collision is composition |
| UNKNOWN | Resolved |

## Map

| Field | Value (Painting / JOB-23099) |
|-------|------------------------------|
| BACKEND_ASSIGNMENT_STATE | `assigned` = no `started_at` / not ended / not blocked / not paused (`operator_tasks.list_all_tasks`) |
| EMPLOYEE_ID | `null` (`assigned_employee_id` and reality `employee_id`) |
| EMPLOYEE_LABEL | `Neatribuit` |
| FRONTEND_STATUS_SOURCE | raw `task.status` English key in `OperatorTaskAssignmentPanel` (`{jobId} · {status} · {assignedLabel}`) |
| FRONTEND_ASSIGNEE_SOURCE | `assignedEmployeeName \|\| assignedEmployeeId \|\| "Neatribuit"` |

`StatusBadge` domain `executionTask` would render `assigned` as **Alocat**. The colliding string uses the **raw key**, not the badge.

## Why the words collide

Backend `assigned` ≠ “assigned to a person”. It is the default queued lifecycle after plan materialization.

`Neatribuit` = no plan employee.

The UI prints both on one line without translating the lifecycle key, so a human reads “assigned and unassigned”.

## Related (not the same bug)

- Eligible pool (Calin / Octavian / Putaru) is a **soft preview**, not the assignee.
- Atelier live work is **Putaru Sandu on ORD-92400**, a different task.
- Ops-Graph has a separate assign picker — not clicked.

No fix in this GO.
