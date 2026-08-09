# WorkOS — V1 Profitability Currency Composition Authority

**Date:** 2026-08-09  
**Starting HEAD:** `90b26264`  
**Branch:** `feat/f7i-owner-rate-activation`  
**Owner GO:** `AUTHORIZE_WORKOS_V1_PROFITABILITY_CURRENCY_COMPOSITION_AUTHORITY`  
**Product code:** **0** (decision prep only)

---

## Verdict

```text
WORKOS_V1_PROFITABILITY_CURRENCY_COMPOSITION_AUTHORITY = PASS_DECISION_PREP
OWNER_DECISION_REQUIRED = YES
HISTORICAL_FX_AUTHORITY = MISSING
COMPANY_BASE_CURRENCY_AUTHORITY = MISSING
PRODUCT_CODE_CHANGES = 0
ORDER_SNAPSHOT_MUTATIONS = 0
LABOR_COST_MUTATIONS = 0
MATERIAL_COST_MUTATIONS = 0
DB_SCHEMA_CHANGES = 0
QA_MUTATIONS = 0
NEXT_TASK = WAIT_FOR_OWNER_DECISION
```

---

## Current currency facts

| Input | Currency | Authority |
|-------|----------|-----------|
| Letters revenue | **EUR** | `OrderSnapshotV2.accepted_currency` + `accepted_commercial_total` (frozen; no FX at convert) |
| Labor actual | **RON** (typical) | `ActualLaborCostLine.currency` ← policy (default RON) |
| Material actual | **RON** (typical) | `StockMovement.currency_snapshot` |
| Same-currency composition | Working | Profitability RM |
| EUR − RON | Blocked | `currency_mismatch_no_fx` (correct) |
| Machine / Other | N/A_FOR_V1 | unchanged |

Commercial offer EUR remains **DONE_FOR_V1** — not reopened.

---

## Authority inventory (condensed)

| Authority | Role | Historical-safe? | Class |
|-----------|------|------------------|-------|
| Order Snapshot V2 accepted EUR\|RON | Revenue | Yes (frozen JSON) | CANONICAL commercial |
| Order Snapshot V2 convert (no live FX) | Commercial law | N/A | CANONICAL |
| `company_commercial_settings.eur_to_ron_rate` | Live EUR→RON | **No** (no rate_date / history) | LIVE_MUTABLE |
| Legacy `commercial_currency_handoff.exchange_rate_eur_ron` | Old Quote→RON order base | Partial (frozen on that path; **not** wired to Profitability / not V2) | COMMERCIAL_ONLY |
| CPP / registry line conversion stamps | Quote-time | Partial | COMMERCIAL_ONLY |
| CostEngine `moneda_implicita` | Costing base | No | PARTIAL / wrong layer |
| Labor / material currency fields | Actual cost truth | Yes (amount currency; **no FX**) | CANONICAL actual |
| Profitability historical FX ledger | Composition | — | **MISSING** |
| Company / accounting base currency | Unified P&L | — | **MISSING** |

No governance doc already picks a Profitability composition FX policy.

---

## Options (realistic only)

### A — Costs RON → EUR (historical FX)

- Revenue stays frozen EUR (commercial truth untouched).
- Aggregate known actual costs (RON) → EUR via **one frozen Order-level rate**.
- Composition in EUR inside Profitability RM only.
- **Feasibility:** HIGH · **Scope:** SMALL–MEDIUM · **Table schema:** none (additive snapshot JSON) · **Historical safety:** YES if rate frozen at convert, never re-read live · **Complexity:** SMALL

### B — Revenue EUR → RON (historical FX)

- Commercial Snapshot EUR total **not mutated**; Profitability derives RON reporting revenue.
- Compose in RON against native labor/material.
- Aligns with legacy `BASE_CURRENCY_DEFAULT=RON` handoff pattern, but that pattern is **not** V2 Profitability authority today.
- **Feasibility:** HIGH · **Scope:** SMALL–MEDIUM · same freeze needs · **Complexity:** SMALL

### C — Explicit Profitability reporting currency

- Introduce `PROFITABILITY_REPORTING_CURRENCY` + normalize both sides.
- Cleaner name; same FX freeze need as A/B; risk of mini multi-currency framework.
- **Feasibility:** MEDIUM · **Scope:** MEDIUM · **Complexity:** MEDIUM — avoid unless Owner wants the named concept.

