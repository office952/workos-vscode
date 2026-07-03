# WorkOS Intake to Execution Operating Model

**Date:** 2026-06-07  
**Repo:** `workos-active`  
**Status:** Official architecture reference — audit-backed, no runtime changes  
**Audience:** Owner, operators, Cursor agents, developers  

**Related docs:**

- `docs/architecture/INTAKE_V4_REALITY_AND_UI_BOUNDARY.md`
- `docs/intake-v3/03_WORK_INTAKE_TO_QUOTES_ORDERS_PRODUCTION.md`
- `docs/architecture/VOLUMETRIC_COMMERCIAL_SPINE_STATUS.md`
- `docs/architecture/PRODUCTSYSTEM_TEMPLATE_ONBOARDING_PLAYBOOK.md`
- `docs/architecture/AI_INFORMATIONAL_LAYER_CONTRACT.md`
- `docs/architecture/TEMPLATE_SPECIFIC_FORM_ARCHITECTURE_AUDIT.md`
- `backend/data_models/product_contracts.py`

**Two complementary spines (same process, different granularity):**

```text
Operational spine (operator-facing):
  Capture → Interpret → Estimate → Draft Offer → Commercial Lock
         → Order Freeze → Plan → Execute → Reconcile

Canonical spine (code contracts):
  REQUEST → PRODUCT DEFINITION → COST → OFFER → ORDER
         → EXECUTION PLAN → EXECUTION REALITY
```

---

## 1. Purpose

This document fixes the **complete WorkOS process** from client request through production reality. It is the official rulebook for all future implementation in:

- Intake V6 Step 1 — module detection
- Intake V6 Step 2 — form + live price + stats
- Intake V6 Step 3 — confirm / handoff
- Product Form System
- Template Recommendation Engine
- AI SVG / Image Interpreter
- Future templates (ACM, bond, casetare, composite products)

**Why it exists:**

1. **Fix the full process** — name stages, handoffs, and ownership so nothing is implied.
2. **Separate preview from operational reality** — Intake estimates and simulates; Order and Execution Plan are real.
3. **Prevent mixing Intake / Pricing / Order / Execution** — each system has a bounded contract; crossing boundaries requires explicit operator confirmation and the correct stage.
4. **Be the base for Form System and AI Interpreter** — file analysis may *suggest* modules and forms; only confirmed operator input becomes Product Definition input.

**Non-goals:** Pixel UI spec, per-template costing formulas, activation of templates without owner onboarding, or changing runtime behavior via this document alone.

---

## 2. End-to-end flow

Nine operational stages. For each: **role**, **input**, **output**, **confirmer**, **may modify**, **must not do**.

### 2.1 Capture

| | |
|--|--|
| **Role** | Record the client request and open a workspace |
| **Input** | Client, channel, work type, description, priority, optional files |
| **Output** | Intake workspace (`IV6-*` or legacy intake entity), initial `product_binding` |
| **Confirmer** | Operator / sales |
| **May modify** | Client notes, assignee, delivery intent, file attachments |
| **Must not do** | Create order, execution plan, draft with binding commercial price, inventory moves |

**Implementation today:** `WorkIntake.tsx`, `IntakeV6OperatorWorkspaceApp`, `backend/models/intake_v6_workspace.py`.

---

### 2.2 Interpret

| | |
|--|--|
| **Role** | Analyze files; detect layers/modules; map semantics; recommend template/form |
| **Input** | SVG / image / PDF, analyzer report, layer names, geometry, paint evidence |
| **Output** | `detected_modules`, layer role candidates, warnings, `recommended_forms` / `recommended_templates` (suggestions only) |
| **Confirmer** | Operator confirms roles, modules, and template/form choice |
| **May modify** | Layer roles, module inclusion/exclusion, template binding until persisted |
| **Must not do** | Auto-confirm unknown layers as letter face; treat AI/OCR as production truth; create ProductDefinition or final price |

**Implementation today:** `frontend/src/lib/svgAnalyzer/`, `IntakeV6SvgAnalyzerStep`, artwork-only guard. **Target (Step 1):** formal `ModuleDetectionResult` contract.

---

