# WorkOS — Profitability V1 Machine + Other Direct Cost Owner Decision Prep

**Date:** 2026-08-09  
**Owner GO:** `AUTHORIZE_PROFITABILITY_V1_MACHINE_OTHER_COST_DECISION_PREP`  
**Starting HEAD:** `23b1ed39`  
**Branch:** `feat/f7i-owner-rate-activation`  
**Product code changes:** `0`  
**QA mutations:** `0`  
**Verdict:** `PASS` (decision prep only — Owner still decides)

```text
PROFITABILITY_V1_MACHINE_OTHER_COST_DECISION_PREP = PASS
OWNER_DECISION_REQUIRED = YES
NEXT_TASK = WAIT_FOR_OWNER_DECISION
```

---

## Baseline (confirmed)

| Claim | Status |
|-------|--------|
| COMMERCIAL / revenue | READY |
| Actual labor cost input | READY |
| Actual material cost input | READY |
| Profitability monetary calculation | NOT_STARTED |
| WORKOS_V1_COMPLETION_ESTIMATE | ≈ 85% |

---

## D. Machine runtime readiness

```text
MACHINE_RUNTIME_INPUT_READINESS = PARTIAL
```

**Have:** MachineRun `machine_id`, START/COMPLETE stamps, participants (`order_id` / plan / `task_key`), derived runtime from timestamps.  
**Missing for cost:** RM does not consume MachineRun; duration not a frozen cost ledger; multi-participant allocation undefined; PAUSE/RESUME deferred.

---

## E–F. Machine rate authority / historical stability

```text
MACHINE_COST_RATE_AUTHORITY = MISSING
MACHINE_RATE_HISTORICAL_STABILITY = MISSING
```

| Candidate | Class | Usable as ACTUAL? |
|-----------|-------|-------------------|
| Dated machine cost policy / ActualMachineCostLine | NOT_PRESENT | No |
| Workcenter `rate_per_hour` | LIVE / CostEngine estimate | No (RM forbids fallback) |
| F7I / commercial registry machine-ish rates | COMMERCIAL | No |
| Machine registry | Identity only | No rates |

If a commercial/WC rate changed tomorrow, there is **no** frozen ACTUAL machine cost line to protect yesterday’s job.

---

## G–H. Machine options

### [A] INCLUDE_IN_V1

Requirements: consume COMPLETED MachineRuns → dated ACTUAL rate authority → freeze cost lines → allocation rules → RM composition + tests.  
Scope: **LARGE** · Schema: **REQUIRED** · Risk: high (wrong rate domain / silent reprice if rushed).

### [B] DECLARE_NA_FOR_V1

MachineRun stays operational truth. Profitability keeps explicit non-zero honesty:

- `machine_cost_status` / `applicability` = N/A or not-captured reasons  
- `value: null`, `available: false` — **never silent 0**

Monetary V1 = revenue − labor − material only for Letters.

---

## I. Machine recommendation (agent only)

```text
MACHINE_COST_V1_RECOMMENDATION = DECLARE_NA_FOR_V1
```

1. Runtime exists; ACTUAL rate + freeze do not.  
2. F7I/WC candidates are commercial/mutable — wrong domain.  
3. INCLUDE is a LARGE cost-domain build, not a composition tweak.  
4. RM already fail-closes machine without inventing 0.  
5. Roadmap already allows Owner N/A → LATER for Letters.

---

## J–K. Other direct — definition and authority

**Current meaning (runtime):** hard-coded cost category `other_direct` / `other_actual_cost` with reason `other_direct_not_declared`, `applicability=not_applicable`, `value=null`. Explicitly **not** a free-form bucket.

```text
OTHER_DIRECT_COST_CURRENT_AUTHORITY = ACTIVE_PARTIAL
```

Read-model N/A contract is live; classified ledger/write path is **absent**. No subcontract/shipping/expense table wired as profitability actuals.

Fail-closed honesty: **N/A ≠ 0 ≠ unknown** already distinguished for other_direct (always N/A today).

---

## L–M. Other direct options

### [A] INCLUDE_IN_V1

New classified ledger (category, amount, currency, provenance, actor) + writers + RM consumption. Medium–large Finance GO.

### [B] DECLARE_NA_FOR_V1

Keep hard N/A for Letters V1; ledger LATER. No silent zero.

---

## N. Other-direct recommendation (agent only)

```text
OTHER_DIRECT_COST_V1_RECOMMENDATION = DECLARE_NA_FOR_V1
```

1. Only honest N/A exists; INCLUDE needs a new domain.  
2. Letters pilot can show useful P&L with revenue + labor + material.  
3. Roadmap already frames other as CONDITIONAL / Owner N/A.  
4. Do not block V1 exit for perfect accounting completeness.  
5. Preserve `other_direct_not_declared` honesty in UI.

---

## O–Q. Profitability composition impact

Conceptual V1 after Owner N/A on both:

```text
profitability_v1 =
  accepted_revenue
  − actual_labor_cost
  − actual_material_cost
  # machine_actual    → N/A_FOR_V1 (not 0)
  # other_direct      → N/A_FOR_V1 (not 0)
```

```text
PROFITABILITY_V1_WITH_NA_COST_CATEGORIES = ACCEPTABLE
```

Reason: labor + material + revenue are READY; RM already excludes N/A categories from inventing zeros and from blocking `complete_actuals` when applicability is `not_applicable`.

If Owner chooses INCLUDE for either category and scope is LARGE → separate prerequisite build before / alongside monetary composition.

---

## R. OWNER DECISION CARD

### OWNER DECISION 1 — MACHINE COST

- **[A] INCLUDE_IN_V1**  
- **[B] DECLARE_NA_FOR_V1**  

Agent recommendation: **B**  
Impact B: next build = `PROFITABILITY_MONETARY_COMPOSITION_V1` with machine explicitly N/A.  
Impact A: LARGE schema + rate freeze program before honest monetary machine lines.

### OWNER DECISION 2 — OTHER DIRECT COST

- **[A] INCLUDE_IN_V1**  
- **[B] DECLARE_NA_FOR_V1**  

Agent recommendation: **B**  
Impact B: composition uses revenue/labor/material; other stays `other_direct_not_declared`.  
Impact A: new classified ledger GO before/with monetary composition.

---

## After Owner answers

| Owner choice | Next |
|--------------|------|
| Machine=B and Other=B | `PROFITABILITY_MONETARY_COMPOSITION_V1` immediately |
| Either = A (small if somehow bounded) | Only if cleanly owned inside composition — unlikely; expect separate LARGE/MEDIUM build |
| Either = A (major) | Separate domain build; do not pretend composition alone fixes rates/ledger |

---

## Roadmap status (not finalized)

```text
MACHINE_COST_V1 = OWNER_DECISION_PENDING
OTHER_DIRECT_COST_V1 = OWNER_DECISION_PENDING
CRITICAL_PATH_UNCHANGED_UNTIL_OWNER_ANSWER = YES
```
