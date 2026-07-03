# WorkOS Commercial Pricing vs Internal Cost vs Runtime Actuals

**Version:** 1.0.0  
**Status:** Architectural contract (Step 7F — design only, no runtime change)  
**Scope:** WorkOS pricing philosophy realignment — P-Media internal production  
**Pilot product:** `TPL-VOLUMETRIC-LETTERS_v2`  
**Related audits:** Cost Philosophy Realignment Audit (2026-06-30) — `HIGH_RISK_MINUTES_AS_PRICE`

---

## 1. Verdict and current problem

### Verdict

WorkOS today carries **HIGH_RISK_MINUTES_AS_PRICE** in the **canonical quote path**, even though parts of the product stack (Intake V6, unit-based costing notes, task runtime) already point in the owner direction.

### Why the risk exists

| Layer | Current behavior | Philosophy conflict |
|-------|------------------|---------------------|
| **QuoteOrchestrator** | `final_price = f(total_internal_cost, margin, discount, VAT)` | Commercial price is **cost-plus** on a single internal total |
| **Cost Engine v2 (default)** | Operations: `estimated_minutes → hours × rate_per_hour` | Minutes × hourly rate becomes **operation_cost → total_cost → quote price** |
| **Pricing Registry** | `workcenter_rates.rate_per_hour` documented as “source of truth” | Registry reads as **client hourly tariff** |
| **Aggregate Cost BOM (7B+)** | `pricing_source_required: workcenter_rates`; missing WC rate → **blocked** | Missing internal labor rule **blocks quote**, not just margin confidence |
| **Formula registry** | Time formulas (`perimeter_based_time`, `led_assembly_time`) feed minute path | Time becomes **mandatory cost input**, not optional sanity |
| **Step 7E blockers** | `WC_ASSEMBLY_rate_missing` → NOT_READY reprice | Owner interprets: **no hourly rate = cannot offer** |

### What remains good (keep)

| Asset | Role | Status |
|-------|------|--------|
| **Intake V6** | Product, geometry, materials, finishes, LED, mounting, module activation | **Source of truth for product** — do not redesign |
| **ProductDefinition (Step 6)** | Canonical product structure from workspace | **Keep** |
| **ProductAggregate (Step 7A)** | Expanded technical BOM | **Keep** |
| **Aggregate Cost BOM (Step 7B/7B.1)** | Readiness, blockers, inventory alignment | **Keep** — reclassify blockers (see §5) |
| **QuoteOrchestrator v2_aggregate path (Step 7C)** | Aggregate-expanded internal cost | **Keep engine path** — decouple from commercial price |
| **Task runtime / execution_reality** | Start/stop, actual minutes | **Correct role** — post-job only |
| **Owner costing notes** (`TPL_VOLUMETRIC_LETTERS_COSTING_LOGIC_AUDIT.md`) | Many ops already **per ml / per piece / per m²** | **Align runtime to this intent** in future steps |

### Owner principle (binding for future work)

> P-Media **does not** quote clients “100 hours × hourly rate”.  
> P-Media quotes **products / jobs / solutions**: e.g. vopsire **X lei/m²**, litere volumetrice **X lei/literă / m² / ml / set / minim / complexitate**.  
> After execution, **real task minutes** verify whether the **per-unit commercial rule** was economically correct.

**Minutes are for:** internal verification, capacity, statistics, post-job analysis, future rule tuning — **not** the primary commercial price source.

---

## 2. Separation of the four models

```
Intake V6 (product truth)
    ↓
ProductDefinition + ProductAggregate
    ↓
┌─────────────────────────────┐     ┌─────────────────────────────┐
│  CommercialPriceProposal    │     │  EstimatedInternalCost      │
│  (what we offer client)     │     │  (what we think it costs)   │
│  mp/ml/buc/set/min/complex  │     │  materials + ops + overhead │
└──────────────┬──────────────┘     └──────────────┬──────────────┘
               │                                    │
               └──────────────┬─────────────────────┘
                              ↓
                    Quote snapshot (Step 8)
                    commercial_price + estimated_internal_cost
                              ↓
                         Order / Production
                              ↓
┌─────────────────────────────┐     ┌─────────────────────────────┐
│  ExecutionActuals           │ ──→ │  ProfitabilityAnalysis      │
│  task start/stop, materials │     │  quoted vs estimated vs     │
│  real duration, employee    │     │  actual; margin; recommend  │
└─────────────────────────────┘     └─────────────────────────────┘
```

Models are **logically separate**. They may share geometry keys from Intake V6 but must not collapse into one “total_cost → price” pipeline.

---

## 3. Model definitions