### 2.3 Estimate

| | |
|--|--|
| **Role** | Configure product candidate; show live stats and **non-binding** cost preview |
| **Input** | Confirmed modules, form answers, finish setup, geometry, registry rates (where available) |
| **Output** | `product_definition_candidate`, `form_answers`, `pricing_preview`, technical stats, material breakdown (preview) |
| **Confirmer** | Operator confirms finish setup and material review boundaries |
| **May modify** | Finishes, commercial inputs, footprint overrides until Review confirm |
| **Must not do** | Apply breakdown to final quote; mutate stock; emit client-facing offer |

**Implementation today:** `IntakeV6ReviewStep`, material breakdown (`is_applied_to_quote=false`), `IntakeV6LiveCalculationSummary` (display). **Target (Step 2):** modular form from confirmed modules.

---

### 2.4 Draft Offer

| | |
|--|--|
| **Role** | Create internal draft quote boundary; link intake to Quotes module |
| **Input** | Handoff readiness pass, `pricing_input`, finish setup confirmed, explicit draft boundaries |
| **Output** | Draft `Quote`, `draft_offer_payload`, linkage (`intake_v6_linkage_v1`) |
| **Confirmer** | Operator: `confirm_no_order`, `confirm_no_execution`, `confirm_no_inventory`, internal draft confirmation |
| **May modify** | Draft quote metadata until priced |
| **Must not do** | Create order; create execution plan; deduct inventory |

**Implementation today:** `IntakeV6ConfirmStep`, `intake_v6_internal_draft_quote_policy_service.py`, `POST .../create-draft-quote`.

---

### 2.5 Commercial Lock

| | |
|--|--|
| **Role** | Bind commercial price and approvals before client acceptance |
| **Input** | Draft quote, QuoteWizard + CostEngine priced snapshot, readiness gates |
| **Output** | Priced quote, pricing review complete, owner approval, accept decision snapshots |
| **Confirmer** | Owner / commercial; operator for pricing review |
| **May modify** | Re-price while draft; re-acknowledge warnings |
| **Must not do** | Accept with stale `analysis_hash`; bypass missing-rate blockers for real quote |

**Implementation today:** V6 commercial spine — pricing review → owner approval → accept (`intake_v6_commercial_quote_service.py`).

---

### 2.6 Order Freeze

| | |
|--|--|
| **Role** | Immutable snapshot of what was sold |
| **Input** | Accepted priced quote |
| **Output** | Locked `Order`, `snapshot_line_items`, `readiness_snapshot`, traceability linkage |
| **Confirmer** | Convert guard with explicit confirmations (`confirm_no_execution_plan`, etc.) |
| **May modify** | **Nothing retroactive on snapshot** |
| **Must not do** | Recalculate cost on order row; create execution plan at convert time |

**Implementation today:** `intake_v6_quote_to_order_service.py`, `OrderSnapshot` in `product_contracts.py`.

---

### 2.7 Plan

| | |
|--|--|
| **Role** | Production plan from frozen order scope |
| **Input** | Order `snapshot_line_items` only |
| **Output** | `ExecutionPlan` with `tasks_json`, dependencies, estimated minutes |
| **Confirmer** | Explicit API / operator action (`POST .../plan/from-order/{id}`) |
| **May modify** | Plan regeneration per policy (order snapshot unchanged) |
| **Must not do** | Build plan from intake preview, draft quote, or task dry-run |

**Implementation today:** `execution_plan_service.py`, `execution_plan_gate_service.py`.

---

### 2.8 Execute

| | |
|--|--|
| **Role** | Run planned tasks on shop floor |
| **Input** | ExecutionPlan tasks, start gates (vector_prep, CNC, etc.) |
| **Output** | Task sessions, assignments, in-progress production state |
| **Confirmer** | Operator / shop floor via Employee Mobile or tablet |
| **May modify** | Task assignment and status within plan rules |
| **Must not do** | Start tasks from intake dry-run; mutate order snapshot |

**Implementation today:** `execution_task_assignment_service.py`, `task_start_gate_service.py`, Employee Mobile routes.

---

### 2.9 Reconcile

