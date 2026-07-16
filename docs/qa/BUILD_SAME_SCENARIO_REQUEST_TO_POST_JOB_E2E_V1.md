# BUILD — Same-Scenario Request → Post-Job E2E Truth V1

**Date:** 2026-07-17  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Baseline planning commit:** `4da68ed`  
**Owner:** `ALEGEM BUILDUL 1` + G1–G4 + `IMPLEMENTARE = GO`

## Purpose

Prove one continuous Letters lineage Request → Post-Job without stitching to order `23099`.

## Context

- Master next after post-job V1: same-scenario E2E  
- Live PA had empty `task_contract.task_rules` despite dossier `task_rules_json` → Plan V2 blocked  
- Fix: compile dossier task rules into ProductAggregate  

## Lineage (disposable)

| Stage | ID |
|-------|-----|
| Intake request | `IR-BUILD1-1784237119` |
| Workspace | `e1b8d1e8-0197-4723-882a-037c41c64d35` |
| Quote | `3` |
| Quote Snapshot V2 | `QSN2-2026-0002` (13 task_rules) |
| Order | `92402` / `ORD-IV6-V2-1784237123-3` |
| Execution plan | `8` (18 tasks materialized) |
| Reality | 1 closed session (`vector_prep`) |
| Post-job | `GET /api/v1/execution/92402/post-job-truth` OK |

Template: `TPL-VOLUMETRIC-LETTERS_v2` · no Logo root · not order `23099`.

## Files changed

- `backend/services/product_aggregate_service.py` — dossier task_rules compile  
- `backend/tests/test_product_aggregate_volumetric_v2.py` — focused test  
- `docs/qa/same-scenario-e2e-2026-07-16/` — HTTP + UI evidence  
- worklog / decision-log updates  

## Commands + results

```text
pytest tests/test_product_aggregate_volumetric_v2.py::test_aggregate_compiles_dossier_task_rules_for_execution_plan
→ 1 passed

Live walk (8001): IR→ensure→dry-run→draft→priced-write→snapshot-v2→review→owner→accept→convert
→ plan-v2 preview/persist/materialize → owner-decision resolve → reality start/end → post-job
→ PASS critical path

UI: http://127.0.0.1:3000/execution/92402
→ order/plan/reality present; task vector_prep Finalizat
```

## Boundary

**In:** continuous lineage proof; PA task_rules compile; evidence  
**Out:** Logo root; W0-B6; Mobile; PreOrder materialize; permanent seed; full inventory redesign; labor money  

## Explicit gaps (not simulated)

- Planning minutes still partial (`PLANNING_MINUTES_SOURCE_REQUIRED`)  
- Stock deduction not forced when ineligible (G3)  
- Labor money excluded (PARTIAL profitability)  
- Fixture setup cloned known Letters payload into **new** IR (not stage stitch)

## Modules / Governance

- `/modules`: update runtime evidence / status refs for same-scenario proof when owner promotes  
- `/governance`: NO ownership change; Logo boundary unchanged  

## Next

Update master STATUS stamp to same-scenario proof recorded; optional follow-up for planning-minutes completeness (separate build).