### A. CommercialPriceProposal

**What it is:** The price proposed to the client for a **product / solution**, not for our time.

| Aspect | Rule |
|--------|------|
| **Inputs** | ProductDefinition, geometry, active modules, market/complexity/urgency, owner commercial rules |
| **Formula families** | lei/m², lei/ml, lei/buc (literă), lei/set, minim lucrare, coeficient complexitate, urgenta |
| **NOT based on** | `minutes × rate_per_hour` as primary rule |
| **Margin** | Target margin / policy applied to **commercial base**, not necessarily identical to internal cost markup |
| **Output** | `commercial_lines[]`, `commercial_subtotal`, `commercial_total`, `currency`, `rule_provenance[]` |
| **Persistence** | Quote snapshot (Step 8) — frozen at offer time |
| **Mutability** | Owner-approved changes only before send; never retroactively changed by actuals |

**Example (vopsire):** “Vopsire cant: 45 lei/ml, minim 120 lei/lucrare” — **not** “2.5 h × 80 lei/h”.

### B. EstimatedInternalCost

**What it is:** Internal pre-production estimate for **margin confidence** and planning — not the client offer formula.

| Aspect | Rule |
|--------|------|
| **Inputs** | ProductAggregate / Aggregate Cost BOM, inventory unit costs, internal operation cost rules |
| **Includes** | Materials, consumables, scrap/waste factors, estimated operations, overhead |
| **Optional** | Estimated effort (minutes) as **sanity check / capacity warning** — does not auto-set commercial price |
| **Output** | `estimated_material_cost`, `estimated_operation_cost`, `estimated_total`, `completeness`, `warnings[]` |
| **Blockers** | Affect **internal cost completeness** and **margin confidence** — not necessarily commercial quote (see §5) |
| **Relationship to CE today** | Evolves from Cost Engine + Aggregate BOM — **renamed and gated separately** |

### C. ExecutionActuals

**What it is:** Production reality collected after acceptance.

| Aspect | Rule |
|--------|------|
| **Sources** | Employee mobile task start/stop, material issues/consumption, `execution_reality`, attendance where relevant |
| **Includes** | Real duration per task, employee, machine/workcenter, actual material qty |
| **Does NOT** | Change quoted commercial price retroactively |
| **Timing** | Order accepted → tasks executed → actuals closed |

**Existing hooks:** `employee_mobile_tasks_service` (sessions), `execution_reality.total_actual_time_minutes`, plan vs actual on execution_plan.

### D. ProfitabilityAnalysis

**What it is:** Post-job comparison and learning loop.

| Aspect | Rule |
|--------|------|
| **Compares** | `CommercialPriceProposal` vs `EstimatedInternalCost` vs `ExecutionActuals` |
| **Metrics** | Estimated margin, actual margin, time variance, material variance, per-unit effective price (lei/m² realized) |
| **Output** | Recommendations for **future** commercial rules — not automatic repricing of closed quotes |
| **Audience** | Owner, production lead, finance — not client-facing |

---

## 4. Formula contract — volumetric letters (`TPL-VOLUMETRIC-LETTERS_v2`)

For each zone: **commercial rule** (client), **internal cost rule** (estimate), **time/capacity check** (non-blocking for commercial), **runtime actual** (post-job).

| Zone | Commercial pricing rule (client) | Estimated internal cost rule | Time / capacity check | Runtime actual metric |
|------|----------------------------------|------------------------------|------------------------|------------------------|
| **debitare față** | lei/m² față sau lei/literă (policy); CNC inclus sau separat per ml tăiere | material m² × inventory cost + CNC ml × internal ml rate | min/ml estimat — **warning** if capacity tight | CNC task actual minutes, ml efectiv |
| **modelare cant** | lei/ml cant sau inclus în pachet literă | profil ml × material + forming ml × internal rate | min/ml — capacity calendar | profile forming task duration |
| **debitare spate** | lei/m² spate / pachet | backing material + CNC passes × ml rate | min — warning | back cut task actuals |
| **LED** | lei/modul, lei/set litere, sau pachet iluminat | module × unit cost + PSU + consumabile | assembly min estimate — **non-blocking** | `led_install_letters` task sessions |
| **asamblare** | inclus în preț/literă sau lei/set | consumabile + % overhead; **not** primary hours×rate | capacity load by set | assembly task actual minutes |
| **finisaje** (vopsire/RAL) | **lei/m²** sau **minim lucrare**; urgenta = coeficient | vopsea/consumabile + eventual subcontract hook (metadata) | optional QC time | painting/QC task actuals |
| **șablon montaj** | lei/m² template montaj (dacă activ) | bar material + prep; premount non-priced internal | prep time — internal only | premount prep (non-priced gate) |
| **ambalare** | fix/comandă sau lei/set | consumabile ambalare | min — warning | packaging task |
| **montaj** (șantier) | lei/vizită, lei/m², sau subcontract line | subcontract metadata / internal install allowance | crew-day capacity | field installation team `started_at`/`ended_at` |

