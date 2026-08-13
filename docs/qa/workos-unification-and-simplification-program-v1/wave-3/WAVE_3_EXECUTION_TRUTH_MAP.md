# Wave 3 — execution truth map

| UI concept | Frontend | API (GET) | Backend owner | Persisted | Mutation authority | User-facing? | Should be? |
|------------|----------|-----------|---------------|-----------|--------------------|--------------|------------|
| ExecutionPlan | ExecutionDetail / dashboard | `/execution/plan/{id}` | `execution_plan` | `tasks_json` / V2 envelope | plan-from-order / plan-v2 (not used) | “Plan de execuție” | YES (manager) |
| Operational task | ops-graph, operator, mobile | plan + `/operator/tasks` | V2 `operational_tasks[]` | envelope + reality | assign / task-action (not used) | task name / ops_display_label | YES |
| Operation identity | WC keys, process_type | preview / task-truth | catalog / CNC model | template/snapshot | design-time | often shown as `CNC_ROUTING` | NO as card title |
| MachineRun | list/detail | `/resource-state/machine-runs` | machine_run commands | machine_run rows | create/start (not used) | Rulări utilaj | YES if distinct |
| Employee session | operator / mobile / reality | `/execution/reality/{id}` | `execution_reality.tasks_json` | sessions | start/end (not used) | “În lucru” | YES, not = task |
| Actuals | PlanActual / reality-review | `/execution-actuals`, `/reality` | ExecutionReality | minutes/materials | complete/materials | Actual column | YES, vs plan |

Parallel truth: operator API vs employee-mobile vs reality start-end vs MachineRun lifecycle.
