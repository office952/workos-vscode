# WorkOS Full System Reality Audit

**Date:** 2026-06-07  
**Scope:** UI + tabs + code + endpoints + data flow + roadmap realignment  
**Repo:** `C:\Users\offic\Desktop\workos-active`  
**Mode:** AUDIT ONLY — no runtime changes, no DB, no `/price`, no quote 4 reprice  
**Reference contract:** `docs/architecture/WORKOS_COMMERCIAL_PRICING_VS_INTERNAL_COST_CONTRACT.md` (Step 7F)

---

## 1. Executive verdict

### **`HIGH_RISK_DEVIATED`**

WorkOS has a **strong product-truth spine** (Intake V6 → ProductDefinition → ProductAggregate → execution actuals) but the **commercial pricing spine is still cost-plus and hour-capable**, contradicting the owner rule: *nothing commercial is calculated at hourly rate*.

| Dimension | Status |
|-----------|--------|
| Product truth (Intake V6, geometry, materials, finishes) | **Coherent** — best-in-system |
| Internal cost estimation path | **Partial** — Aggregate BOM + Cost Engine exist but mixed with hourly default |
| Commercial price proposal | **Missing as model** — collapsed into `total_cost × margin` |
| Execution actuals (task start/stop) | **Correct role** — operational, not quote source |
| ProfitabilityAnalysis | **Not implemented** |
| UI clarity | **Mixed** — some honest read-only labels; Pricing/Intake panels imply cost→offer |
| Legacy surface area | **Large** — intake v3/v4/v5 routers, mock pages, parallel flows |

**Before Step 7G/8:** Do **not** extend `/price`, Pricing Registry edits, or quote snapshot work until `CommercialPriceProposal` is separated from `EstimatedInternalCost` per Step 7F contract.

---

## 2. One-page summary

### Coherent today

- **Intake V6** volumetric workspace: SVG → layers → review (finisaje/iluminare/montaj) → confirm — canonical product capture.
- **ProductDefinition / ProductAggregate / Cost BOM preview** (Steps 6–7D): read-only truth paths aligned with modular product flow.
- **Execution stack**: Operator, Tablet, ExecutionDetail reality start/end — minutes belong here.
- **Inventory material registry** as acquisition/unit cost source (internal, not stock-on-hand for quoting).
- **Owner unit-based ops doc** (`TPL_VOLUMETRIC_LETTERS_COSTING_LOGIC_AUDIT.md`) — per ml/buc/m² intent documented.

### Deviated today

- **`QuoteOrchestrator._apply_commercial`**: `net = total_cost × (1 + margin)` on all v1/v2/aggregate paths.
- **Cost Engine default `rate_basis=per_hour`**: minutes → hours × `rate_per_hour` → operation line → total → quote.
- **Pricing page** treats `workcenter_rates` as “Operații / Rate” for quote calculation; UI `RATE_BASIS_OPTIONS` only `per_hour | per_linear_meter` (no per_piece/per_m² in admin UI).
- **Intake V6 `intakeV6OfferCalculator`**: client-facing offer model = internal cost buckets + markup + discount + VAT (**cost-plus in UI**).
- **No `CommercialPriceProposal` schema** in backend — design doc only.

### Dangerous today

- **`POST /api/v1/entities/quotes/price`** and **`/{id}/price`**: single pipeline bundles internal cost + commercial price.
- **Aggregate BOM blockers** (`missing_pricing`, `WC_ASSEMBLY`) gate commercial readiness — owner says these should gate **margin confidence**, not necessarily offer.
- **DocumentCenter**: synthetic docs from quotes/orders — looks operational, no document API.
- **Settings → Societate tab**: static mock while CostEngine tab is live pricing config.
- **Intake v3**: ~72 deprecated endpoints still mounted.

### Required before Step 7G/8

1. Step **7G** — `CommercialPriceProposal` read-only prototype (no `/price` change).
2. Step **7H** — split `EstimatedInternalCost` from commercial in orchestrator + snapshot fields.
3. Reclassify Pricing Registry labels (internal cost rules, not client hourly tariff).
4. Owner input on finish groups + commercial rules per zone (Step 7E.1 hold remains).
5. Deprecation labels for legacy intake routes and mock pages (Step 11 — no code yet).

---

## 3. Full menu map

Classification legend: **AO** ACTIVE_OPERATIONAL · **RO** ACTIVE_READONLY_TRUTH · **AR** ADMIN_REGISTRY · **AN** ANALYTICS_ONLY · **FR** FUTURE_RESERVED · **LC** LEGACY_COMPATIBILITY · **MU** MISLEADING_UI · **DP** DEAD_PIECE · **HR** HIGH_RISK_WRONG_DIRECTION · **ND** NEEDS_OWNER_DECISION

### Operațiuni

