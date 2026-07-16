# Worklog — Intake V6 Step2 layer UI + mounting + readiness implementation

**Date:** 2026-07-16  
**Task:** `WORKOS-INTAKE-V6-STEP2-LAYER-UI-MOUNTING-READINESS-IMPLEMENTATION-V1` +  
`WORKOS-INTAKE-V6-STEP2-RUNTIME-CLOSURE-AND-DEV-MODE-VERIFICATION-V1`  
**Starting HEAD (implementation):** `47cc4c1`  
**Implementation commit:** `463707b`  
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
- Letter section stacked Fata → Cant → Spate; logos Spate inside expand (later closed onto shared shell).
- Mounting sentinel `{ kind: installation_template, template_code: null }` BE+FE; composition inactive for ACM/metal.
- Compact banner with blocker/warning counts; map `MOUNTING_SOLUTION_MISSING`; residual “neconfirmat”; tariff flag without rows → diagnostic warning.
- Same-workspace PUT finish-setup: sentinel persisted; `MOUNTING_SOLUTION_MISSING` cleared; `backing_mode=forex_10_no_bevel` preserved; material-breakdown keys/total unchanged (725.16).

### Runtime closure — 2026-07-16

#### Dev-mode startup
- Command: `npm run dev:stack` with `FLEX_COLLAB_PHASE2_ENABLED=true` (Phase2 defaults true in code).
- Pre-check: `:8001` healthy uvicorn PID **30500**; `:3000` absent.
- Action: reused backend (`freshness=current_and_ready`); started frontend only via stack.
- After start: backend PID **30500** `:8001`; frontend PID **27124** `:3000`.
- Duplicate listeners: none created for backend; frontend newly bound.
- HEAD proof: Vite serves `IntakeV6LayerCardShell.tsx` from worktree; UI shows collapsed Față/Cant/Spate + sentinel Montaj.

#### Browser walkthrough (required)
- URL: `http://127.0.0.1:3000/intake-v6/11891d68-c4c8-4719-acc5-f8fcb22a44af/operator`
- Step 1: 6 layers (4 Vector Litere + 2 Vector Logo); composition letters + logo.
- Step 2 collapsed: compact cards; no Forex select; labeled summaries; logos “Print + laminare”.
- Step 2 expanded letter: Față → Cant → Spate; Forex only when expanded.
- Step 2 expanded logo: Print + laminare wording; Spate Forex inside expand.
- Montaj: Șablon checked; site install enabled; Soluție = Fără soluție suplimentară (sentinel); no ACM/metal child.
- Banner: compact counts; expandable; “neconfirmat”; `contains_missing_prices_inconsistent` as diagnostic warning.
- LED: illuminated, modules present (145).
- Evidence: `docs/qa/intake-v6-step2-runtime-closure/` (`01`–`06` PNGs + `api_nonregression_probe.json`).

#### Pricing / ProductDefinition non-regression
- `material-breakdown.totals.material_cost_total` = **725.16 EUR** (unchanged).
- Material keys retain `forex_backing` + logo artwork keys; ops retain `cnc_backing_cutting_forex_10mm`.
- No ACM material keys; mounting sentinel present; top-level `backing_mode=forex_10_no_bevel`; LED on.
- No registry / CostEngine / currency edits.

#### Fresh tests (post-review fix pass)
```
frontend vitest (7 files): 80 passed
backend pytest test_mounting_installation_template_sentinel.py: 5 passed
```

#### Independent review (`/ce-code-review`)
- Initial verdict: REQUEST_CHANGES
- Blocking fixed:
  1. Wire `collectMissingPriceLineKeysFromBreakdown` (no hardcoded empty keys while demoting tariff).
  2. Migrate logo cards onto shared `IntakeV6LayerCardShell` + stacked Față→Cant→Spate; logo collapsed-contract tests.
- Residual accepted: `contains_missing_prices` numeric root cause deferred to pricing audit (G3/plan).

#### Compound (`/ce-compound` headless)
- `docs/solutions/architecture-patterns/intake-v6-step2-layer-card-and-mounting-sentinel.md`

### Runtime writes
- Allowed previously: finish-setup PUT with installation_template sentinel.
- Closure: no new DB writes required for verification (read + UI).
- Not done: quote/order/execution/seed/Product System/pricing registry.

### Remaining limitations
- Logo Product System catalog seed (G3 document-only).
- `contains_missing_prices` root-cause numeric fix → GRADI-CURAT PRICING TRUTH AUDIT.
- Footer “Probleme și avertizări — N” can show a larger diagnostic pool than the compact Step2 banner; primary operator banner is the compact yellow one.

### Next
GRADI-CURAT PRICING TRUTH AUDIT
