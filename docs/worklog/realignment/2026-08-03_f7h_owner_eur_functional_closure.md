# Worklog — F7H Owner EUR functional closure

**Status:** `FUNCTIONAL_PASS_WITH_UNPUBLISHED_RATE_GAPS`  
**Runtime closure:** `PASS_WITH_UI_WARNING` · Rounding `EXPECTED_RAW_PRECISION_ROUNDING` · Push `READY_NOT_PUSHED`  
**Scope:** Native EUR commercial path for Intake V6 volumetric letters + ACM through CPP → Snapshot V2 → Step 3. Final price audit deferred.  
**Identity:** worktree `C:\w\psiso`, branch `feat/capacity-batch-20d-scoped-b-92401`, implementation `7575e2c6`, honesty follow-up `6492cd15`, gitdir `C:\Users\offic\workos_app_vs\.git`. Stash `{0}` untouched.

## Architecture readback

Product Template / PD / PA do not own rates. Pricing Registry + commercial catalog own configurable rules. CPP ≠ EIC. Snapshot freezes. ExecutionPlan out of scope.

## Tariff research

Owner-confirmed commercial EUR: RAL labor 1/ml, montaj 200/location.  
Provisional commercial reuse of workcenter EUR (not dedicated sell decisions): CNC_ROUTER 1.5/ml, RETURN_PROFILE_MACHINE_FORMING 5/ml.  
Unpublished (fail-closed): back CNC EUR/m², LED module sell, PSU sell, RAL EUR minimum floor.  
Legacy 100 RON/color not converted. Research agent confirmed contradictions vs retired RON DEV_BRIDGE; no merge invented.

## Changes (implementation commits — not this docs commit)

- `backend/data/commercial_rules_volumetric_v2.py` — EUR catalog + presentation helpers + unpublished gaps  
- `backend/services/commercial_price_proposal_service.py` — native EUR, currency guards, RAL top-up  
- `backend/services/linked_logo_commercial_price_service.py` — presentation EUR  
- `backend/services/intake_v6_priced_quote_dry_run_service.py` — totals currency from presentation  
- schemas + Step 3 FE wiring + targeted tests + QA pack

## F7H-RUNTIME-CLOSURE-V1 proof

- Stale WorkOS `:8000` (PID 27932 / reloader from `C:\w\psiso\backend`) stopped under Owner GO; restarted via `.\scripts\dev-detached.ps1`.
- Fresh BE identity: `/api/v1/system/version` → `git_commit=6492cd15`; FE Vite on `:3000` from same worktree.
- Fresh dry-run `IV6-9C5D9538`: Litere raw 277.0707 → 277.07; ACM 190.7845 → 190.78; grand raw 467.8552 → **467.86**; sum of displays 467.85. FE formats backend total; does not sum subtotals.
- Step 3 UI: **Total ofertă (parțial)** 467,86 EUR; unpublished codes listed; handoff blocked; not labeled final.
- `MISSING_RETURN_PAINT_COLOR` absent on fresh dry-run/handoff (entry claim outdated); acceptance still blocked.
- Scenario B via controlled test `test_f7h_mixed_eur_ron_fail_closed` PASS (no runtime DB write).
- Protected baselines before/after restart PASS (1847.5 / 847.5, hashes a59b6c44 / 2d412e6e, plan22 tasks=5, pilot_gate_open=false).
- Screenshots: `docs/qa/F7H_OWNER_EUR_FUNCTIONAL_CLOSURE_V1/evidence/screenshots-runtime-closure/`.

## Remaining

Owner push decision for mechanism commits. Final commercial tariff pass remains separate.  
Materialization CLOSED. Scheduling HOLD. Push not executed.

**Direction score:** 92/100% (runtime identity closed; display 0.01 reconciliation + final tariffs remain).