| Menu | Route | Component | Tabs / panels | Read/Write | Key endpoints | Status | Risk | Recommendation |
|------|-------|-----------|---------------|------------|---------------|--------|------|----------------|
| Control Tower | `/dashboard` | `Dashboard.tsx` | KPI cards, alerts, throughput | R (mock fallback) | `GET /api/v1/dashboard-stats` | RO | Mock if API down | Keep; label mock state |
| Shop Floor | `/shop-floor` | `ShopFloor.tsx` | Workcenter grid, jobs, alerts | R | `GET /machines`, `GET /operator/tasks` | RO | Mock alerts | Keep |
| Operator | `/operator` | `OperatorView.tsx` | Task panel, materials, blueprint, clarifications | R+W | `POST /operator/task-action`, reality materials | AO | Minutes OK here | Keep; protect from quote reuse |
| Atelier Tablet | `/tablet/*` | `TabletMode.tsx` | Station → queue → task detail | R+W | Same as Operator | AO + MU | “Cere ajutor” demo-only | Label help as non-persisted |

### Comercial

| Menu | Route | Component | Tabs / panels | Read/Write | Key endpoints | Status | Risk | Recommendation |
|------|-------|-----------|---------------|------------|---------------|--------|------|----------------|
| Clienți | `/clients`, `/clients/:name` | `Clients.tsx`, `ClientWorkspace.tsx` | Overview, cereri, oferte, comenzi; **facturi/documente/note empty** | R | Entity GET clients/intakes/quotes/orders | RO + FR | Placeholder tabs | Keep placeholders honest |
| Work Intake | `/intake` | `WorkIntake.tsx` | Pipeline filters (new…blocked) | R+W | `intake_requests` CRUD; `POST quotes/from-intake` | AO + LC | Routes volumetric to V6 | Keep hub; deprecate non-vol detail |
| Work Intake detail | `/intake/:id` | `IntakeLegacyRoute` → V6 or `IntakeDetail` | Legacy form sections | R+W | intake_requests; assist APIs | LC + MU | Non-vol still legacy | Redirect all to V6 when ready |
| Intake V6 | `/intake-v6/.../operator` | `IntakeV6OperatorWorkspaceApp` | Steps: SVG → Review (finisaje/iluminare/montaj) → Confirm | R+W | `/api/v1/intake-v6/*` | AO | Offer calc = cost-plus (**HR**) | Freeze layout; fix pricing in 7G+ |
| Oferte | `/quotes`, `/quotes/:id` | `Quotes.tsx` | List + detail; QuoteWizard modal | R+W | `quotes` CRUD; **`POST .../price`** | AO + **HR** | `/price` = cost-plus | Step 8 split snapshot |
| Comenzi | `/orders`, `/orders/:id` | `Orders.tsx` | Status pipeline | R+W | orders CRUD; `POST execution/plan/from-order` | AO | Mock jobs if mock | Keep |
| Execuție | `/execution`, `/execution/:id` | `ExecutionDashboard`, `ExecutionDetail` | Observability, plan gate, reality tasks | R+W | `GET execution/dashboard`, `POST reality/start-task` | AO + RO | Correct actuals role | Step 9 harden |
| Execuție review | `/execution/reality-review` | `OperationalRealityReview.tsx` | Review table | R | `GET /operational-reality/review` | AN | — | Keep |
| Documente | `/documents` | `DocumentCenter.tsx` | Doc list from quotes/orders | R (synthetic) | Reads quotes/orders only | **MU** + DP | No document API | Step 11 deprecate or wire real API |

### Resurse

| Menu | Route | Component | Tabs | Read/Write | Key endpoints | Status | Risk | Recommendation |
|------|-------|-----------|------|------------|---------------|--------|------|----------------|
| Inventar & OC | `/inventory` | `Inventory.tsx` | all, placi, role, cerneala, altele, sheet_quality, **automatizare (mock)** | R (+ mock writes) | `inventory_materials`, suppliers | RO + MU | Mock tabs in live mode | Isolate mock tabs |
| Pricing | `/inventory/pricing` | `Pricing.tsx` | **coverage, all, verify, markup, audit** | R+W admin | `GET /pricing/registry`; PATCH admin materials/WC rates; markup policies | AR + **HR** | “Quote calculation hub”; per_hour default | Step 7I rename/separate |
| Product System | `/product-system` | `ProductSystem.tsx` | Library: active/archived; Studio: structure, operational, form-system, general | R+W | product_templates, families, simulate-cost (admin) | AR | Cost BOM panel RO truth (7D) | Keep; add commercial preview 7G |
| Blueprint Dossier | `/product-system/blueprint-dossier` | `BlueprintDossierStudio.tsx` | Dossier sections, active/archived list | R+W | product-blueprint-dossiers | AR | CE mapping = config not live quote | Keep |
| Dossier completion | `/product-system/dossier-completion` | `DossierCompletionDashboard.tsx` | Completion metrics | R | product-readiness | RO | Not canonical readiness | Label clearly |
| Output blocks | `/product-system/output-blocks-preview` | `OutputBlocksPreview.tsx` | Preview | R | output-blocks APIs | FR | — | Keep |
| Colaboratori | `/colaboratori` | `Colaboratori.tsx` | Supplier list | R+W | suppliers entity | AR | HUB boundary metadata | Keep future-only |
| Utilaje | `/utilaje` | `Utilaje.tsx` | Machine list; blocked create; **local ink settings** | R | `GET /machines` only | RO + MU | Create blocked; ink not saved | Persist or remove ink UI |
| Rapoarte | `/reports` | `Reports.tsx` | Summary charts | R | `GET /reports-summary` | RO | Mock fallback | Keep |
| Rapoarte operaționale | `/reports/operational` | `OperationalReports.tsx` | Completitudine, angajați, taskuri, materiale, montaj | R | `GET /operational-reports/summary` | AN | Explicitly no profit | Keep |

