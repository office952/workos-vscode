# WorkOS V1 — Exit Record

**Date:** 2026-08-10  
**Owner GO:** `AUTHORIZE_WORKOS_V1_EXIT_VERIFICATION_RESUME`  
**Starting HEAD:** `71ec5b2b`  
**Baseline HEAD (Golden accepted):** `71ec5b2b`  
**Finalize note date:** 2026-08-10 (Owner product-set ack)  
**Branch:** `feat/f7i-owner-rate-activation`  
**Worktree:** `C:\w\psiso`

## Final verdict

```text
WORKOS_V1_EXIT_VERIFICATION_RESUME = PASS
WORKOS_V1_EXIT_VERIFICATION = PASS
WORKOS_V1_STATUS = FINALIZED_FOR_AGREED_SCOPE
WORKOS_V1_COMPLETION = 100_PERCENT_FOR_AGREED_V1_SCOPE
TECHNICAL_EXIT_CRITERIA = PASS
OWNER_ACKNOWLEDGMENTS = COMPLETE
EXIT_CRITERIA_BLOCKED = 0
OPEN_V1_TECHNICAL_BLOCKERS = 0
ACTIVE_V1_RISK = 0
PRODUCT_CODE_CHANGES = 0
DB_SCHEMA_CHANGES = 0
QA_MUTATIONS = 0
PUSH = NO
NEXT_RECOMMENDED_BUILD = NONE_BEFORE_RELEASE_DECISION
NEXT_TASK = NOT_AUTHORIZED
```

Owner product-set lines received 2026-08-10. V1 is finalized for the agreed Letters-only scope. Next action is a separate RELEASE / PUSH / DEPLOY decision or POST_V1 / V1.1 roadmap — not another V1 feature build.

## Locked accepted programs (not re-run)

| Program | Status |
|---------|--------|
| WORKOS_V1_GOLDEN_LETTERS_E2E_FINAL_PROOF | PASS |
| COMMERCIAL_OFFER / COMMERCIAL_OFFER_V1 | DONE_FOR_V1 |
| UI_HONESTY_V1 | DONE_FOR_V1 |
| LIGHT_THEME_V1 | DONE_FOR_V1 |
| PRODUCTION_READINESS_V1 | DONE_FOR_V1 |
| LETTERS_COMMERCIAL_CURRENCY | EUR |

## V1 scope (Owner-locked)

```text
WORKOS_V1_PRODUCT_SET = LETTERS_ONLY
LOGO_SOLD_ROOT_V1 = LATER
ACM_EXPANSION_V1 = LATER
Required product = Litere volumetrice luminoase (TPL-VOLUMETRIC-LETTERS_v2)
Deferred = Logo sold-root, ACM treatments, ACM cassette, other families
```

## Deployment model

```text
V1_DEPLOYMENT_MODEL = single-workstation / internal laboratory / Windows
DB_ENGINE = SQLite (DEC-DATABASE-01)
```

## Owner decisions

| Decision | Status |
|----------|--------|
| SQLite V1 | ACCEPTED (DEC-DATABASE-01) |
| MACHINE_COST_V1 | DECLARE_NA_FOR_V1 |
| OTHER_DIRECT_COST_V1 | DECLARE_NA_FOR_V1 |
| PROFITABILITY_CURRENCY_POLICY | A |
| WORKOS_V1_PRODUCT_SET = LETTERS_ONLY | **ACCEPTED** (Owner 2026-08-10) |
| LOGO_SOLD_ROOT_V1 = LATER | **ACCEPTED** (Owner 2026-08-10) |
| ACM_EXPANSION_V1 = LATER | **ACCEPTED** (Owner 2026-08-10) |

## Golden Letters proof reference

- Report: `docs/qa/workos-v1-golden-letters-e2e-final-proof/WORKOS_V1_GOLDEN_LETTERS_E2E_FINAL_PROOF_REPORT.md`
- Worklog: `docs/worklog/realignment/2026-08-10_workos_v1_golden_letters_e2e_final_proof.md`
- Runner: `backend/scripts/run_golden_letters_e2e_final_proof_v1.py`
- Proof HEAD: `71ec5b2b`

```text
V1_PRODUCT_FLOW = PASS
Intake → Product Truth → PD → Aggregate → CPP → Quote → Order
→ ExecutionPlan → Assignment → Session → Actuals → Profitability
```

## STATUS_RECONCILIATION_REQUIRED — labor money

Golden wording vs prior Labor Cost Rate Snapshot / readiness must not be silently merged.

| Claim | Source | Meaning |
|-------|--------|---------|
| `labor money N_A_FOR_V1` | Golden report lines (fixture observation) | Labor money absent on **this Golden run** |
| `LABOR_COST_RATE_SNAPSHOT_AUTHORITY = PASS` | `docs/architecture/LABOR_COST_RATE_SNAPSHOT_AUTHORITY.md` | Rate freeze writer + historical stability proven |
| `PROFITABILITY_ACTUAL_LABOR_COST_READINESS = READY` | Authority + roadmap §8 | Duration + stable rate + `finalize_labor_lines` → `ActualLaborCostLine` ready as input |
| `PROFITABILITY_MONETARY_CALCULATION = DONE_FOR_V1` | Policy A / actual read model | Canonical RM can include labor when lines exist |

**Exact reconciliation (do not rewrite prior READY):**