| | |
|--|--|
| **Role** | Capture reality vs plan; learn without rewriting commercial truth |
| **Input** | Actual time, observational materials, issues, divergences |
| **Output** | `ExecutionReality` records, divergence reports, optional future calibration inputs |
| **Confirmer** | Operators; review via Operational Reality UI |
| **May modify** | Reality rows (with invalidation/restore flows) |
| **Must not do** | Rewrite quote or order snapshot; auto-adjust accepted price |

**Implementation today:** `execution_reality_service.py`, `OperationalRealityReview.tsx`.

---

### 2.10 Flow diagram

```mermaid
flowchart LR
  CAP[Capture] --> INT[Interpret]
  INT --> EST[Estimate]
  EST --> DRF[Draft Offer]
  DRF --> CLK[Commercial Lock]
  CLK --> FRZ[Order Freeze]
  FRZ --> PLN[Plan]
  PLN --> EXE[Execute]
  EXE --> REC[Reconcile]
```

---

## 3. Canonical stage contracts

Mapping between **operational stages** and **canonical code spine**:

| Operational | Canonical | Primary artifact | Binding? |
|-------------|-----------|------------------|----------|
| **Capture** | **REQUEST** | Intake workspace, client context | No |
| **Interpret + Configure (Estimate prep)** | **PRODUCT DEFINITION (candidate)** | Confirmed modules, form answers, layer roles | Candidate until quote price |
| **Estimate (preview)** | **COST (preview)** | Material breakdown, live calc display | **No** |
| **Draft Offer + Commercial Lock** | **OFFER** | Draft → priced → accepted Quote | Yes at accept |
| **Order Freeze** | **ORDER** | `OrderSnapshot` locked | Yes |
| **Plan** | **EXECUTION PLAN** | `ExecutionPlan.tasks_json` | Yes (production scope) |
| **Execute + Reconcile** | **EXECUTION REALITY** | Time, materials, divergence | Observational |

**Product Definition (canonical)** is built at **quote pricing** via `ProductSystemService.build_product_definition(template, user_config)` — not as a standalone persisted entity today. Intake produces the **inputs** that become `user_config` / `pricing_input`.

**Cost (canonical)** authoritative path: `CostEngine` → `QuoteOrchestrator` → `QuoteCalculationSnapshot`. Intake breakdown is **not** this path.

---

## 4. Intake role

**Intake does not** directly produce an order or real execution.

### Intake does

| Responsibility | Description |
|----------------|-------------|
| Colectare cerere | Client, channel, work type, workspace |
| Analiză fișier | SVG/image/PDF → analyzer report |
| Detecție module | Layers, paths, colors, gradients, artwork candidates |
| Preview estimativ | Material breakdown, nesting, pricing_input preview, stats |
| Draft quote handoff | Policy-gated link to Quotes module |

### Intake does not

| Forbidden | Why |
|-----------|-----|
| Order snapshot | Requires accepted quote + convert |
| Execution plan real | Requires order snapshot |
| Mutare stoc | Production/inventory layer |
| Taskuri reale în DB | Dry-run and handoff preview only |
| Preț final fără Quote/Cost Engine | UI may display estimates; binding price is Quote path |

**Rule:** Intake is a **decision and handoff station**, not the commercial or production system of record.

**Reference:** `docs/architecture/INTAKE_V4_REALITY_AND_UI_BOUNDARY.md` (applies to V6 via shared services).

---

## 5. Intake V6 role

Intake V6 is the **active operator path** for volumetric letters (`TPL-VOLUMETRIC-LETTERS_v2`). Shell: `layers` → `review` → `confirm`.

### Step 1 — Analiză fișier / Detecție module *(current + target)*

| | |
|--|--|
| **Inputs** | SVG / image / PDF; optional AI suggestions (informational) |
| **Processing** | Parse layers, colors, paths, strokes, gradients; pseudo-layers; artwork detection |
| **Outputs** | `detected_modules[]`, layer role candidates, warnings, `recommended_forms` / `recommended_templates` |
| **Confirmer** | Operator — every module/layer role explicit |
| **Must not** | Confirm-all → face for non-letter content; auto template switch |