### Personal

| Menu | Route | Component | Tabs | Read/Write | Key endpoints | Status | Risk | Recommendation |
|------|-------|-----------|------|------------|---------------|--------|------|----------------|
| Angajați operaționali | `/employees` | `Employees.tsx` | Filters | R+W | `/entities/employees` | AR | `cost_ora_calculat` from backend | OK if not in quote |
| Evidență HR | `/employees-records/*` | `EmployeesRecords`, `EmployeeProfile` | Profile sections | R+W | employees + registry | AR | HR only | Keep |
| Pontaj | `/attendance` | `Attendance.tsx` | Month calendar | R+W | `/employee-attendance/*` | AO | Not fiscal | Keep |
| Efecte pontaj | `/attendance/effects` | `EmployeeAttendanceEffects.tsx` | — | R+W | attendance effects | AO | Payroll-adjacent | Keep |
| Plăți angajați | `/employee-payments` | `EmployeePayments.tsx` | Tranșa 15/30 | R+W | `/employee-payments/*` | AO | — | Keep |
| Avansuri | `/employee-advances` | `EmployeeAdvances.tsx` | Ledger | R+W | `/employee-balances/*` | AO | — | Keep |
| Employee mobile | `/employee-app/*`, `/employee-app-v2/*` | Mobile apps | Task sessions | R+W | `/employee-mobile/*` | AO | Actuals source | Step 9 link |

### Sistem

| Menu | Route | Component | Tabs | Read/Write | Key endpoints | Status | Risk | Recommendation |
|------|-------|-----------|------|------------|---------------|--------|------|----------------|
| Module Chain | `/modules` | `ModuleChain.tsx` | Health + static events | R | `GET /system/health` | RO + DP | Events are static demo | Label demo |
| Governance | `/governance` | `Governance.tsx` | boundaries, flows, agents, truth, gates… | R | **None** — `governanceData` | REFERENCE | Not runtime | Keep as docs UI |
| Setări | `/settings` | `Settings.tsx` | Societate, Plăți rec., **CostEngine**, Integrations | R+W (partial) | recurring-payments, cost-engine, SmartBill | AR + MU | Societate = mock | Wire or label mock |
| Demo routes | `/demo/*` | CommercialSpineDemo, etc. | — | R | varies | FR | Hidden from menu | Keep isolated |

**Hidden redirects (legacy URLs):** `/products`, `/templates` → product-system; `/inventory/material-price-registry` etc. → pricing; `/personal` → employees.

---

## 4. Tab-by-tab audit (critical pages)

### Intake V6 (`IntakeV6OperatorWorkspaceApp`)

| Tab / step | Role | Data source | Endpoints | Writes DB? | Mismatch / risk |
|------------|------|-------------|-----------|------------|-----------------|
| SVG Analyzer | Geometry + layer roles | Workspace payload | `POST svg`, `PUT analysis-bundle`, `PUT layer-roles` | Yes | — |
| Review → Finisaje | Finish groups, RAL, artwork | `finish_setup`, `letter_group_finishes` | `PUT finish-setup`, `PUT letter-group-finishes` | Yes | 0/N confirmed blocks handoff |
| Review → Iluminare | LED, PSU | workspace modules | preview endpoints | Partial | — |
| Review → Montaj | Mounting, premount | workspace | preview endpoints | Partial | — |
| Live calculation panel | **Internal cost preview** | material breakdown + pricing snapshot | `pricing-input-preview`, `material-breakdown`, `pricing-snapshot` | No | **TAB_PRICING_PHILOSOPHY_RISK**: shows line costs; “tarif lipsă” tied to registry |
| Offer / commercial inputs | **Client offer preview** | `intakeV6OfferCalculator` | Uses preview payloads | No (until quote create) | **HR**: `productionBase` = internal costs × markup |
| Confirm | Handoff gates | readiness + blockers | `create-draft-quote`, spine POSTs | Yes on CTA | Blockers include missing rates |
| Pricing input panel (7D notice) | Truth label | — | — | No | Correctly says aggregate path read-only |

### Product System (`ProductSystem.tsx`)

