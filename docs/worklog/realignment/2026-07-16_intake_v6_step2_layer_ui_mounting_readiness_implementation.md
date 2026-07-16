# Worklog — Intake V6 Step2 layer UI + mounting + readiness implementation

**Date:** 2026-07-16  
**Task:** `WORKOS-INTAKE-V6-STEP2-LAYER-UI-MOUNTING-READINESS-IMPLEMENTATION-V1`  
**Starting HEAD:** `47cc4c1`  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Workspace:** `11891d68-c4c8-4719-acc5-f8fcb22a44af`  
**Owner gates:** G1 YES · G2 YES · G3 YES DOCUMENT-ONLY · G4 YES  

## Progress

### Kickoff
- Plan accepted; implementation authorized.
- Method: tests first → shell → adapters → mounting sentinel → banner → same-workspace verify → commit.
- Pricing numerical changes: NO. Logo seed: NO. Migration: none.

### U1–U7 completed
- Shared `IntakeV6LayerCardShell` + collapsed Spate summaries; Forex select only when expanded.
- Letter section stacked Fata → Cant → Spate; logos Spate inside expand.
- Mounting sentinel `{ kind: installation_template, template_code: null }` BE+FE; composition inactive for ACM/metal.
- Compact banner with blocker/warning counts; map `MOUNTING_SOLUTION_MISSING`; residual “neconfirmat”; tariff flag without rows → diagnostic warning.
- Same-workspace PUT finish-setup: sentinel persisted; `MOUNTING_SOLUTION_MISSING` cleared; `backing_mode=forex_10_no_bevel` preserved; material-breakdown keys/total unchanged (725.16).

### Tests run
```
frontend vitest: mountingSolution, banner display/component, letter collapsed contract,
  letter finishes, artwork finishes, quote handoff readiness — 76 passed
backend pytest: test_mounting_installation_template_sentinel + mounting_solution_intake_reference — 18 passed
```

### Runtime writes
- Allowed: finish-setup PUT on workspace `11891d68-…` with installation_template sentinel + confirmed=true.
- Not done: quote/order/execution/seed/Product System/pricing registry.

### Remaining / deferred
- Logo Product System catalog seed (G3 document-only).
- `contains_missing_prices` root-cause numeric fix → GRADI-CURAT PRICING TRUTH AUDIT.
- Full browser visual walkthrough on :3000 (UI code ready; API mounting verified).

### Next
GRADI-CURAT PRICING TRUTH AUDIT