**Current code:** `IntakeV6SvgAnalyzerStep`, `svgAnalyzer`, `intakeV6ArtworkOnlyGuard.ts`.  
**Target contract:** `ModuleDetectionResult` persisted alongside analysis bundle.  
**Foundation (v1):** See [MODULE_DETECTION_RESULT_CONTRACT.md](./MODULE_DETECTION_RESULT_CONTRACT.md) — typed contract + pure mapper in `frontend/src/lib/intakeV6/moduleDetectionResult.ts`; not yet UI source of truth.

### Step 2 — Configurare și calcul *(current + target)*

| | |
|--|--|
| **Inputs** | Confirmed modules, template form contract, finish options |
| **Processing** | Modular form from confirmed modules; live price display; technical stats |
| **Outputs** | `product_definition_candidate`, `form_answers`, `pricing_preview`, `stats` |
| **Confirmer** | Operator confirms `finish_setup` |
| **Must not** | Treat live calc as final quote; auto-save false letter groups |

**Current code:** `IntakeV6ReviewStep`, `template-form-contract`, letter/artwork finish sections.  
**Target:** Product Form System drives form shape from confirmed modules.

### Step 3 — Confirmare / Handoff

| | |
|--|--|
| **Inputs** | Readiness status, handoff preview, fatal blockers |
| **Processing** | Verify what **will** and **will not** be created |
| **Outputs** | `draft_offer_payload`, `handoff_readiness`, optional draft quote creation |
| **Confirmer** | Operator explicit boundaries + internal draft confirmation |
| **Must not** | Imply order/execution/inventory creation |

**Current code:** `IntakeV6ConfirmStep`, `intake_v6_internal_draft_quote_policy_service.py`.

### Intake V6 handoff artifact summary

| Artifact | Binding? |
|----------|----------|
| `product_definition_candidate` | Candidate until QuoteWizard prices |
| `confirmed_modules` / layer roles | Required for handoff |
| `form_answers` / `finish_setup` | Persisted in workspace payload |
| `pricing_preview` | **Non-binding** |
| `handoff_readiness` | Gate |
| `draft_offer_payload` | Creates draft only after policy pass |

---

## 6. Product Definition role

Product Definition composes the **technical product** from confirmed modules and template rules.

### Responsibilities

- Layers, materials, processes, dimensions, validation
- Supports **composite products** (multiple modules/templates) as a future capability
- Contract-first: `ProductDefinition` in `product_contracts.py`

### Rules

| Rule | Detail |
|------|--------|
| Does not calculate final price | No cost figures on `ProductDefinition` |
| Does not create order | Quote → convert chain only |
| Does not start execution | Order → plan chain only |
| Contract-first | DTO exchanged ProductSystem → CostEngine → Quotes → Order |
| Built at quote time today | `ProductSystemService.build_product_definition()` |

**Persistence today:** Embedded in quote `line_items` → frozen in order snapshot. **Not** a standalone persisted stage (gap P2).

---

## 7. Product Form System role

*(Target architecture — partially present via `template-form-contract`)*

### Principles

1. **Template declares requirements** — dossier / form schema per `template_code`
2. **Form System builds the form** — fields, sections, conditional visibility from confirmed modules
3. **File may activate modules** — detection suggests; operator confirms
4. **Form may recommend another form/template** — suggestion only; operator confirms switch
5. **Operator always confirms** — no auto-apply of form or template changes

### Canonical pipeline

```text
Layer name / geometry / AI suggestion
  → Semantic Layer Registry (map layer semantics → module ids)
  → Form modules required (template + activated modules)
  → Operator confirmation
  → Product Definition (at quote price)
  → Cost Engine
```

### Relationship to Intake V6 steps

| Step | Form System role |
|------|------------------|
| Step 1 | Suggest modules and form fragments from detection |
| Step 2 | Render confirmed modular form; collect `form_answers` |
| Step 3 | Validate completeness against handoff policy |

**Reference:** `docs/architecture/TEMPLATE_SPECIFIC_FORM_ARCHITECTURE_AUDIT.md` — registry gap documented; volumetric form wired by family string today.

---

## 8. Template Recommendation Engine role