| Tab | Role | Endpoints | Writes? | Risk |
|-----|------|-----------|---------|------|
| Library active/archived | Template picker | product_templates | Yes (CRUD) | Mock templates if mock flag |
| Studio → Structure | Components, materials, ops | template JSON | Yes | Legacy `comp_auto_1` synthesis |
| Studio → Operational | Task rules, routing | template + registry | Yes | Parallel to dossier |
| Studio → Form System | Mini-module bindings | `form-contract`, Cost BOM panel | No (BOM preview) | **RO truth** — Step 7D OK |
| Studio → General | Metadata | template fields | Yes | — |
| Cost BOM preview | Aggregate readiness | `GET cost-bom-preview/{code}` | No | Blockers include WC rates (**reclassify 7F**) |

### Pricing (`Pricing.tsx`)

| View (`PricingMainView`) | Role | Endpoints | Writes? | Risk |
|--------------------------|------|-----------|---------|------|
| coverage | Template-filtered registry coverage | `GET /pricing/registry` | No | Mixed material + WC + markup |
| all | Full registry table | same | No | — |
| verify | Gate readiness | same + local gates | No | `no_price` blocks “ready” |
| markup | Commercial markup policies | admin markup APIs | Yes | **Cost-plus policies** |
| audit | Dry-run markup | `POST .../dry-run` | No | Applies margin to cost |

**Workcenter edit form:** `RATE_BASIS_OPTIONS = ["per_hour", "per_linear_meter"]` — missing `per_piece`, `per_square_meter` despite backend support.

### Inventory (`Inventory.tsx`)

| Tab | Role | API | Risk |
|-----|------|-----|------|
| all, placi, role, cerneala, altele | Stock view | inventory_materials | OK — not quote source |
| sheet_quality | Admin audit | admin inventory | OK |
| automatizare | **Mock** purchase/simulation | local `inventoryEngine` | **TAB_LEGACY_CONTENT** — disabled banner in live |

### Oferte (`Quotes.tsx`)

| Area | Role | Endpoints | Risk |
|------|------|-----------|------|
| List | Quote pipeline | GET quotes | Mock fallback |
| Detail | Line items, breakdown | GET quote by id | Shows `componentBreakdown` from cost engine |
| QuoteWizard | Create + **price** | `POST /quotes/price` | **HR** canonical commercial path |
| Reprice / revision | In-place price | `POST /quotes/{id}/price` | Same |
| Convert to order | Order creation | `POST orders/from-quote` | OK |

### Execuție (`ExecutionDetail.tsx`)

| Section | Role | Endpoints | Actual vs estimated |
|---------|------|-----------|---------------------|
| Observability | Plan vs reality | `GET observability` | Shows both |
| Plan gate | Generate plan | `POST plan/from-order` | Write |
| Reality tasks | Start/complete | `POST reality/start-task`, `end-task` | **Actual minutes** |
| Stock deduction | Preview | inventory deduction status | Not pricing |

---

## 5. Endpoint audit (condensed inventory)

**Router count:** 77 modules under `backend/routers/` (auto-included via `main.py`).

### Critical pricing / quote endpoints

| Method | Path | Class | Consumer | Notes |
|--------|------|-------|----------|-------|
| POST | `/api/v1/entities/quotes/price` | **DANGEROUS_MIXED** | Quotes wizard, tests | Creates quote + applies `_apply_commercial` |
| POST | `/api/v1/entities/quotes/{id}/price` | **DANGEROUS_MIXED** | Quotes reprice | In-place revision |
| GET | `/api/v1/pricing/registry` | **DANGEROUS_MIXED** | Pricing page | Materials + WC + markup unified |
| PATCH | `/api/admin/workcenter-rates/{code}` | INTERNAL_COST | Pricing admin | Default `per_hour` |
| PATCH | `/api/admin/inventory-materials/{code}` | INTERNAL_COST | Pricing admin | `unit_cost` → Cost Engine |
| POST | `/api/admin/commercial-markup-policies/dry-run` | COMMERCIAL_PRICING | Pricing audit tab | Margin on cost |
| POST | `/api/v1/product-system/simulate-cost` | **DANGEROUS_MIXED** | ProductSystem admin | Same engine as `/price`, no persist |
| GET | `/api/v1/product-system/cost-bom-preview/{code}` | READ_ONLY | Form System 7D | Internal BOM truth |
| GET | `/api/v1/intake-v6/pricing-snapshot` | **DANGEROUS_MIXED** | Intake V6 | Exposes raw rates to operator |
| GET | `/api/v1/intake-v6/workspaces/{id}/pricing-input-preview` | READ_ONLY | Intake V6 | quote_input assembly |
| POST | `/api/v1/intake-v6/.../create-draft-quote` | WRITE_OPERATIONAL | Intake confirm | Does not call `/price` alone |
| PUT | `/api/v1/cost-engine/config` | INTERNAL_COST | Settings | v1 profile rates 80/40 RON/h |

### Legacy intake (still mounted)

