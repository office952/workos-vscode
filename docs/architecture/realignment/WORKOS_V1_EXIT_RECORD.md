# WorkOS V1 — Exit Record

**Date:** 2026-08-09  
**Owner GO:** `AUTHORIZE_WORKOS_V1_EXIT_VERIFICATION`  
**Starting HEAD:** `2e522b6c`  
**Branch:** `feat/f7i-owner-rate-activation`

## Final verdict (this verification)

```text
WORKOS_V1_EXIT_VERIFICATION = TECHNICALLY_READY_OWNER_ACK_PENDING
TECHNICAL_EXIT_CRITERIA = PASS
WORKOS_V1_STATUS = NOT_FINALIZED_UNTIL_OWNER_ACK
```

## V1 scope (expected / pending formal lock)

```text
V1_PRODUCT_SET = LETTERS_ONLY (awaiting formal Owner line)
Required product = Litere volumetrice luminoase (TPL-VOLUMETRIC-LETTERS_v2)
Deferred = Logo sold-root, ACM treatments, ACM cassette, other families
```

## Deployment model

```text
V1_DEPLOYMENT_MODEL = single-workstation / internal laboratory (Windows)
DB_ENGINE = SQLite (DEC-DATABASE-01)
```

## Owner decisions

| Decision | Status |
|----------|--------|
| SQLite V1 | ACCEPTED (DEC-DATABASE-01) |
| MACHINE_COST_V1 | DECLARE_NA_FOR_V1 |
| OTHER_DIRECT_COST_V1 | DECLARE_NA_FOR_V1 |
| PROFITABILITY_CURRENCY_POLICY | A |
| WORKOS_V1_PRODUCT_SET = LETTERS_ONLY | **MISSING formal ack** |

## Exit criteria (§14 roadmap)

| # | Criterion | Status | Evidence |
|---|-----------|--------|----------|
| 1 | Letters Intake→PD/PA→CPP/EIC→Snapshot→Order | PASS | Commercial + Letters packs; roadmap A/C/D/F/G/H DONE_FOR_V1 |
| 2 | Snapshots historically stable (no live reprice) | PASS | Order Snapshot no_reprice; commercial closure |
| 3 | ExecutionPlan sold-scope tasks | PASS | EP DONE_FOR_V1 |
| 4 | Assign + controlled sessions | PASS | Phase B assignment + session safety packs |
| 5 | MachineRun observe usable | PASS | MachineRun DONE_FOR_V1 (cost N/A) |
| 6 | Actual labor frozen/stable | PASS | Labor input closure + historical rate |
| 7 | Actual material available/fail-closed | PASS | Material actuals DONE_FOR_V1 |
| 8 | Profitability never invents | PASS | Policy A + composition DONE_FOR_V1; 30 pytest |
| 9 | No unauthenticated commercial/exec write bypass | PASS | Security write-gate DONE_FOR_V1 |
| 10 | HR salary not broadly readable | PASS | Security write-gate DONE_FOR_V1 |
| 11 | Required UI flows discoverable | PASS | `/modules` live spot-check 2026-08-09 |
| 12 | Capacity / Phase E / PAUSE deferred honestly | PASS | Modules Capacity `IMPLEMENTED_INACTIVE` |
| 13 | SQLite decision + production smoke | PASS | Readiness pack + runbook |
| 14 | Modules/Governance match closed-domain truth | PASS | `/modules` Profitability DONE; Capacity inactive |

```text
EXIT_CRITERIA_TOTAL = 14
EXIT_CRITERIA_PASS = 14
EXIT_CRITERIA_NA = 0
EXIT_CRITERIA_BLOCKED = 0
```

## Accepted V1 limitations

- Machine monetary cost = `N_A_FOR_V1`
- Other Direct = `N_A_FOR_V1`
- Capacity Stage 1 = `IMPLEMENTED_INACTIVE`
- REASSIGNMENT_PHASE_E = `DEFERRED_LATER`
- PAUSE/RESUME = `DEFERRED_LATER`
- Postgres = `LATER`
- Logo/ACM expansion = `LATER`
- Advanced warehouse/MRP / enterprise observability = `LATER`
- `printed_vinyl` finish = fail-closed / LATER (non-blocking for Letters Oracal path)

## POST_V1 backlog (concise)

1. Release / push / deploy Owner decision  
2. Logo sold-root / ACM treatments / cassette (separate product GOs)  
3. Capacity activation (Owner Option D)  
4. Phase E + PAUSE/RESUME  
5. Machine/other monetary cost if Owner INCLUDE  
6. Postgres / multi-tenant / cloud (if ever authorized)

## Evidence references

- `docs/operations/WORKOS_V1_PRODUCTION_RUNBOOK.md`
- `docs/qa/workos-v1-production-readiness-smoke-pack/`
- `docs/qa/workos-v1-bounded-ui-honesty-closures/`
- `docs/qa/workos-v1-exit-verification/`
- Prior domain packs (commercial, security, material, profitability Policy A)

## Owner reply required (exact)

```text
WORKOS_V1_PRODUCT_SET = LETTERS_ONLY
LOGO_SOLD_ROOT_V1 = LATER
ACM_EXPANSION_V1 = LATER
```

After those lines: update this record to `FINALIZED_FOR_AGREED_SCOPE` — no further feature build required.