*(Target architecture — not a standalone service today)*

When detected modules **do not fit** the current template/form, the system **recommends** options; it **never auto-switches**.

### Recommendation types

| Option | Example |
|--------|---------|
| Keep current form; exclude element | Litere volumetrice + layer ACM → exclude ACM from scope |
| Add optional module | Litere + policromie artwork section |
| Switch template/form | File is primarily ACM panel, not letters |
| Composite form | Litere pe suport ACM; panou decupat + litere aplicate |

### Example

| Context | Detection | Recommendations |
|---------|-----------|-----------------|
| Template: **Litere volumetrice** | Layer `acm-decupat` | 1) Litere volumetrice pe suport ACM 2) Panou ACM decupat + litere aplicate 3) Păstrează Litere volumetrice; exclude ACM |

### Rules

- Recommendations are **informational** until operator selects and confirms
- Template switch requires explicit confirmation and workspace rebinding policy
- Mismatch without decision → **blocked handoff** (fail-closed)

**Current partial behavior:** artwork-only guard, out-of-scope layer warnings, template binding at workspace create.

---

## 9. Pricing role

| Layer | Authority | Role |
|-------|-----------|------|
| **Intake material breakdown** | Preview / informative | Layout, nesting, missing-rate visibility; `is_applied_to_quote=false` |
| **Intake live calc UI** | Display only | Must not become source of truth |
| **Cost Engine** | **Canonical cost** | Materials, labour, machine, external, overhead from ProductDefinition + registry |
| **QuoteOrchestrator** | **Canonical commercial** | Margin, VAT, net/gross on top of CostResult |
| **Commercial gate** | Blocker | `can_create_commercial_quote`, warn-ack, missing rates |

### Rules

- **UI does not calculate authoritative cost** — may show estimates aligned with preview APIs
- **Missing rates block real quote** — fail-closed; owner fills registry
- **Currency must be preserved** in handoff and snapshot (partial: Orders table lacks currency column — gap P2)

**Implementation:** `cost_engine_service.py`, `quote_orchestrator.py`, `volumetric_quote_ready_policy.py`.

---

## 10. Offer / Quote role

### Offer / Quote

- Commercial document backed by Cost Engine snapshot
- Lifecycle: draft → priced → accepted (V6 commercial spine)
- May start as **internal draft** from Intake Step 3
- Requires: pricing review, owner approval, accept (with explicit confirmations)

### Draft quote boundaries

| Draft quote **does not** | |
|--------------------------|---|
| Create order | Convert is separate after accept |
| Create execution plan | Plan is post-order explicit action |
| Mutate stock | Inventory is production layer |

**Implementation:** `Quotes.tsx`, `QuoteWizard`, `intake_v6_commercial_quote_service.py`, `create-draft-quote` endpoint.

---

## 11. Order role

Order appears **after offer acceptance** and **freezes** the commercial and technical snapshot.

### Immutable after convert

- `snapshot_line_items` — product definition, cost result, quote snapshot, handoff embeds
- `readiness_snapshot` — traceability at convert time
- Commercial totals — not retroactively changed when registry rates change later

### Traceability linkage

| Key | Location |
|-----|----------|
| `intake_v6_linkage_v1` | Quote notes |
| `intake_v6_order_linkage_v1` | Order notes |
| `client_analysis_hash` | Handoff guards (SVG identity sync) |
| `IV6-{workspace_id}` | Workspace intake code |

**Implementation:** `intake_v6_quote_to_order_service.py`, `order_snapshot_service.py`.

---

## 12. Execution Plan role

| Rule | Detail |
|------|--------|
| Generated **explicitly** from Order Snapshot | `POST .../plan/from-order/{id}` |
| **Not** from Intake | Preview ≠ plan |
| **Not** from draft quote | No production scope without order |
| Produces **planned tasks** | Real DB entity |

### Preview vs real (Intake)

| Intake artifact | Contract |
|-----------------|----------|
| Production handoff preview | `preview_only=true`, no DB writes |
| Task generation dry-run | Simulate candidates only |
| Order-bound task readiness | Informational gate before plan exists |