| Prefix | Endpoints | Class |
|--------|-----------|-------|
| `/api/v1/intake-v3` | ~72 deprecated | LEGACY |
| `/api/v1/intake-v4` | workspace + quote spine subset | LEGACY_COMPAT |
| `/api/v1/intake-v5` | analyze, calculate, quote, order | LEGACY + MIXED |

### Execution actuals (correct zone)

| Method | Path | Class |
|--------|------|-------|
| POST | `/api/v1/execution/reality/start-task` | EXECUTION_ACTUALS |
| POST | `/api/v1/execution/reality/end-task` | EXECUTION_ACTUALS |
| POST | `/api/v1/operator/task-action` | EXECUTION_ACTUALS |
| POST | `/api/v1/employee-mobile/tasks/{id}/start` | EXECUTION_ACTUALS |
| GET | `/api/v1/operational-reality/review` | ANALYTICS |

### Missing / design-only

- `CommercialPriceProposal` — **no endpoint**
- `EstimatedInternalCost` — partial via simulate-cost / snapshot `cost_result`
- `ProfitabilityAnalysis` — **no endpoint**

---

## 6. Pricing / cost / quote philosophy audit

### Canonical quote price construction (today)

```
Intake/product_template/quote_input
    → QuoteOrchestrator.build_snapshot()
        → CostEngine v2 (rate_basis default per_hour OR ml/buc/m² if configured)
        → total_cost
    → _apply_commercial(total_cost, margin, discount, VAT)
    → QuotePrice.final → grand_total persisted
```

**Location:** `backend/services/quote_orchestrator.py` lines ~432, ~569, ~756, ~945–958.

### Search-term findings (material locations)

| Term | Role today | Commercial? | Internal? | Analytics? | Risk |
|------|------------|-------------|-----------|------------|------|
| `rate_per_hour` | WC registry + CE per_hour path | **Yes** (via total_cost) | Yes | Possible | **HR** |
| `workcenter_rates` | Registry + BOM blockers | **Yes** when missing blocks quote | Yes | — | **HR** |
| `estimated_minutes` | Formula handlers → CE | **Yes** if per_hour | Yes | Post-job potential | **HR** |
| `rate_basis=per_linear_meter` | Owner volumetric ops | Yes if used | Yes | — | OK if primary |
| `per_piece` / `per_square_meter` | Backend CE support | Yes | Yes | — | OK; **UI admin incomplete** |
| `margin` / markup policies | `_apply_commercial` + Intake offer calc | **Yes** | — | — | **HR** cost-plus |
| `CommercialPriceProposal` | docs only | — | — | — | Gap |
| `execution_reality.total_actual_time_minutes` | Execution | No | — | Yes | **ANALYTICS_ONLY_OK** |
| `labour_rate_ron_per_hour=80` | v1 CE fallback | **Yes** if v1 path | Yes | — | **HR** legacy |

### Tests enforcing obsolete flow

- `test_blk18_cost_engine_boundary.py` — validates `rate_per_hour` merge (internal, OK).
- `test_quote_in_place_pricing_contract.py` — `/price` contract (cost-plus assumed).
- `test_volumetric_preliminary_costing.py` — workcenter_rates in simulation.

---

## 7. Commercial pricing registry audit (Section E)

**Verdict: No dedicated commercial pricing registry exists.** What exists is a **mixed technical registry**.

| Owner rule | Exists? | Where stored | Used by Intake? | Used by CE/Quote? | Philosophically correct? |
|------------|---------|--------------|-----------------|-------------------|----------------------------|
| CNC lei/ml by material+thickness+bevel | **Partial** | `workcenter_rates` (`rate_basis=per_linear_meter`) + formula_params pass counts in template/dossier | Preview breakdown | CE if rate_basis set | **Partial** — not material×thickness matrix |
| Cant aluminiu lei/ml | **Partial** | WC rate + geometry keys | Breakdown rows | CE | Partial |
| Vopsire lei/m² or minim | **Partial** | `PAINTING` per ml in owner doc; not separate commercial table | Live calc | CE | **Wrong unit** if ml used for paint |
| LED lei/modul or set | **Partial** | `rate_basis=per_piece` in audit doc | Intake LED inputs | CE if configured | OK intent |
| Asamblare lei/literă or pachet | **No commercial rule** | ASSEMBLY explicitly not quote-priced in audit | — | Internal only | **Gap** |
| Șablon montaj lei/m² | **Partial** | Template module + rates | Preview | CE | Partial |
| Ambalare fix | **Partial** | per m² in audit doc | — | CE | Partial |
| Montaj șantier | **Future** | subcontract metadata | Intake montaj tab | Not priced | FR |
| Minim lucrare | **No** | — | — | — | **Missing** |
| Complexitate | **No commercial coef** | `artwork_complexity_decisions` = product only | Intake review | Not in quote formula | **Missing** |
| Urgență | **No** | — | — | — | **Missing** |
| Product/package rules | **No** | — | — | — | **Missing** |

**Storage summary:** DB tables `workcenter_rates`, `inventory_materials.unit_cost`, `commercial_markup_policies` — all feed **internal cost → margin**, not standalone commercial proposal.

