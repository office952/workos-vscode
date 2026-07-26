# Task / Execution Boundary — Montaj

## Intake V6 task preview (runtime)

`GET /api/v1/intake-v6/workspaces/{id}/task-preview` → `acm_task_preview.json`

- `preview_only: true`
- Items from **operation_catalog** for volumetric pilot (graphic preflight, production model confirm, CNC file prep, etc.)
- Not a parallel full execution system

## Montaj influence on tasks

| Source | Effect |
|--------|--------|
| Mounting template Forex | Conditional plan inclusion via `volumetric_conditional_plan_tasks_service` + readiness `task_preparation_readiness_service` (area/material) |
| Segmented background/electrical | Explicitly **informational only** — no materialization (`future_task_intent_authority: INFORMATIONAL_ONLY` in PD proposal marker) |
| ACM local face modules | No tasks (UI states this) |
| Commercial site montaj | Offer/commercial — not shop task generation here |
| Accesorii 5% | Cost estimate — not a task |

## Duplicate catalog risk

- Operation catalog preview vs ProductAggregate `task_contract` / dossier `task_rules_json` are separate read models.
- Aggregate warning: dossier metadata vs task_rules consumption for ExecutionPlan V2 — **not** Intake creating a second writer.
- Metal module trigger field mismatch (`metal_support_required` vs `mounting_system`) is a **parallel activation** smell, not dual task writers.

## Verdict

Intake V6 Montaj **does not** create a parallel execution task system. It previews catalog operations and may gate Forex template CNC readiness. Segmented/electrical remain non-executing by contract.
