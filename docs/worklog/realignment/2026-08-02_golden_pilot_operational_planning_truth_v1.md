# Worklog — Golden Pilot Operational Planning Truth V1

**Date:** 2026-08-02  
**Repo:** `C:\w\psiso`  
**Branch:** `feat/capacity-batch-20d-scoped-b-92401`  
**Prior pushed tip:** `9714ddd8`  
**Build commit message:** `Establish operational planning truth` (local only)

## What changed

- Canonical ORR workcenter resolution at Quote Snapshot freeze (DEC-010).
- Planning-duration fact collection now flattens `quote_geometry`; duration runs after ORR ensure-ops so `vector_prep` receives formula minutes.
- EP V2 consumes frozen Aggregate WC only; materializer persists `workcenter` + `machine_requirement`.
- DEC-009: protect `973015`; next_dry = `973018/20` (`FIX-GOLDEN-PILOT-PLANNING-TRUTH-V1`).
- Ops-Graph copy for unconfigured WC / missing minutes; quieter post-materialize banner.
- Read-only eligibility readiness audit service.

## Fixture

`order_id=973018` · `plan_id=20` · 18 ops · 24 deps · vector_prep 10 min · 15 WC resolved · 3 LED ambiguous · 0 sessions/actuals/assignments.

## Evidence

`docs/qa/golden-pilot-operational-planning-truth-v1/WORKOS_GOLDEN_PILOT_OPERATIONAL_PLANNING_TRUTH_V1_REPORT.md`