---

## 8. Intake V6 audit (Section F)

| Question | Answer |
|----------|--------|
| Coherent product source of truth? | **DA** — for volumetric letters (geometry, finishes, LED, mounting modules) |
| Canonical fields | `analysis_bundle`, `layer_roles`, `finish_setup`, `letter_group_finishes`, `quote_geometry`, workspace module flags |
| Legacy / fallback | `intakeV4*` API naming in frontend; artwork complexity = FUTURE_RESERVED; some v4 compat keys in payload |
| Price/cost calc in Intake | **DA** — `IntakeV6LiveCalculationSummary`, `intakeV6OfferCalculator`, material breakdown services — **internal + cost-plus offer** |
| Reads from Pricing | `pricing-snapshot`, registry rates in previews — **not commercial rules** |
| Hardcoded | Default markup 35%, VAT 19%, EUR/RON fallback in offer calculator |
| Move to CommercialPriceProposal | Offer totals, minim/complexity/urgency, per-zone mp/ml/buc rules |
| Keep unchanged | Step flow, Review tabs, workspace schema, SVG analyzer |
| Misleading labels | “Calcul live”, “Preț” column on material lines — reads as client price; Confirm says “cost intern” (better) |
| UI drift risk | **Frozen by policy** — audit found presentation atoms only; no layout change requested |

---

## 9. Product System audit (Section G)

| Question | Answer |
|----------|--------|
| Source of truth | **ProductDefinition** (builder) + **ProductAggregate** (expanded modules) for technical structure |
| Preview only | Cost BOM preview, product-definition GET, simulate-cost |
| Legacy | Parent template empty → UI synthesizes `comp_auto_1`; `comp_flat_legacy` diagnostic |
| Active modules (volumetric v2) | `TPL-VOLUM-ALUMINIU_v1`, premount optional, face/back prep modules |
| Future | `geometry_svg`, `electrica_logo`, artwork complexity pricing |
| Dead | `comp_flat_legacy` in cost path (blocked if leaked) |
| Hourly push | Dossier `time_formulas`, CE mapping with `per_hour` defaults |
| Missing for CommercialPriceProposal | Dedicated commercial rule registry + preview endpoint |
| Keep | Aggregate adapter, Step 7D UI notices, mini-module registry |

---

## 10. Quote / Order audit (Section H)

| Question | Answer |
|----------|--------|
| Where is final price built? | `QuoteOrchestrator._apply_commercial(cost_result.total_cost)` after CE |
| `commercial_price` separate from `estimated_internal_cost`? | **NU** — single `QuotePrice` object |
| Where mixed? | Snapshot `cost_result` + `price` in same payload; Intake offer calculator mirrors same |
| Margin applied? | `(1 + margin)` on total_cost; markup policies in Pricing admin |
| Universal cost-plus? | **DA** — all three orchestrator paths |
| minutes=price risk? | **DA** when `rate_basis=per_hour` or v1 fallback |
| Step 8 change | Side-by-side snapshot fields per 7F contract |
| Do not touch until GO | Quote 4 reprice, 7E.2 apply, `/price` behavior |

**Quote 4 path (read-only audit state):** draft, `grand_total=0`, no `quote_input`, intake linkage incomplete — see Step 7E reports.

---

## 11. Execution / Shop Floor audit (Section I)

| Question | Answer |
|----------|--------|
| Real time collected | `execution_reality` start/end; employee mobile task sessions; operator task-action timestamps |
| UI start/stop | Operator, Tablet, ExecutionDetail, Employee mobile |
| DB writes | reality tasks, sessions, material capture |
| Actual vs estimated | Observability compares plan estimates vs actual minutes |
| Link to order | execution_plan from order; tasks scoped by order_id |
| ProfitabilityAnalysis link | Data exists; **no analysis layer** |
| Risk of minutes in initial pricing | **Low in execution code** — risk is upstream in CE/orchestrator |
| Protect | Keep execution APIs out of `/price`; do not feed actuals back into quote |

---

## 12. HR / Pontaj audit (Section J)

| Page | Calculates | Writes | In quote/pricing? |
|------|------------|--------|-------------------|
| Employees | Displays `cost_ora_calculat` | CRUD employees | **Not directly** — OK_ANALYTICS if stays HR |
| Attendance | Hours/exceptions | Events CRUD | OK |
| Payments / Advances | Net pay, balances | Payments, transactions | OK |
| Employee mobile | Task duration | Sessions | OK — actuals |

**No evidence** employee hourly cost is multiplied into `/price` today; risk is **indirect** via workcenter `rate_per_hour` conflation.

---

## 13. System / Governance / Settings (Section L)

| Area | Controls | Active? | Risk |
|------|----------|---------|------|
| Module Chain | Module health | Partial live | Static events misleading |
| Governance | Architecture docs | Static | Safe |
| Settings → CostEngine | v1 labour/machine rates | **Live write** | **HR** — 80/40 RON/h fallback |
| Settings → Societate | Company info | **Mock** | MU |
| SmartBill integration | External invoicing | Config | Future commercial docs |
| Dev guard bypass | Session bypass for protected routes | Env flag | Can hide auth gaps |

