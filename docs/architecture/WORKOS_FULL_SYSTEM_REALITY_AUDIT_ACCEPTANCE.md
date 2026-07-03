# WorkOS Full System Reality Audit — Acceptance & Runtime Freeze Contract

**Version:** 1.0.0  
**Status:** Accepted (Step 7F.1 — documentation only, no runtime change)  
**Date:** 2026-06-07  
**Repo:** `C:\Users\offic\Desktop\workos-active`  
**Supersedes nothing in code** — binds future work only.

**Related documents:**
- `docs/audits/WORKOS_FULL_SYSTEM_REALITY_AUDIT.md` (Full System Reality Audit)
- `docs/architecture/WORKOS_COMMERCIAL_PRICING_VS_INTERNAL_COST_CONTRACT.md` (Step 7F cost philosophy contract)

---

## 1. Audit accepted

### Verdict

**`HIGH_RISK_DEVIATED`** — accepted as accurate description of WorkOS as of the Full System Reality Audit (2026-06-07).

### What we accept

| Finding | Acceptance |
|---------|------------|
| **Commercial pricing runtime is deviated** | **Accepted.** `/price` mixes internal cost and commercial price; `QuoteOrchestrator._apply_commercial` applies `total_cost × margin`; Cost Engine defaults to `per_hour`; Pricing Registry conflates material costs, workcenter rates, markup, and quote calculation; `CommercialPriceProposal` and `ProfitabilityAnalysis` do not exist as runtime models. |
| **Product and execution foundations are good** | **Accepted.** Intake V6 is coherent as product truth; ProductDefinition / ProductAggregate are the correct technical direction; ExecutionActuals (task start/stop, reality capture) are the correct place for real minutes; HR/Pontaj are internal and must not drive commercial client price. |

### Implication

Until realignment steps **7G–12** are executed with **explicit owner GO**, the **dangerous paths listed in §3 remain frozen** — no ad-hoc fixes, no “quick reprice,” no registry edits presented as commercial policy.

---

## 2. Protected foundations

These areas are **protected**. Future work must **preserve** them as sources of truth; do not redesign, rewrite, or bypass without owner decision.

| Foundation | Role | Protected artifact / path |
|------------|------|---------------------------|
| **Intake V6** | Product truth | Workspace payload: geometry, materials, finishes, LED, mounting, module activation; operator flow frozen (no layout/flow redesign) |
| **ProductDefinition** | Canonical product structure | `GET /api/v1/product-system/product-definition/{template_code}`; builder service |
| **ProductAggregate** | Technical expanded BOM | `GET /api/v1/product-system/aggregate/{template_code}`; Aggregate Cost BOM preview (read-only truth, Step 7D) |
| **ExecutionReality / task sessions** | Actual runtime truth | `POST /api/v1/execution/reality/start-task`, `end-task`; operator / tablet / employee-mobile sessions; real minutes post-order |
| **HR / Pontaj** | Internal people truth | Employees, attendance, payments, advances — analytics and payroll-adjacent only; **not** commercial price input |
| **Material Registry** | Material acquisition cost truth | `inventory_materials.unit_cost` (+ admin PATCH) — internal material cost for estimation; **not** client-facing commercial rule by itself |

**Rule:** Changes to protected foundations require **owner GO** and must not be bundled with commercial pricing fixes unless explicitly scoped.

---

## 3. Frozen dangerous paths

The following are marked **`FROZEN_UNTIL_REALIGNED`**.  
**No code changes** to these paths in Step 7F.1 or without owner GO + aligned step (7G+).

| Path / surface | Why frozen | Risk if touched ad-hoc |
|----------------|------------|-------------------------|
| `POST /api/v1/entities/quotes/price` | Mixes internal cost + commercial price in one write | Reprice drift, false “fixed” quotes |
| `POST /api/v1/entities/quotes/{id}/price` | In-place reprice; same mixed model | Quote 4 / production quotes corrupted |
| `QuoteOrchestrator._apply_commercial` | `total_cost × margin` as client price | Reinforces cost-plus philosophy |
| **Cost Engine `per_hour` path** | `estimated_minutes → hours × rate_per_hour → operation_cost → quote` | Commercial hourly pricing |
| **`workcenter_rates` as quote/commercial source** | Missing `rate_per_hour` blocks readiness; UI reads as client tariff | “Cannot offer” conflated with internal cost gap |
| **Pricing Registry as unified quote calculation hub** | Single view: materials + WC rates + markup | Cannot separate commercial vs internal |
| **Intake V6 live offer as official quote** | `intakeV6OfferCalculator`: internal buckets + markup + TVA | Operator treats preview as client offer |
| **Settings → CostEngine hourly fallback** | v1 `labour_rate_ron_per_hour` / `machine_rate_ron_per_hour` (e.g. 80/40 RON/h) | Silent hourly commercial path |
| **Markup policies as universal commercial model** | Margin applied to internal cost total | Cost-plus as only commercial rule |