**Implementation:** `execution_plan_service.py`; intake previews in `intake_v6_production_handoff_preview_service.py`.

---

## 13. Execution Reality role

Captures **what actually happened**:

- Real time (start/end task)
- Observational materials
- Problems and divergences

### Rules

- **Does not rewrite** offer or order snapshot
- **May inform** future template rules, rates, or estimates — not retroactive pricing
- **Does not deduct inventory** by itself (separate inventory layer)

**Implementation:** `execution_reality_service.py`, `/execution/reality-review`.

---

## 14. Safety rules

Firm rules for all implementations:

| # | Rule |
|---|------|
| 1 | **UI does not calculate cost** — Cost Engine + QuoteOrchestrator are authoritative |
| 2 | **AI does not decide without operator** — suggestions only; `requires_confirmation=true` |
| 3 | **SVG does not auto-create complete product** — detection → confirmation → definition |
| 4 | **File may request modules, not automatic price** — modules suggest form fragments; price follows ProductDefinition + Cost Engine |
| 5 | **Form may recommend another form, not auto-switch template** — operator confirms template change |
| 6 | **Draft quote does not create order** |
| 7 | **Order snapshot is immutable** |
| 8 | **Execution plan created only from order** |
| 9 | **Intake preview is not execution reality** |
| 10 | **Missing data = fail closed / blocked** — no silent defaults (`product_contracts.py`) |
| 11 | **Template mismatch requires operator confirmation** — artwork-only, ACM on letters template, etc. |
| 12 | **Analysis hash sync** — stale intake invalidates downstream commercial confirmations |
| 13 | **Geometria calculează. Regulile validează. AI interpretează. Operatorul confirmă.** |

---

## 15. Current implementation map

Audit-backed snapshot (2026-06-07). **Complete** = production-ready for TPL-VOLUMETRIC-LETTERS fixture paths unless noted.

### Intake

| Component | Status | Paths |
|-----------|--------|-------|
| V6 operator path | **Complete** (pilot) | `frontend/.../intake-v6/`, `backend/routers/intake_v6_workspaces.py` |
| V4 backend | Registered; UI → V6 | `backend/routers/intake_v4_workspaces.py` |
| V3 | Partial preview chain | `backend/services/intake_v3_*` |
| V5 | Experimental | `backend/services/intake_v5_service.py` |
| Classic IntakeDetail | Legacy non-volumetric | `IntakeDetail.tsx`, redirect volumetric → V6 |

### Product System

| Component | Status | Paths |
|-----------|--------|-------|
| Product contracts | Complete | `backend/data_models/product_contracts.py` |
| ProductSystemService | Complete at quote-time | `backend/services/product_system_service.py` |
| TPL-VOLUMETRIC-LETTERS_v2 | Complete (reference template) | Playbook + dossier |
| Template binding in intake | Complete volumetric | `intake_v6_product_system_service.py` |
| Form registry | **Partial** | `template-form-contract`; no full Form System |

### Pricing

| Component | Status | Paths |
|-----------|--------|-------|
| QuoteOrchestrator | Complete | `backend/services/quote_orchestrator.py` |
| CostEngine | Complete volumetric | `backend/services/cost_engine_service.py` |
| Intake material breakdown | Preview only | `intake_v6_material_breakdown_service.py` |
| Commercial gate | Complete fixture paths | `volumetric_quote_ready_policy.py` |

### Quote / Offer

| Component | Status | Paths |
|-----------|--------|-------|
| Draft quote from V6 | Complete guarded | `create-draft-quote`, Confirm step |
| QuoteWizard | Complete volumetric | `QuoteWizard`, `VolumetricLettersQuoteFlow` |
| Commercial spine | Complete fixture paths | V6 accept/convert endpoints |
| Client PDF/send | Partial | `quote_document_service.py` |

### Order

| Component | Status | Paths |
|-----------|--------|-------|
| Immutable snapshot | Complete | `OrderSnapshot`, convert service |
| V6 quote-to-order | Complete | `intake_v6_quote_to_order_service.py` |
| Currency on Orders row | **Missing** | Snapshot JSON only |

### Execution

