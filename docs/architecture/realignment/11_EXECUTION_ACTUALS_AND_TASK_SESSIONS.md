# ExecutionActuals & Task Sessions

**Version:** 1.0.1  
**Status:** Target architecture + **runtime boundaries VALIDATED** (2026-06-30)  
**Services (read context):** `execution_reality_service.py`, employee mobile tasks  
**Model:** `execution_reality.py`  
**Step:** 9 hardening — **PARTIAL**; reality/session boundary **VALIDATED**

---

## 1. Rolul sistemului

ExecutionActuals colectează **realitatea producției** după acceptare/comandă: task start/stop, angajat, durată reală, materiale reale, observații, blocaje, diferențe față de estimare.

**Regulă:** **Minutele reale se colectează aici.** Minutele sunt pentru statistică, capacitate și analiză post-job — **nu** pentru preț comercial client.

---

## 2. Ce detine

| Categorie | Conținut |
|-----------|----------|
| **Task start / stop** | Session timestamps |
| **Angajat** | Who performed work |
| **Durata reala** | total_actual_time_minutes per task/order |
| **Materiale reale** | Issues, consumption observations |
| **Observații** | Operator notes, blockers |
| **Blocaje** | Downtime, defects |
| **Diferențe vs estimare** | Plan vs actual time/material |
| **execution_reality records** | Aggregated actuals |
| **Machine/workcenter context** | Where work happened |

---

## 3. Ce NU detine

| Exclus |
|--------|
| Preț comercial initial / oferta client |
| Modificare retroactivă quote-ului acceptat |
| CommercialPriceProposal |
| EstimatedInternalCost (upstream estimate) |
| Generare ExecutionPlan (upstream) |
| HR payroll calculation (separate boundary) |
| Client billing recalculation |

---

## 4. Inputuri

| Sursă | Date |
|-------|------|
| ExecutionPlan | Task list baseline |
| Employee Mobile | Task sessions start/stop |
| Operator / Tablet UI | Manual start/stop |
| Material issues | Inventory consumption events |
| Attendance (where relevant) | Cross-check availability |

**API (existing context):**

- `POST /api/v1/execution/reality/start-task`
- `POST /api/v1/execution/reality/end-task`

---

## 5. Outputuri

| Output | Consumator |
|--------|------------|
| Actual minutes per task | ProfitabilityAnalysis |
| Actual material usage | ProfitabilityAnalysis, inventory |
| Plan vs actual variance | Production lead dashboards |
| Capacity statistics | Scheduling, analytics |
| Learning signals | Future commercial rule tuning (recommendations only) |

---

## 6. Source of truth

| Aspect | Status |
|--------|--------|
| Real production time | **Source of truth** (post-order) |
| Real material consumption | **Source of truth** (where captured) |
| Commercial price | **NOT** — frozen in Order |
| Estimated minutes pre-job | ExecutionPlan / internal — **not** this |

**Audit status:** **GOOD foundation** — correct place for real minutes.

---

## 7. Conexiuni cu celelalte sisteme

```
Order → ExecutionPlan
    ↓
ExecutionActuals (THIS) ← Employee Mobile / Operator sessions
    ↓
ProfitabilityAnalysis (quoted vs estimated vs actual)
    ↓
Recommendations for FUTURE CommercialPriceProposal rules — NOT retroactive quote change
```

| Sistem | Relație |
|--------|---------|
| HR/Pontaj | Employee identity — cost for internal analysis only |
| Inventory | Material deductions — not quote price source |
| Quote/Order | Read-only commercial baseline for comparison |
| Cost Engine | **NO** feedback loop to change accepted price |

---

## 8. Reguli owner obligatorii

1. Real minutes **never** become client invoice formula retroactively.
2. Post-job: verify if mp/ml/buc/set commercial rule was economically correct.
3. Protected foundation — preserve execution_reality paths (audit acceptance).
4. Sessions must link order_id ↔ plan task ↔ employee.
5. Actuals closed before full ProfitabilityAnalysis — **UNKNOWN** exact gate policy.

---

## 9. Riscuri actuale din audit

| Risc | Detaliu | Tag |
|------|---------|-----|
| Hardening needed | order ↔ reality ↔ mobile linkage | Step 9 |
| Minutes could be misread | If UI conflates with commercial | `MISLEADING_UI` risk |
| Partial material capture | **UNKNOWN** completeness | `NEEDS_OWNER_DECISION` |
| Pre-quote minute estimates | Confused with actuals | Separation docs |

---

## 10. Target state (Step 9)

| Aspect | Țintă |
|--------|-------|
| Clear session model | Every task has start/stop or explicit skip reason |
| Order linkage | Mandatory order_id on production sessions |
| Material observations | Structured variance vs estimate |
| UI labels | „Timp real producție” — not „preț” |
| No quote mutation | Enforced at API + governance |

### Runtime — ExecutionReality / session boundary (VALIDATED 2026-06-30)

**Status:** **VALIDATED**. Full Step 9 hardening still **NEEDS OWNER GO**.

| Rule | Runtime behavior |
|------|------------------|
| ExecutionReality starts | Only at `POST /api/v1/execution/reality/start-task` — not at plan materialize |
| `start-task` / `end-task` | Runtime reality — **not** plan creation |
| Materialize | Does **not** start tasks; does **not** create sessions |
| Actual minutes | Do **not** modify accepted quote or `accepted_commercial_total` |
| DivergenceService | `GET /api/v1/execution/divergence/{order_id}` — **read-only**; `has_reality=false` when no reality |
| QA fixture | Order `88001` — plan ready, reality absent — expected for pre-start state |

**Worklogs:** `2026-06-30_step_9_3_6_operational_reality_review_audit.md`, `2026-06-30_step_10_actuals_profitability_hardening_audit.md`

---

## 11. Forbidden behavior

| Interzis |
|----------|
| Actuals modify accepted commercial_price |
| Actuals feed back into /price for same quote |
| Use actual minutes as CommercialPriceProposal formula |
| Collect actuals before order acceptance (as truth) |
| Silent session without plan task reference |
| Materialize creates ExecutionReality or sessions | **Forbidden** — validated |
| Actual minutes modify accepted commercial total | **Forbidden** — policy + Slice 10.1 guard |

---

## 12. Acceptance criteria

| Criteriu | OK când |
|----------|---------|
| Session → plan task | Traceable |
| Actual minutes aggregated | execution_reality totals |
| Quote unchanged post-actuals | Policy test |
| ProfitabilityAnalysis input ready | Step 10 read-only GET **VALIDATED** (10.2+10.3) |
| UI not misleading | Step 11 labels |
