# Production Readiness Dependency Gates — Decision

## Problem (confirmed audit)

WorkOS allowed physical execution (CNC, print/vinyl, operator/reality start) before critical preparation was complete. Readiness was partially enforced on Employee Mobile but bypassable from Operator and ExecutionDetail. `vector_prep` did not block CNC; template decisions did not block `mounting_template_cnc_cut`; document handoff did not block execution.

## Goal

Unified backend start gate: **no cut, print, or assembly start until critical preparation is done**, unless an explicit audited override is used.

## MVP gates (this build)

### CNC gate

| Successor | Predecessor / rule |
|-----------|-------------------|
| `face_cnc_cut` | `vector_prep` done |
| `back_cut` | `vector_prep` done |
| `mounting_template_cnc_cut` | `vector_prep` done (when task exists for Forex) |
| Any task with `machine_type` in `CNC_ROUTER`, `CNC` | `vector_prep` done (fallback when no explicit rule) |

Unsatisfied predecessor on `vector_prep` → readiness `waiting_file` with operator-facing message.

**Exception:** Tasks without CNC router machine type and without explicit CNC process_id are not auto-gated by machine_type fallback.

### Template gate (`mounting_template_cnc_cut`)

| `mounting_template_material_type` | Behavior |
|-----------------------------------|----------|
| `forex` | Requires type=forex, template area, material `MAT-SABLON-MONTAJ`, existing material conditions |
| `paper` | **Blocks** CNC — paper templates are not CNC-cut |
| `none` | **Blocks** — no CNC template task should run |
| missing / invalid | `waiting_template_decision` |

### Print / vinyl gate (partial)

Implemented only where real quote_input fields exist:

- When `face_finish_type` implies vinyl, blocks if `face_vinyl_color_code` or Oracal roll width metadata is missing.

**Deferred:** Generic print file required gate — no reliable required-print-file source in plan/snapshot yet.

### Document / workshop info gate

**Deferred for blocking:** Status codes `waiting_document`, `waiting_workshop_info` are reserved. No generic block on missing documents until required/critical document marking exists in the task contract.

### Material `not_checked`

Remains **warning** in procurement summary. Becomes block only when existing project-critical + procurement rules say `can_block_if_missing` (unchanged from manual procurement MVP).

## What blocks start

- Unsatisfied physical dependencies (`waiting_predecessor`)
- Unsatisfied `vector_prep` for CNC (`waiting_file`)
- Invalid/missing template decision for mounting CNC (`waiting_template_decision`)
- Missing vinyl metadata when finish type requires it (`waiting_file` / preparation reason)
- Project-critical material procurement block (`waiting_material`) — existing rules only
- Manual block on task (`blocked_manual`)

## What does not block

- Generic missing documents
- All materials with `not_checked` status
- Pricing / template costing fields alone (e.g. `mounting_template_material_type` for pricing without CNC task)
- Employee Mobile UX paths (same backend gate; no new mobile UI)

## Override policy

- Parameters: `override_readiness: true`, `override_reason` (min 3 characters)
- Roles: `admin`, `operator` only
- Stored in reality session `initial_fields` / metadata JSON — **no migration**
- API responses indicate override when used
- UI: ExecutionDetail disables Start until reason entered; Operator task-action accepts same fields
- **No silent bypass** on any start path

## Shared gate

`assert_task_startable()` in `task_start_gate_service.py` is invoked from:

1. `employee_mobile_tasks_service.start_my_task`
2. `operator_tasks` start action
3. `execution.reality/start-task`

## Deferred (next builds)

- Required/critical document blocking
- Generic print file gate
- Lead-specific override role granularity
- Notification Center surfacing of readiness blockers
- Auto-assignment / join-assist integration

## Out of scope (boundary)

CostEngine, Pricing, ProductSystem pricing registry, PWA/start_url, Employee Mobile Work Room UX, DB migrations, Notification Center.