---

## 14. Dead pieces / duplicate flows (Section M)

| Location | Suspect reason | Used? | Recommendation |
|----------|----------------|-------|----------------|
| `backend/routers/intake_v3_*` | Deprecated 72 endpoints | Tests/compat | **deprecate** — mount guard |
| `backend/routers/intake_v5.py` | Parallel calculate/quote | Low | **isolate** |
| `IntakeDetail` + `/intake/:id` | Pre-V6 form | Non-volumetric | **deprecate** |
| `DocumentCenter` | Mock doc generation | Menu visible | **deprecate** or implement |
| `Utilaje` ink settings | Local state only | UI shown | **remove later** or persist |
| `ModuleChain` REFERENCE_EVENTS | Static | Display | **rename** “Architecture demo” |
| `CommercialSpineDemo`, `/demo/*` | Dev demos | Hidden | keep isolated |
| Parallel task catalog (V3 ops) | Not ProductDefinition tasks | Intake previews | **needs owner decision** |
| `intake_v4_*` frontend API names | Namespace compat | Active in V6 | keep until rename sprint |
| Tests for intake-v3/v4 | Large surface | CI | trim in Step 12 |

---

## 15. Misleading UI labels / side-effect risks (Section O — audit only, no changes)

| Location | Issue | Future copy/label only |
|----------|-------|------------------------|
| Pricing page header | “Quote calculation pricing hub” | Split: “Reguli cost intern” + “Propunere comercială (viitor)” |
| Pricing WC form | “Rate”, default per_hour | “Cost intern estimativ (ml/buc/m²/h)” |
| Intake live calc | Column “Preț” on internal lines | “Cost intern estimat” |
| Intake offer panel | Shows gross total from cost+markup | “Previzualizare cost-plus (de înlocuit)” until 7G |
| Quotes wizard | Implies final client offer from `/price` | Badge “cost intern + marjă” |
| Dashboard/Reports “Live” | May show mock | “Sursă: mock” when applicable |
| DocumentCenter actions | Send/sign/download | “Demo — fără persistență” |
| Tablet “Cere ajutor” | Looks operational | “Demo” |

---

## 16. Source of Truth Map (Section N)

```
1. Product truth
   ├── Intake V6 workspace payload (canonical)
   ├── ProductDefinition (GET /product-system/product-definition)
   └── ProductAggregate (GET /product-system/aggregate)

2. Material truth (acquisition unit cost)
   └── inventory_materials (+ admin PATCH unit_cost)

3. Commercial price truth
   └── ❌ MISSING — target: CommercialPriceProposal registry (Step 7G)
       └── Today wrongly: QuotePrice.final from cost_plus

4. Estimated internal cost truth
   ├── Aggregate Cost BOM (GET cost-bom-preview)
   ├── Cost Engine (simulate-cost, /price cost_result half)
   └── workcenter_rates + material unit costs

5. Execution actuals truth
   ├── execution_reality + task sessions
   └── employee_mobile_tasks timestamps

6. HR truth
   └── employees, attendance, payments, balances

7. Profitability truth
   └── ❌ MISSING — partial data in operational reports (no margin)

8. Governance truth
   └── governanceData (static) + feature flags in settings/env
```

---

## 17. High-risk deviations (action table)

| # | Location | Risk | Impact | Fix step |
|---|----------|------|--------|----------|
| 1 | `quote_orchestrator._apply_commercial` | Cost-plus universal | Client price tied to internal cost | 7H + 8 |
| 2 | CE `per_hour` default | minutes × rate → quote | Violates owner rule | 7H + 7I |
| 3 | Aggregate BOM `missing_pricing` blocks quote | WC rate = cannot offer | Blocks commercial incorrectly | 7F contract → 7H gates |
| 4 | `intakeV6OfferCalculator` | UI cost-plus offer | Operator sees wrong philosophy | 7G UI prototype |
| 5 | Pricing registry unified view | Material cost = offer input | Conflates registries | 7I |
| 6 | `pricing-snapshot` exposes rates | Operator sees “tarif” | Mental model hourly | 7I labels |
| 7 | v1 CE 80/40 RON/h fallback | Silent hourly pricing | Wrong quotes on legacy path | 7H remove from commercial |
| 8 | Markup policies dry-run | Encodes cost-plus | Reinforces wrong model | 7G commercial rules |
| 9 | No CommercialPriceProposal | Cannot express mp/ml/set/min | Structural gap | 7G |
| 10 | DocumentCenter mock | False operational confidence | Process risk | 11 |

---

## 18. Owner-rule compliance (nothing commercial at hourly rate)

