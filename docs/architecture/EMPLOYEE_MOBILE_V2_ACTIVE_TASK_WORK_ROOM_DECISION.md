# Employee Mobile v2 — Active Task Work Room Decision

| Field | Value |
|-------|-------|
| **Status** | Foundation implemented — advanced multi-person deferred |
| **Branch context** | `local/integration-pr4-plus-svg-path` |
| **Route** | `/employee-app-v2/tasks/:taskId` (Work Room) |
| **v1 boundary** | `/employee-app` unchanged |

## Context

Employee Mobile v2 improves list/pipeline UX but lacked a dedicated operational surface after **Start Task**. Tasks live in `execution_plan.tasks_json` (plan) and `execution_reality.tasks_json` (work sessions). There is no separate ORM `ExecutionTask`.

Employee mobile already supports **start / block / complete / unblock** and **clarification requests**. Operator desktop supports **pause / resume**; mobile did not until this foundation build.

## Decision

**Work Room is the correct direction.** After Start (or when opening an active task), the employee works on a dedicated mobile-first screen focused on actions and short context — not a long detail scroll.

```text
Home / Listă → tap task → Work Room
Start reușit → rămâne / revine în Work Room (aceeași rută)
```

## Included in this build

- Architecture decision doc (this file)
- Employee-mobile API: **pause** (Întrerup lucrul) and **resume** (Reiau lucrul) on the authenticated employee's session
- Fix **`derive_task_status_from_sessions`**: global `done` only when no active sessions remain
- Employee-aware status in mobile list via **`derive_task_status_for_employee`**
- v2 **Work Room** layout: operational header, context, primary actions, collapsible secondary details
- Start → stay/navigate Work Room (same route, refreshed state)
- **Blocked vs Întrerup**: distinct semantics and UI copy
- Minimal **block_reason** visibility in OperatorView (+ API field on operator task list)
- Real-only participant hint: „Lucrezi singur” / „+N colegi activi” from `active_helper_count`
- Targeted backend + frontend tests

## Deferred

- Join / assist mobile endpoints
- Multi-person completion confirmations („Am terminat partea mea” flow)
- `ExecutionTaskIssue` entity
- Notification Center / issues inbox
- Off-shift auto-close from attendance
- v2 promotion over v1 / PWA `start_url` changes
- DB migrations (JSON reality model sufficient)

## Blocked vs Întrerup lucrul

| | **Blocked** | **Întrerup lucrul** |
|---|-------------|---------------------|
| Meaning | Real impediment — work cannot continue | Employee leaves temporarily — not an impediment |
| Examples | Missing material, wrong size, broken equipment, waiting decision | End of shift, internal urgency, normal break, reassigned temporarily |
| Requires reason | Yes (category + optional text) | No |
| Sets `blocked_at` | Yes | No — sets `paused_at` on session |
| Admin visibility | `block_reason` shown | Session paused; task not blocked |

## Multi-person rules

- **Do not** mark task globally `done` when one participant completes while other sessions are still active.
- **Do not** fake participant names or avatars in mobile UI.
- `active_helper_count` may show „+N colegi activi” only — no join/assist actions in this build.
- Global finalize with confirmations remains a later build.

## PASS / FAIL

**PASS** when:

- v1 `/employee-app` functionally untouched
- v2 Work Room coherent; Start lands in Work Room
- Pause/resume mobile work; pause ≠ blocked
- Block requires reason; visible minimally in admin
- Multi-session partial complete does not yield global `done` while others active
- Single-worker complete still yields `done`
- No fake participants; no migrations; targeted tests green

**FAIL** when:

- v1 regresses; v2 promoted; PWA changed
- Pause maps to blocked; partial multi-complete marks global done
- Buttons without backend; invented participants
- join/assist/issues/confirmations shipped in this build

## Next build (recommended)

**Employee Mobile v2 Task Issues & Assist** — `ExecutionTaskIssue` or structured reporting, join/assist API, participant list with privacy rules, lead-only global complete policy.