**Documentation-only status:** This section **does not** disable endpoints, feature-flag code, or alter runtime behavior. It **freezes team intent**: no implementation on these paths until **7G → 7H → 8** (and owner GO per step).

**Explicitly frozen operations (owner hold):**
- Reprice **quote 4**
- Apply **Step 7E.2** payload repair
- **Pricing Registry data edits** for “readiness” without commercial rule design
- **Cost Engine / QuoteOrchestrator rewrite** outside scoped steps

---

## 4. Owner pricing law

Binding for all future WorkOS commercial work:

1. **No commercial hourly pricing** — P-Media does not quote clients “ore × tarif.”
2. **No `per_hour` commercial basis** — `rate_per_hour` and minute-derived hours are **not** the primary client price formula.
3. **No missing `rate_per_hour` blocker for commercial offer** — absence of internal hourly rate may affect **EstimatedInternalCost completeness / margin confidence**, not necessarily the ability to propose a commercial price (mp/ml/buc/set/minim/complexitate).
4. **No `total_internal_cost × margin` as universal final price** — commercial price comes from **product/solution rules**, not a single cost-plus transform on one internal total.
5. **Time belongs only to ExecutionActuals / analytics / post-job profitability** — task start/stop, real duration, capacity, statistics, and **ProfitabilityAnalysis** (after execution) verify whether per-unit commercial rules (lei/m², lei/ml, etc.) were economically correct.

### Owner examples (reference)

| Zone | Commercial basis |
|------|------------------|
| CNC | lei/ml by material + thickness + bevel (sanfren) |
| Cant aluminiu | lei/ml |
| Vopsire / finisaj | lei/m² or minim lucrare |
| LED | lei/modul, lei/set, or package |
| Client offer | **Never** “100 ore × tarif” |

---

## 5. Correct source-of-truth map

```
┌─────────────────────────────────────────────────────────────────┐
│ PRODUCT TRUTH                                                    │
│   Intake V6 workspace → ProductDefinition → ProductAggregate     │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ MATERIAL TRUTH (acquisition / unit cost)                         │
│   inventory_materials (+ admin unit_cost)                        │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ COMMERCIAL PRICE TRUTH — TARGET (not runtime today)              │
│   CommercialPriceProposal — mp/ml/buc/literă/set/minim/         │
│   complexitate/urgentă/valoare comercială                        │
│   ❌ Today wrongly aliased: QuotePrice.final from cost_plus      │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ ESTIMATED INTERNAL COST TRUTH — PARTIAL (mixed in /price today)  │
│   Aggregate Cost BOM + Cost Engine (non-hourly target)           │
│   Materials + consumables + internal operation rules + overhead  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ EXECUTION ACTUALS TRUTH                                          │
│   execution_reality, task sessions, operator/mobile timestamps   │
│   Real minutes, materials, employees — post acceptance/order     │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ HR TRUTH                                                         │
│   employees, attendance, payments, advances                      │
│   Internal only — not commercial price input                     │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ PROFITABILITY TRUTH — TARGET (not implemented)                   │
│   ProfitabilityAnalysis: quoted vs estimated vs actual           │
│   Recommendations for future rules — no retroactive quote change │
└─────────────────────────────────────────────────────────────────┘
```

**Guardrail:** No layer may silently substitute another (e.g. execution minutes → quote price; material unit_cost → client mp price without commercial rule).

---

## 6. Step sequence accepted

Future realignment proceeds **in order**; each step requires **owner GO** before implementation.

