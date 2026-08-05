# Task Resource Requirement — Read-Only Contract

**Task:** `TASK_RESOURCE_REQUIREMENT_READONLY_CONTRACT`  
**Owner GO:** `AUTHORIZE_TASK_RESOURCE_REQUIREMENT_READONLY_CONTRACT`  
**Date:** 2026-08-05  
**Branch:** `feat/f7i-owner-rate-activation`  
**Starting HEAD:** `9b3d95ff`  
**Architecture:** `docs/architecture/TASK_RESOURCE_REQUIREMENT_READONLY_CONTRACT.md`

---

## Verdict

```text
TASK_RESOURCE_REQUIREMENT_READONLY_CONTRACT = PASS
TASK_DEMAND_BOUNDARY = FINALIZED
RESOURCE_AVAILABILITY_BOUNDARY = FINALIZED
MINIMAL_CONTRACT = FINALIZED
NOW = identity + workcenter + nullable duration/source + derived UNKNOWN status + soft non-HYBRID mode hint
LATER = authoritative resource_mode, people, workspace, batch, duration splits, capability stamp
NULL_BEHAVIOR = PRESERVED
MACHINE_RUN / WORKSPACE_BOOKING / EMPLOYEE_AVAILABILITY = NOT_IMPLEMENTED
CAPACITY_STAGE_1 = IMPLEMENTED_INACTIVE
QA_MUTATIONS = 0
PHASE_B / PHASE_C = NOT_AUTHORIZED / BLOCKED
NEXT_TASK = NOT_AUTHORIZED
RECOMMENDED_NEXT_SLICE = TASK_RESOURCE_REQUIREMENT_READONLY_PROJECTION
```

---

## Key findings

1. EP tasks already carry WC routing + null-preserving minutes; not demand fields.  
2. HYBRID (METAL_FAB / VINYL on plan 23) cannot get authoritative `resource_mode` from WC.  
3. People / workspace / batch = UNKNOWN on protected plans.  
4. Missing demand → `RESOURCE_REQUIREMENTS_UNKNOWN`, never “no resources needed”.  
5. Next proportional slice = readonly projection of existing stamps — not schema, not MACHINE_RUN.

---

## QA zero-mutation

```text
s65 · Sched/Res ACTIVE · Capacity 0 · assign=7 · fk=0
SHA = b54d223f0f8929268319ff1589203d9999711908974cd60029395929ab9d28b4
```

---

## Method

Docs-only. Explore subagent for task field inventory; parent classified plans 21–22–23 and finalized NOW/LATER. No runtime. Overengineering avoided: no geometry, no auto-batch, no persisted soft mode for hybrids.

---

## Files

| Path | Change |
| ---- | ------ |
| `docs/architecture/TASK_RESOURCE_REQUIREMENT_READONLY_CONTRACT.md` | new |
| `docs/worklog/realignment/2026-08-05_task_resource_requirement_readonly_contract.md` | this |
| `docs/architecture/MACHINE_BATCH_AND_MANUAL_WORKSPACE_OWNER_DECISIONS.md` | pointer |
| `docs/architecture/realignment/21_WORKOS_IMPLEMENTATION_ROUTE.md` | route |

**No push.**