1. Labor monetary cost is **not** a product-set `DECLARE_NA_FOR_V1` category (unlike Machine / Other Direct).
2. Golden proved labor **minutes** (40 min session). It did **not** call `finalize_labor_lines`, so no `ActualLaborCostLine` rows were created for the Golden order.
3. Golden read `ProfitabilityAnalysisService` (`/profitability-analysis/...`), which still hardcodes labor-money exclusion and emits `hr_labor_cost_missing`. Operator UI labels that panel as legacy diagnostic; canonical Policy A surface is `/profitability-actual/...` (`profitability_actual_read_model_service`), which sums frozen labor lines when present.
4. Therefore Golden’s phrase `labor money N_A_FOR_V1` is a **fixture/path observation**, not a new Owner N/A declaration and not a rewrite of Labor Cost Rate Snapshot READY.
5. Exit criterion §14.6 remains **PASS** on accepted authority + prior labor packs. Golden did not re-exercise the finalize → actual-RM monetary path; that gap is honesty documentation, not a new technical blocker and not a silent PASS over contradiction.

```text
STATUS_RECONCILIATION_REQUIRED = DOCUMENTED
LABOR_MONEY_PRODUCT_LIMITATION = NOT_N_A_FOR_V1
GOLDEN_LABOR_MONEY = ABSENT_ON_FIXTURE_PATH (no finalize; legacy analysis reader)
PRIOR_LABOR_COST_READINESS = READY (unchanged)
MACHINE_COST / OTHER_DIRECT = N_A_FOR_V1 (unchanged)
```

## Exit criteria (§14 roadmap)

| # | Criterion | Status | Evidence | Blocker |
|---|-----------|--------|----------|---------|
| 1 | Letters Intake→PD/PA→CPP/EIC→Snapshot→Order | PASS | Golden Letters E2E Final Proof | — |
| 2 | Snapshots historically stable (no live reprice) | PASS | Golden + commercial closure | — |
| 3 | ExecutionPlan sold-scope tasks | PASS | Golden EP 18 operational tasks | — |
| 4 | Assign + controlled sessions | PASS | Golden assignment + 40 min session | — |
| 5 | MachineRun observe usable | PASS | MachineRun DONE_FOR_V1 (cost N/A) | — |
| 6 | Actual labor frozen/stable | PASS | Labor rate snapshot authority PASS; Golden time proven; see labor reconciliation | — |
| 7 | Actual material available/fail-closed | PASS | Golden material issue → known cost 2.125 | — |
| 8 | Profitability never invents | PASS | Policy A; Golden PARTIAL materials; labor honesty via reconciliation | — |
| 9 | No unauthenticated commercial/exec write bypass | PASS | Security write-gate DONE_FOR_V1 | — |
| 10 | HR salary not broadly readable | PASS | Security write-gate DONE_FOR_V1 | — |
| 11 | Required UI flows discoverable | PASS | UI honesty + Light Theme DONE_FOR_V1; health spot-check 2026-08-10 | — |
| 12 | Capacity / Phase E / PAUSE deferred honestly | PASS | Capacity IMPLEMENTED_INACTIVE; Phase E / PAUSE LATER | — |
| 13 | SQLite decision + production smoke | PASS | PRODUCTION_READINESS_V1 DONE_FOR_V1; `/health` healthy + FE 200 | — |
| 14 | Modules/Governance match closed-domain truth | PASS | Prior exit + closed domains; no reopen of Light/Commercial | — |

```text
EXIT_CRITERIA_TOTAL = 14
EXIT_CRITERIA_PASS = 14
EXIT_CRITERIA_NOT_APPLICABLE_BY_V1_SCOPE = 0
EXIT_CRITERIA_BLOCKED = 0
```

## Commercial / UI / Execution / Profitability (final)

```text
COMMERCIAL_OFFER_V1 = DONE_FOR_V1
LETTERS_COMMERCIAL_CURRENCY = EUR
UI_HONESTY_V1 = DONE_FOR_V1
LIGHT_THEME_V1 = DONE_FOR_V1
EXECUTION_PLAN / ASSIGNMENT / SESSIONS / MACHINE_RUN = PASS_FOR_V1
MATERIAL_ACTUALS = PASS_FOR_V1
LABOR_ACTUAL_TIME = PASS_FOR_V1
LABOR_MONEY = READY_CAPABILITY (not auto on Golden path; see reconciliation)
Machine Cost = N_A_FOR_V1
Other Direct = N_A_FOR_V1
Policy A = FROZEN_CURRENT
PRODUCTION_READINESS_V1 = DONE_FOR_V1
```

## Accepted V1 limitations

- Machine monetary cost = `N_A_FOR_V1`
- Other Direct = `N_A_FOR_V1`
- Capacity Stage 1 = `IMPLEMENTED_INACTIVE`
- REASSIGNMENT_PHASE_E = `LATER`
- PAUSE/RESUME = `LATER`
- Postgres = `LATER`
- Logo sold-root = `LATER`
- ACM expansion = `LATER`
- Advanced Inventory/MRP = `LATER`
- P2/P3 UI polish = `POST_V1`
- Snapshot-authoritative freeze does not carry live Adaos (Golden uses 0% markup path)

## POST_V1 / after FINALIZED

1. Separate RELEASE / PUSH / DEPLOY decision — not another feature build  
2. Logo / ACM / Capacity / Phase E / PAUSE / Postgres / machine-other cost — only under new Owner GOs  
3. P2/P3 UI polish = POST_V1  

## Owner acknowledgments (complete)

```text
WORKOS_V1_PRODUCT_SET = LETTERS_ONLY
LOGO_SOLD_ROOT_V1 = LATER
ACM_EXPANSION_V1 = LATER
OWNER_ACKNOWLEDGMENTS = COMPLETE
```