| Step | Name | Scope (accepted) |
|------|------|------------------|
| **7F** | Cost philosophy contract | Done — `WORKOS_COMMERCIAL_PRICING_VS_INTERNAL_COST_CONTRACT.md` |
| **7F.1** | Audit acceptance + runtime freeze | **This document** |
| **7G** | `CommercialPriceProposal` read-only prototype | Schema + preview; **no `/price` change** |
| **7H** | `EstimatedInternalCost` separation, non-hourly | Decouple from commercial; retag gates |
| **7I** | Pricing Registry separation and labels | Internal cost rules vs commercial rules UI/copy |
| **8** | Quote snapshot | `commercial_price` + `estimated_internal_cost` side by side |
| **9** | ExecutionActuals hardening | Link sessions to orders; strengthen capture |
| **10** | ProfitabilityAnalysis | Post-job compare + recommendations |
| **11** | UI cleanup / deprecation labels | Mock pages, Pricing copy, legacy intake labels |
| **12** | Dead pieces cleanup | intake v3/v5, legacy flows — after owner review |

**On hold until separate GO:** Step 7E.2 apply (quote 4 payload repair), quote 4 reprice, any Pricing Registry edits for WC_ASSEMBLY “readiness.”

---

## 7. What NOT to do now

- No **quote 4 reprice**
- No **7E.2 apply**
- No **`/price` changes**
- No **Pricing Registry data edits**
- No **Cost Engine rewrite**
- No **QuoteOrchestrator rewrite**
- No **UI redesign**
- No **Intake V6 rewrite**
- No **DB reset / reseed**
- No **seed or migration runs**
- No **order / execution_plan / real task creation** for audit/fix experiments

---

## 8. Required guard for all future prompts

Copy into future WorkOS implementation prompts until owner revokes:

```
OWNER DECISION GUARD:
Doar ownerul decide daca modificam ceva sau nu.
Nu implementa modificari fara GO explicit de la owner.

NO-HOURLY-COMMERCIAL GUARD:
Nimic in WorkOS nu se calculeaza comercial la ora.
Orele/minutele sunt doar ExecutionActuals / analytics / post-job profitability.

SOURCE OF TRUTH GUARD:
Intake V6 = produs.
ProductAggregate = structura tehnica.
CommercialPriceProposal = pret comercial.
EstimatedInternalCost = cost intern non-hourly.
ExecutionActuals = realitate productie.
ProfitabilityAnalysis = analiza dupa executie.
```

Additional freeze reminder for agents:

```
RUNTIME FREEZE (7F.1):
Paths in WORKOS_FULL_SYSTEM_REALITY_AUDIT_ACCEPTANCE.md §3 are FROZEN_UNTIL_REALIGNED.
Do not modify POST .../quotes/price, QuoteOrchestrator._apply_commercial, Cost Engine per_hour
commercial use, or Pricing Registry as unified quote hub without owner GO and aligned step (7G+).
```

---

## 9. No-side-effects confirmation

| Check | Step 7F.1 status |
|-------|------------------|
| DB writes | **None** |
| Seed / migration | **None** |
| POST `/price` | **Not called** |
| Quote 4 reprice | **Not done** |
| Order / execution_plan / tasks | **Not created** |
| UI changes | **None** |
| Backend / frontend code changes | **None** |
| Pricing Registry data edits | **None** |
| Runtime behavior | **Unchanged** |
| Deliverable | **Only this documentation file** |

---

## 10. Roadmap awareness

| # | Criterion | Score /10 | Notes |
|---|-----------|-----------|-------|
| 1 | Audit accepted honestly | 10 | HIGH_RISK_DEVIATED acknowledged |
| 2 | Protected foundations documented | 10 | Intake V6, Aggregate, Execution, HR, materials |
| 3 | Dangerous paths frozen (intent) | 10 | §3 list; no code freeze mechanism |
| 4 | Owner pricing law explicit | 10 | §4 |
| 5 | Source-of-truth map | 10 | §5 |
| 6 | Step sequence 7G–12 accepted | 10 | §6 |
| 7 | Guards for future prompts | 10 | §8 |
| 8 | No accidental implementation | 10 | Doc-only step |
| 9 | Runtime still deviated (honesty) | 6 | Acceptance ≠ fix |
| 10 | Path to 7G clear | 9 | Next step defined |

### **Cat sunt in directia stabilita: 95/100**

**−5%:** Runtime remains deviated until 7G+; freeze is **documentary**, not enforced in code (by design for 7F.1).

---

**Document owner:** WorkOS architecture  
**Next action (requires owner GO):** Step **7G** — CommercialPriceProposal read-only prototype  
**Runtime status:** UNCHANGED