| Zone | PASS/FAIL | Motiv |
|------|-----------|-------|
| Intake V6 product capture | **PASS** | Geometry/product — no hourly commercial |
| Intake V6 live calc / offer | **FAIL** | Cost lines + markup; rates from registry including per_hour |
| Product System / BOM preview | **PASS** (mostly) | Internal estimate; blocked on WC — wrong gate but not hourly commercial rule |
| Pricing Registry admin | **FAIL** | per_hour default; labeled as quote rates |
| `/price` / QuoteOrchestrator | **FAIL** | total_cost × margin; per_hour CE path |
| Quotes UI | **FAIL** | Presents `/price` output as offer |
| Execution / Operator / Mobile | **PASS** | Minutes = actuals only |
| HR / Pontaj | **PASS** | Not in quote path |
| Settings CostEngine | **FAIL** | labour_rate_ron_per_hour in v1 config |
| Operational reports | **PASS** | Explicitly excludes profit/hourly commercial |

**Overall owner compliance: FAIL (commercial path)** — **PASS (execution/HR path)**.

---

## 19. Corrective roadmap (aligned to user request)

| Step | Focus | Audit finding driving it |
|------|-------|--------------------------|
| **7G** | CommercialPriceProposal schema + read-only preview | No commercial registry; Intake offer calc wrong |
| **7H** | EstimatedInternalCost separation; decouple `_apply_commercial` | Single snapshot today |
| **7I** | Pricing Registry separation + labels | Mixed registry; per_hour UI |
| **8** | Quote snapshot commercial + internal side-by-side | `/price` bundles both |
| **9** | ExecutionActuals hardening | Data exists; link to orders |
| **10** | ProfitabilityAnalysis | Not built |
| **11** | UI cleanup / deprecation labels | DocumentCenter, mock tabs, Pricing copy |
| **12** | Dead pieces cleanup | intake v3/v5, legacy IntakeDetail |

**Explicitly NOT now:** Quote 4 reprice, 7E.2 apply, `/price` changes, Pricing data edits.

---

## 20. No-side-effects confirmation

| Check | Status |
|-------|--------|
| DB writes | **None** |
| Seeds / migrations | **None** |
| POST `/price` | **Not called** |
| Quote 4 reprice | **Not done** |
| Order / execution_plan / tasks | **Not created** |
| UI / CSS changes | **None** |
| Code changes | **Only this audit document** |
| Git | `workos-active` — **not a git repository** at audit time (no branch/status) |

---

## 21. Roadmap awareness score

| # | Criterion | Score /10 |
|---|-----------|-----------|
| 1 | Intake V6 as product truth | 9 |
| 2 | ProductDefinition / Aggregate | 8 |
| 3 | CommercialPriceProposal (target) | 1 |
| 4 | EstimatedInternalCost (separated) | 4 |
| 5 | Quote snapshot dual-field | 2 |
| 6 | ExecutionActuals | 7 |
| 7 | ProfitabilityAnalysis | 1 |
| 8 | UI honesty / labels | 5 |
| 9 | Legacy containment | 4 |
| 10 | Owner hourly-rule compliance (commercial) | 3 |

### **Cat sunt în direcția stabilită: 68/100**

**Interpretation:** Strong product and execution foundation (~75–80% on Intake→Aggregate→Tasks), but commercial pricing layer (~25–35%) still implements pre-7F cost-plus/hour-capable model. Step 7F contract exists; **implementation gap** is the main drag.

---

## Appendix A — Commands run

```text
cd C:\Users\offic\Desktop\workos-active
git status --short          → fatal: not a git repository
git branch --show-current   → fatal: not a git repository

rg Route/path/nav frontend/src/App.tsx
rg APIRouter/include_router backend/routers (77 modules)
rg rate_per_hour|QuoteOrchestrator|CostEngine backend frontend docs
rg IntakeV6|intake-v6 backend frontend
rg legacy|mock|deprecated backend frontend docs
```

Runtime UI verification: **not performed** (audit from code + docs; optional live pass deferred to avoid stale server ambiguity).

---

## Appendix B — Key file references

| Topic | Path |
|-------|------|
| Menu / routes | `frontend/src/App.tsx` |
| Quote commercial transform | `backend/services/quote_orchestrator.py` |
| Cost Engine per_hour | `backend/services/cost_engine_service.py` |
| Aggregate BOM blockers | `backend/services/aggregate_cost_bom_adapter.py` |
| Pricing registry service | `backend/services/pricing_registry_service.py` |
| Intake offer cost-plus | `frontend/src/lib/intakeV6/intakeV6OfferCalculator.ts` |
| Step 7F contract | `docs/architecture/WORKOS_COMMERCIAL_PRICING_VS_INTERNAL_COST_CONTRACT.md` |
| Owner unit ops | `docs/architecture/TPL_VOLUMETRIC_LETTERS_COSTING_LOGIC_AUDIT.md` |

---

**Audit complete.** Brutal honesty: WorkOS today is a **production-oriented system with a legacy commercial pricing engine**. Realignment is documented (7F) but **not yet reflected in runtime**. Proceed to **7G** only after owner acknowledges this audit.