| Component | Status | Paths |
|-----------|--------|-------|
| ExecutionPlan from order | Complete fixture paths | `execution_plan_service.py` |
| Task dry-run (intake) | Preview | `intake_v6_task_generation_dry_run_service.py` |
| Production handoff preview | Preview | `intake_v6_production_handoff_preview_service.py` |
| Dependency gates | Complete MVP | `task_start_gate_service.py` |

### Execution Reality

| Component | Status | Paths |
|-----------|--------|-------|
| Start/end task | Complete | `execution_reality_service.py` |
| Observational materials | Complete | Reality materials API |
| Reality review UI | Complete | `OperationalRealityReview.tsx` |

---

## 16. Current gaps

Prioritized from audit and regression matrix. **P0 only if real blocker exists.**

### P0

| Gap | Notes |
|-----|-------|
| *(none listed)* | No universal P0 blocker on volumetric fixture spine; document gaps below are P1–P3 |

### P1

| Gap | Impact |
|-----|--------|
| **Missing `Serviciu print` rate** | Case 3 mixed letters + policromie — PARTIAL until registry filled |
| **Parser / group names for non-path elements** | e.g. `<g id="artwork-policromie">` collapses to `unassigned`; operator sees wrong layer name |
| **Multi-template product families** | Operator path scoped to volumetric; ACM/bond/casetare not onboarded |

### P2

| Gap | Impact |
|-----|--------|
| **V4/V6 namespace debt** | `intakeV4*` inside `intakeV6/`; compat import fragility |
| **ProductDefinition not persisted standalone** | Hard to audit pre-quote product composition |
| **Orders.currency column missing** | Currency only in snapshot JSON |
| **Unified readiness partial** | V3/V4/V6 policy + display stages overlap |
| **Product Form System not formalized** | Template-form-contract exists; no module-driven form registry |
| **Template Recommendation Engine not built** | Partial guards only (artwork-only, scope warnings) |

### P3

| Gap | Impact |
|-----|--------|
| **Stale WorkIntake V2 doc** | `VOLUMETRIC_WORKINTAKE_V2_MIGRATION_BOUNDARY.md` — no code |
| **V3/V5 parallel backends** | Confusion risk for agents |
| **Print file / document blocking gates** | Partial/deferred |
| **Zero-minute formula ops** | No plan tasks emitted |
| **Corel complex SVG layer collapse** | `pbl-complex` — analyzer fidelity |

---

## 17. Recommended next steps

Ordered sequence before AI Interpreter and complex templates:

| # | Action | Rationale |
|---|--------|-----------|
| 1 | **Close pricing config gap: `Serviciu print`** | Unblocks mixed letter + artwork cases (P1) |
| 2 | **Preserve group/layer names for non-path elements** | Operator trust in Step 1 detection |
| 3 | **Formalize Step 1 = `ModuleDetectionResult` contract** | Stable handoff to Form System |
| 4 | **Define Product Form System contract** | Template schema → modular form → `form_answers` |
| 5 | **Define Layer Semantic Registry** | Map layer names/geometry → module ids |
| 6 | **Define Template Recommendation Engine** | Mismatch options with operator confirm |
| 7 | **Then: AI SVG/Image Interpreter** | Informational only; plugs into Step 1 suggestions |
| 8 | **Future templates (owner onboarding each)** | ACM / bond / casetare; litere pe suport ACM; cut and glow; composite product forms |

Each new template must complete `PRODUCTSYSTEM_TEMPLATE_ONBOARDING_PLAYBOOK.md` chain before operator activation.

---

## Appendix — Quick reference for implementers

**Before changing Intake V6:** Read §4, §5, §14.  
**Before Form System:** Read §7, §3, `TEMPLATE_SPECIFIC_FORM_ARCHITECTURE_AUDIT.md`.  
**Before AI:** Read §14, `AI_INFORMATIONAL_LAYER_CONTRACT.md`.  
**Before new template:** Read §8, `PRODUCTSYSTEM_TEMPLATE_ONBOARDING_PLAYBOOK.md`.  
**Before commercial change:** Read §9–11, `VOLUMETRIC_COMMERCIAL_SPINE_STATUS.md`.

---

*End of document.*