### D — Change Letters commercial to RON

- Avoids FX by reopening **DONE_FOR_V1** commercial domain + historical offer law.
- **Rejected for V1** unless Owner forces — high impact, not simpler overall.

**Live internet / today’s Settings rate at view time / hardcoded FX:** forbidden.

---

## Historical FX freeze

| Question | Finding |
|----------|---------|
| HISTORICAL_FX_AUTHORITY | **MISSING** (nothing Profitability can safely consume today) |
| Closest live source | Settings `eur_to_ron_rate` — usable only if **snapshotted** into Order at convert |
| Closest frozen legacy | `commercial_currency_handoff` — wrong path for Order Snapshot V2 Letters |
| Recommended freeze point (if Owner picks FX) | **Order Snapshot V2 convert** — one rate per Order |
| Storage (no Alembic) | Additive keys on `Orders.snapshot_v2_json` (e.g. profitability FX stamp); RM reads stamp only |
| Per-event FX (Day1 material / Day5 labor) | Not required for V1; Order-level rate is the practical tradeoff |

### Conceptual stability check (policy candidate)

```text
Revenue: 1000 EUR (frozen)
Labor:   1000 RON
Material: 500 RON
FX frozen at Order convert: 5.0 RON/EUR  (example fixture only)

Option A: costs = 1500/5 = 300 EUR → contribution = 700 EUR
Change Settings live rate to 6.0 → historical contribution MUST stay 700 EUR
```

If live Settings is read at P&L view → **policy fails**.

---

## Schema impact

```text
SCHEMA_CHANGE_REQUIRED (tables/Alembic) = NO
SNAPSHOT_CONTRACT_EXTENSION (additive JSON) = YES for chosen FX policy
LABOR / MATERIAL typed FX columns = NOT needed if Order-level freeze + RM normalize
ORDER_SNAPSHOT commercial totals rewrite = FORBIDDEN (0)
```

---

## Composition owner

Normalization belongs in **Profitability composition / read model** — not Quote, Session, or Inventory side effects.

Preserve: Machine / Other = `N_A_FOR_V1` (never numeric 0).

---

## Agent recommendation

```text
AGENT_RECOMMENDED_CURRENCY_POLICY = A
PROFITABILITY_REPORTING_CURRENCY = EUR
FX_RATE_AUTHORITY = company_commercial_settings.eur_to_ron_rate SNAPSHOTTED at Order Snapshot V2 convert
FX_FREEZE_POINT = ORDER_CONVERT
FX_STORAGE = additive Order Snapshot V2 JSON (not live Settings at view)
```

Reasons (≤6):

1. Keeps DONE Letters commercial EUR as the contribution language.  
2. Does not invent a missing company/accounting base currency.  
3. One Order-level freeze; one conversion of aggregated known RON costs.  
4. Upstream labor/material/commercial amounts stay immutable.  
5. Reuses existing Settings rate **only as snapshot source**, not live authority.  
6. Smallest honest V1 path back to composition PASS.

---

## OWNER DECISION CARD — PROFITABILITY CURRENCY

```text
OWNER DECISION — PROFITABILITY CURRENCY COMPOSITION V1

[A] Costs RON → EUR using historical FX frozen at Order convert
    (Agent recommendation)
[B] Revenue EUR → RON (derived reporting only) using same freeze
[C] Named Profitability reporting currency (same FX need; more surface)
[D] Reopen Letters commercial currency (NOT recommended)

Agent recommendation: A
Historical freeze: Order Snapshot V2 convert — stamp Settings eur_to_ron_rate once
Implementation scope after decision: SMALL
Schema tables: 0 · Snapshot JSON additive: YES
Product code this GO: 0

Reply example:
PROFITABILITY_CURRENCY_POLICY = A
```

After Owner answer → separate bounded GO: wire stamp + RM normalize + tests → then return to `PROFITABILITY_MONETARY_COMPOSITION_V1` for final PASS.

---

## UI

Current fail-closed UI (contribution unavailable / currency mismatch) is honest. No UI work in this GO.

---

## Roadmap impact

- Do not lower V1 % because fail-closed is correct.  
- Single explicit Owner blocker remains: this decision.  
- No new Profitability subtopics.  
- Next after Owner: bounded wire → composition PASS → UI honesty / production readiness / exit.