**Out of commercial price (gates only):**

| Module | Role |
|--------|------|
| `geometry_svg` | Readiness gate — not priced |
| `electrica_logo` | Future reserved — not priced |
| `comp_flat_legacy` | Diagnostic only — not structural truth |

**Note:** Owner audit doc (`TPL_VOLUMETRIC_LETTERS_COSTING_LOGIC_AUDIT.md`) already lists **per ml / per piece / per m²** for many operations. Step 7G+ must make **CommercialPriceProposal** follow those units explicitly, while **EstimatedInternalCost** may reuse registry values as **internal unit costs**, not as “hourly client tariff”.

---

## 5. Blocking rules (new contract)

### Must block **commercial price** (quote cannot be sent as final offer)

- Missing **critical commercial pricing rule** for an active priced module/line
- Missing **critical geometry** (letter_count, face area, perimeter where rule requires it)
- Missing **critical material** or **material unit price** where commercial rule is material-linked
- Invalid product configuration (conflicting modules, incomplete finish groups when policy requires confirmation)
- ProductDefinition / Aggregate **structural** incomplete for priced scope

### Must **NOT** block commercial price solely because of

- Missing `rate_per_hour` on a workcenter
- Missing estimated minutes / time formula resolution
- Missing runtime actuals (pre-production)
- Missing internal labor cost rule used **only** for analytics
- HUB / externalization hooks (`selected_now=false`)
- Internal cost estimate incomplete **if** commercial rules are complete and owner accepts margin risk (explicit acknowledgement)

### May block **internal cost completeness** / **margin confidence** (warnings or owner gate)

- Missing internal operation cost rule (incl. legacy `WC_ASSEMBLY` internal rule)
- Missing estimated effort for capacity planning
- Missing employee/internal labor rate for profitability preview
- Large gap between commercial proposal and internal estimate (owner acknowledgement)

### Blocker severity mapping (migration target)

| Today (runtime) | Step 7F classification |
|-----------------|------------------------|
| `ERR_WORKCENTER_RATE_MISSING` → quote blocked | **INTERNAL_COST_INCOMPLETE** — warn; commercial may proceed with acknowledgement |
| `aggregate_bom:missing_pricing:WC_ASSEMBLY` | **INTERNAL_COST_INCOMPLETE** — not commercial blocker |
| Missing geometry / material pricing | **COMMERCIAL_BLOCKER** — keep |
| `finish_groups_unconfirmed` | **COMMERCIAL_BLOCKER** or **OWNER_ACK** — policy decision |
| `total_cost <= 0` → blocked | Split: `commercial_total <= 0` vs `estimated_internal_total <= 0` |

---

## 6. Reinterpretation of workcenter rates

### Today

- Table: `workcenter_rates`
- Fields: `rate_per_hour`, `rate_per_linear_meter`, `rate_basis`
- Docstring: “canonical source of truth for **hourly rates**”
- UI: Pricing Registry — “Workcenter rates”, edit `rate_per_hour`

### Step 7F contract (conceptual — no rename migration yet)

| Old mental model | New mental model |
|------------------|------------------|
| Workcenter rate = what client pays | **Internal operation unit cost rule** |
| `rate_per_hour` = client tariff | **Internal labor cost per hour** — for estimate & post-job comparison only |
| `rate_per_linear_meter` = generic rate | **Internal cost per ml / m² / buc** — may inform commercial rule drafting, not replace it |
| Missing rate = cannot quote | Missing rate = **internal cost incomplete** / low margin confidence |

### Proposed UI labels (future)

- ✅ “Reguli cost intern (estimare)”
- ✅ “Cost intern estimativ per ml / buc / m²”
- ✅ “Verificare manoperă / capacitate”
- ❌ “Tarif preț client”
- ❌ “Preț pe oră ofertat clientului”

### Allowed uses of `rate_per_hour` after realignment

1. **EstimatedInternalCost** — fallback when no mp/ml/buc rule exists yet (legacy)
2. **Capacity check** — estimated hours vs calendar
3. **ProfitabilityAnalysis** — effective hourly cost realized vs estimated
4. **Never** as the sole commercial formula shown to client

---

## 7. Impact on Step 7E blockers (reinterpretation)

### `WC_ASSEMBLY` missing / `rate_per_hour` null

| Old interpretation | Step 7F interpretation |
|--------------------|------------------------|
| “Cannot reprice quote 4” | “Internal assembly cost rule missing — **margin confidence low**” |
| Blocks `/price` | Should **not alone** block **CommercialPriceProposal** if commercial rules exist (e.g. lei/set litere) |

### Remain real blockers for quote 4 (unchanged)

- Finish groups **0/N confirmed** (product/commercial completeness)
- Quote 4 **no quote_input** / linkage incomplete
- Geometry canonical gaps (`letter_face_area_m2`, etc.)
- Critical **material pricing** missing for commercial lines
- Missing **commercial formula** for active priced scope

### Step 7E.2 apply (still on hold)

Payload repair remains valid for **product truth** (Intake → quote_input). After 7F, setting WC rates is **recommended for internal analytics**, not a prerequisite to **offer** a volumetric letters job with explicit lei/m² or lei/literă rules.

---

## 8. Roadmap (recalibrated)

| Step | Name | Scope | Runtime? |
|------|------|-------|----------|
| **7F** | Cost philosophy contract | **This document** | No |
| **7G** | `CommercialPriceProposal` schema + read-only prototype | New schema; preview endpoint; no `/price` change | Read-only prototype only |
| **7H** | `EstimatedInternalCost` separated from commercial | Rename gates; split snapshot fields; CE output tagging | Yes — guarded |
| **7I** | Quote 4 payload repair | After owner input (finish groups); apply linkage | Yes — owner GO |
| **8** | Quote snapshot | Side-by-side `commercial_price` + `estimated_internal_cost` + provenance | Yes |
| **9** | Task execution | ExecutionActuals collection hardened | Yes |
| **10** | ProfitabilityAnalysis | Post-job dashboard + recommendations | Yes |

**Deferred from old path:** Reprice quote 4 until 7G–7H clarify commercial vs internal separation and owner confirms commercial rules for volumetric v2.

---

## 9. Forbidden future behavior

The following are **explicitly forbidden** in future implementation:

1. **`final_quote_price = total_internal_cost × margin`** as the **only** universal rule
2. **Missing `rate_per_hour`** automatically blocking commercial price
3. **Minutes × hourly rate** as the **primary** client-facing formula
4. UI copy implying the **client pays for our time** (“ore × tarif”, “preț orar client”)
5. Retroactive change of accepted commercial price from ExecutionActuals
6. Using Aggregate Cost BOM **blocked** status as synonymous with “cannot offer client”

---

## 10. Acceptance criteria (this document)

| Criterion | Met |
|-----------|-----|
| Clarifies owner philosophy (product/solution pricing) | ✅ |
| Separates commercial price from internal cost | ✅ |
| Preserves Intake V6 as product source of truth | ✅ |
| Preserves ProductDefinition / Aggregate / Aggregate BOM | ✅ |
| Stops minute=price drift in **future** steps | ✅ (contract defined) |
| Proposes next steps without implementing runtime | ✅ |

---

## Appendix A — Conceptual schema (non-binding, no migration)

```yaml
CommercialPriceProposal:
  template_code: string
  workspace_id: string | null
  lines:
    - line_id: string
      rule_type: mp | ml | buc | set | minim | complexitate | urgenta
      quantity: number
      unit: string
      unit_price: number
      line_total: number
      provenance: string  # rule_id, owner_policy, manual
  subtotal: number
  commercial_total: number
  target_margin_pct: number | null
  warnings: string[]

EstimatedInternalCost:
  material_total: number
  operation_total: number
  overhead_total: number
  estimated_total: number
  completeness: ready | partial | blocked
  internal_blockers: string[]
  estimated_effort_minutes: number | null  # sanity only

QuoteSnapshot_vNext:
  commercial: CommercialPriceProposal
  estimated_internal: EstimatedInternalCost
  # legacy alias during migration:
  # price.final ← commercial.commercial_total (NOT estimated_total × margin)
```

---

## Appendix B — References

- Cost Philosophy Realignment Audit (2026-06-30) — conversation / report
- `docs/architecture/MODULAR_PRODUCT_FLOW_CONTRACT.md` — flow (note: §“Prices from workcenter_rates only” superseded by this contract for **commercial** price)
- `docs/architecture/TPL_VOLUMETRIC_LETTERS_COSTING_LOGIC_AUDIT.md` — owner unit-based ops
- Steps 7A–7D implementation reports — Aggregate path, UI truth alignment

---

**Document owner:** WorkOS architecture  
**Next review:** Before Step 7G implementation  
**Runtime status:** UNCHANGED — design only
