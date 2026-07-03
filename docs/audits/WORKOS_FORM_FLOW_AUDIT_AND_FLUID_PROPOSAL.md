# WorkOS Form Flow Audit & Fluid Operator Proposal

**Date:** 2026-06-07  
**Type:** Audit + product/UX architecture proposal — **no runtime changes**  
**Branch:** `master` @ `1c626ff` (Volumetric Commercial Spine Finalization Pack committed)  
**Primary template:** `TPL-VOLUMETRIC-LETTERS`  
**Related prior audit:** `docs/architecture/INTAKE_TO_QUOTE_PROCESS_AUTOMATION_AUDIT.md`

---

## 1. Executive summary

The operator problem is real and localized: on **TPL-VOLUMETRIC-LETTERS intake detail**, the form feels **dead** because (a) SVG parse/layer status is easy to miss, (b) geometry still requires manual entry after vector upload, (c) **fast-ask Apply does not persist**, (d) readiness panels **list blockers without repair CTAs**, and (e) the same data is re-entered across intake spec, quote tab, and QuoteWizard.

The commercial spine (quote gate → convert → execution **201**) is **stabilized downstream**, but **upstream intake forms did not move with it**. Operators see improved quote readiness chips and demo routes while intake still behaves like a long accordion form.

**Single recommended direction:** adopt **staged operator workflows** — one visible stage at a time, every blocker maps to a field + scroll target + CTA, autosave on vector/metadata, explicit stage confirmation for production fields, and a **hardened handoff contract** into QuoteWizard / embedded simulate.

This document does **not** propose a visual redesign or Figma reskin. It proposes **operational form architecture**.

---

## 2. Current form inventory

| Form / Location | Purpose | Entity | Critical fields | Optional / deferred | Current problems | Downstream dependency |
|-----------------|---------|--------|-----------------|---------------------|------------------|----------------------|
| **NewIntakeDialog** (`NewIntakeDialog.tsx`) | Create intake | `intake_requests` | client, work type, description, channel, delivery | priority, contact details | No template confirm on create; `dimensions: "—"` legacy | IntakeDetail workspace routing |
| **WorkIntake list sidebar** (`WorkIntake.tsx`) | Pipeline triage | intake status, delivery | assignee (for some actions) | notes (required wrongly for mark-ready) | **Mark-ready navigates only**; rules ≠ IntakeDetail volumetric gate | IntakeDetail, draft quote create |
| **IntakeDetail orchestrator** (`IntakeDetail.tsx`) | Route generic vs modular | patches to intake row | `product_spec_json`, `site_audit_json`, `confirmed_template_code`, status | — | Dual paths (~2900 lines); legacy vs staged readiness disagree | Template workspace, `/quotes` nav (generic) |
| **VolumetricLettersWorkspace** | Modular shell | — | tab context | — | Quote tab open before spec saved | QuoteHandoffPanel |
| **TemplateConfirmationPanel** | Confirm template | `confirmed_template_code` | template code | — | Extra click after Quick Start already picked volumetric | Mark-ready legacy gate |
| **Product001IntakeSpecEditor** | Full product spec | `product_spec_json` | geometry, PSU, paint, mounting, vector metadata | production-only tags in §1 | **8 collapsed sections**; dual save model; §11 hidden in workspace | simulate-cost, quote_gate |
| **VectorIntakeFastAskPanel** | Vector pathway entry | spec vector fields | file, layer roles, 5 decisions | — | **Apply local-only**; parse MVP no area/perimeter; status buried | Geometry §3, readiness |
| **VectorStudioPanel** (§9) | Layer/review (manual path) | vector mappings | file, mappings, manual review | — | **Duplicate** of fast-ask on manual path; hidden on vector path | Backend vector gate |
| **TerrainRequirementPanel** | Install site audit | `site_audit_json` | address, photos, power when install | — | Correctly gated | Commercial readiness |
| **RequestContextPanel** | Client/assignee/delivery | `assigned_to`, `delivery_type` | assignee for mark-ready | — | Duplicates Quick Start delivery | Legacy readiness |
| **ReadinessGatePanel** | Mark ready + simulate CTA | status → `ready_for_quote` | legacy gate fields | staged list display | Simulate can show before commercial ready; mark-ready ≠ quote-ready | Quote list draft |
| **QuoteHandoffPanel → VolumetricLettersQuoteFlow** (embedded) | Simulate/price in intake | simulate/price APIs | saved spec snapshot | — | **Uses persisted spec only**; pricing margin/VAT hidden defaults | quotes row, quote_gate |
| **VolumetricLettersQuoteFlow** (standalone) | Full volumetric quote UX | quote via price API | quote_input fields | — | Re-edits intake fields locally; **not synced back** to spec | Quotes detail, convert |
| **QuoteWizard** (`QuoteWizard.tsx`) | Generic 4-step quote | quotes | client, template, quote_input, pricing | — | Volumetric delegates to flow; **SvgLayerAnalysisPanel only here**; possible missing import bug | Quotes, orders |
| **SvgLayerAnalysisPanel** | Paste SVG analyze (wizard) | none persisted | layer mapping | — | **Not in intake journey**; duplicate tooling | Wizard step 3 suggestions |
| **Quotes** (`Quotes.tsx`) | Quote lifecycle | quote status, convert | acknowledgement, convert guard | — | No quote edit form; readiness chip added (finalization pack) | Orders, execution |
| **Orders** (`Orders.tsx`) | Order display | — | — | — | Read-only; no forms | Execution |
| **ProductSystem** (`ProductSystem.tsx`) | Template studio | templates | components, ops, materials | calibration notes | Admin surface; drift from wizard field tables | CostEngine structure |
| **Pricing** (`Pricing.tsx`) | Registry admin | materials, rates | unit costs, gates | — | Not operator quote form | Indirect pricing |
| **Inventory** (`Inventory.tsx`) | Stock/OC | inventory entities | SKU, qty | — | Not in intake→quote path | Production |
| **Clients** (`Clients.tsx`) | Client search/KPIs | — | search | — | No client CRUD form | Navigation |
| **ClientWorkspace** | Client hub | — | filters | Facturi/Documente/Note **stubs** | Placeholder tabs | Intake/quote links |

---

## 3. Current operator journey (TPL-VOLUMETRIC-LETTERS)

| Step | UI state | Data source | Blocker / readiness | Operator must do | Next action obvious? | Persists? | Downstream uses it? | Friction |
|------|----------|-------------|---------------------|------------------|----------------------|-----------|---------------------|----------|
| 1 Open/create intake | WorkIntake + dialog | API / mock | — | Pick client, work type | Yes | Yes | Intake row | — |
| 2 Assign client/contact | Dialog + context panel | intake fields | — | Select client | Partial | Yes | Quote client_name | Contact not prefilled |
| 3 Confirm template | TemplateConfirmationPanel | `confirmed_template_code` | templateOk staged | **Extra confirm click** | No | On click | Gates, routing | Redundant after Quick Start |
| 4 Pathway select | IntakePathwaySelector | `intake_input_pathway` | — | Pick vector/manual/estimate | Yes | **Autosave** | Section visibility | OK post-841cc96 |
| 5 Upload SVG | VectorIntakeFastAskPanel | spec vector metadata | file validation | Pick file | Partial | **Autosave on attach** | Vector gate | Filename/layers may feel invisible if panel collapsed |
| 6 Parse / layers | Same panel | client `svgVectorAnalysis` + parser | role mapping | Map layer roles | Partial | Partial (file autosave; roles on apply/save) | Geometry hints, gate | **Parse status not prominent**; PERIMETER/AREA unsupported by design |
| 7 Fast ask (5 decisions) | VectorIntakeFastAskPanel | local answers | — | Answer dropdowns | Partial | **No — Apply is local** | Prefill sections | Feels like second form |
| 8 Geometry fields | Product001 §2–3 | spec | simulate readiness | **Manual area/perimeter/count** | **No** | Manual save | CostEngine quote_input | **Core pain: SVG doesn't unlock geometry** |
| 9 Production options | §4–8 | spec | final quote prep | Many scattered fields | No | Manual save | quote_gate metadata | Accordion overload |
| 10 Save spec | Footer button | API PATCH | — | Click Salvează | Unclear when needed | Yes | Quote tab reads this | Autosave vs manual confusion |
| 11 Simulate | Quote tab embedded flow | POST simulate-cost | `missingForSimulate` | Open tab, click simulate | Partial | No (response only) | quote_gate preview | **Unsaved spec ignored** |
| 12 Mark ready | ReadinessGatePanel | status patch | legacy gate | Mark gata | Partial | Yes | WorkIntake draft quote | **≠ commercial quote ready** |
| 13 Commercial quote | Same tab or Quotes | POST price | `can_create_commercial_quote` | Create quote | Better post-finalization | Yes | Quotes list chip | Downstream improved |
| 14 Ack warnings | Quotes detail | convert API | requires_acknowledgement | Checkbox | Yes (recent UX) | Yes | Order |
| 15 Convert → execution | Quotes / orders | convert + plan | execution validation | Convert | Yes (demo/E2E) | Yes | Execution 201 | Works on fixture paths |

**Honest broken/unclear points:**

1. **Fast-ask Apply without persist** — operator completes vector decisions, readiness still stale until manual Save.
2. **Geometry parser MVP** — bbox suggestions only; `PERIMETER_AREA_UNSUPPORTED_MSG` — operator must type metrics manually with weak visual link to SVG.
3. **Layer mapping unresolved** — UI shows roles but **no single “mapping complete” CTA** tied to readiness repair.
4. **Three readiness vocabularies** — `intakeReadiness.ts`, `intakeReadinessStages.ts`, `volumetricIntakeFormPrep.ts` (+ WorkIntake list rules).
5. **SvgLayerAnalysisPanel isolated in QuoteWizard** — intake operators never see equivalent paste-analyze unless they open wizard elsewhere.

---

## 4. Main problems (classified)

### A. Flow problems

- No staged stepper; all sections visible as collapsed accordions.
- Template confirmation separated from Quick Start volumetric selection.
- Quote tab reachable before spec saved — simulate fails opaquely.
- Readiness panels enumerate blockers without **scroll-to-field** or **Confirm stage** CTAs.
- WorkIntake “Marchează Gata” only navigates; uses different rules than volumetric detail.

### B. Data problems

- Fast-ask Apply → local React state only until manual Save.
- Standalone `VolumetricLettersQuoteFlow` edits not written back to `product_spec_json`.
- Legacy duplicate keys (`face_finish` / `face_finish_type`, `ral_color` / `paint_ral_code`, etc.).
- `intake_requests.dimensions` string parallel to spec mm fields (legacy noise).
- Vector analysis in wizard (`SvgLayerAnalysisPanel`) not persisted — separate from intake spec pipeline.

### C. Validation / readiness problems

- Mark-ready (legacy) allows envelope-only while commercial quote needs vector/Oracal/RAL.
- `missingForSimulate`, `isSimulateInputReady`, and staged simulate checks overlap but differ.
- Warning vs blocker distinction clear **downstream** (quote_gate) but **not upstream** at intake.
- Readiness side panel repeats status; does not drive repair sequence.

### D. UX / layout problems

- Technical vector metadata mixed with operator production decisions in one long form.
- Right panel shows chips/lists; main column does not highlight **current stage**.
- No bottom sticky **“Complete vector stage”** / **“Confirm geometry”** actions.
- Section 11 (quote prep hints) **hidden** in modular workspace slot.

### E. Domain / model problems

- TPL-VOLUMETRIC-LETTERS treated as generic accordion instead of **production pipeline stages**.
- SVG/layer mapping is core production input but UX treats it as optional fast-ask prefix.
- Vector pathway hides Vector Studio (§9) but manual pathway duplicates vector surfaces.

### F. Testability problems

- Commercial E2E starts at quote fixtures — **no intake SVG upload E2E**.
- Readiness tested downstream; intake form stages lack fixture + Playwright coverage.
- No single intake→quote E2E with real SVG file attach + layer map + simulate.

---

## 5. Proposed form principles

1. **Staged workflows, not long forms** — one primary working stage visible; completed stages collapse to summary chips.
2. **Backend authority for readiness** — UI displays and repairs; never invents `can_create_commercial_quote`.
3. **Every blocker is actionable** — code → human label → section → field id → CTA (scroll/focus/open file picker).
4. **Persist on meaningful boundaries** — autosave vector file, layer map, pathway; confirm-save on geometry/production batches.
5. **Single source of truth** — intake `product_spec_json` is canonical; quote tab reads live saved spec (+ optional read-only preview of dirty draft with banner).
6. **Progressive gates** — identity → vector → geometry → simulate → commercial metadata → quote handoff (align with existing `intakeReadinessStages` semantics).
7. **No duplicate surfaces** — one vector/layer UI on vector pathway; wizard SVG panel delegates to same contract or is removed from operator path.

---

## 6. Proposed staged form architecture (global pattern)

```
┌─────────────────────────────────────────────────────────────┐
│ Header: intake code · client · template · stage readiness   │
│ Primary CTA: Complete [current stage] / Open quote          │
├─────────────────────────────────────────────────────────────┤
│ Stepper: Context → Vector → Geometry → Production → Simulate│
├──────────────────────────────┬──────────────────────────────┤
│ Main working area            │ Repair panel                 │
│ (current stage fields only)  │ blockers + warnings          │
│                              │ next action + scroll targets │
├──────────────────────────────┴──────────────────────────────┤
│ Footer: Save status · Confirm stage · Run simulate            │
└─────────────────────────────────────────────────────────────┘
```

### State model (operator-visible)

| State | Meaning |
|-------|---------|
| `draft` | Identity only |
| `partially_complete` | Some stages done |
| `blocked` | Hard gate (missing required stage input) |
| `ready_for_simulation` | simulate-cost allowed |
| `ready_for_quote` | Intake status / legacy mark-ready |
| `ready_with_warnings` | Commercial allowed with warnings |
| `requires_acknowledgement` | Convert/quote gated on ack |
| `converted` | Order exists |

### Field classification

| Type | Examples | When required |
|------|----------|---------------|
| Identity/context | client, assignee, delivery | Before mark-ready |
| Template decision | confirmed template, pathway | Before vector stage |
| Vector/SVG | file, layer roles, review | Before commercial quote |
| Geometry | area, perimeter, count, depth | Before simulate |
| Production options | Oracal, RAL, PSU, mounting | Before commercial quote (warnings possible) |
| Commercial/pricing | margin, VAT (quote tab) | At price time |
| Readiness/validation | ack checkbox | At convert |
| Internal/admin | template studio | Admin routes only |

### Persistence rule

| Event | Persist |
|-------|---------|
| Pathway change | Immediate autosave |
| Vector file attach + analysis metadata | Immediate autosave |
| Layer role map confirmed | Immediate autosave on confirm |
| Fast-ask decisions applied | **Immediate autosave on Apply** (change from today) |
| Geometry batch confirmed | Autosave on “Confirm geometry” |
| Production options batch | Autosave on stage confirm or debounced |
| Full spec manual Save | Remains as safety net |

### Readiness repair rule

Each blocker record:

```typescript
{ code, label, stageId, fieldId, repairAction: "scroll" | "openFile" | "toggleAck" }
```

Repair panel sorted by stage order; primary CTA = first blocking stage.

---

## 7. TPL-VOLUMETRIC-LETTERS proposed screen structure

### A. Header

- Intake code, client, template badge, **current stage label**, aggregate readiness pill
- CTA: **Continue [stage]** or **Run simulation** when eligible

### B. Stepper (7 stages)

1. **Context** — assignee, delivery, description summary (read-mostly if from Quick Start)
2. **Product template** — auto-confirm when Quick Start = volumetric; pathway card
3. **Vector / SVG** — upload, parse status banner, detected layers table, role mapping
4. **Geometry & layers** — confirmed metrics + parser suggestions apply; manual fallback explicit
5. **Production options** — finish, paint, LED, mounting (grouped)
6. **Simulation readiness** — missing-for-simulate list + embedded simulate
7. **Quote handoff** — commercial gate summary + link to Quotes / open wizard

Completed stages: collapsed summary row (e.g. “Vector: logo.svg · letters layer mapped ✓”).

### C. Main working area

Only fields for **active stage**. No 8 accordions all closed.

### D. Right repair panel

- Blockers (red) with **Fix** buttons
- Warnings (amber) with acknowledge-at-quote note
- **Next action** sentence: “Upload SVG and assign letters layer to continue.”

### E. Bottom actions

- Save indicator (last saved / saving / error)
- **Confirm [Stage]**
- **Run simulation** (enabled when stage ≥ geometry complete)
- **Open quote wizard** (when commercial gate allows)

---

## 8. SVG / layer mapping proposed model

| Step | Operator sees | System does |
|------|---------------|-------------|
| Upload | File picker + immediate filename + size | Validate file; autosave metadata |
| Parse | Banner: parsing / success / failed + warning list | `analyzeSvgVectorFile` + `parseSvgGeometryFromFile` |
| Layers | Table: layer name, suggested role, dropdown | `svgLayerRoleSuggestion` preselect safe roles |
| Confirm mapping | **“Confirm layer mapping”** CTA | Persist `svg_layer_mappings`; set `layerMappingConfirmed` |
| Geometry hints | Read-only suggestions + **Apply to geometry** | Map bbox/count suggestions; **honest** that area/perimeter may remain manual |
| Review | Manual review toggle when parser incomplete | Sync to spec; feeds vector gate |
| Downstream | Quote tab shows vector summary read-only | Same mappings in CostEngine readiness |

**Non-negotiable honesty:** Until parser supports true letter metrics, UI must say **“Confirm letter area and perimeter manually — automatic extraction not available yet.”**

---

## 9. Readiness / validation proposed model

Unify operator-facing stages with backend gates:

| Stage gate | Frontend check | Backend check |
|------------|----------------|---------------|
| Simulate | `evaluateSimulationReadiness` only | simulate-cost readiness |
| Commercial quote | Show `quote_gate` from simulate/price | `ProductReadinessService` |
| Mark intake ready | Legacy + staged **merged display** — single list | intake status transition |
| Convert | Quotes panel | order conversion + ack |

**Single missing-items component** fed by:

1. Staged intake missing groups (field-level)
2. Backend `quote_gate.classified` (when simulate has run)

No fourth vocabulary on WorkIntake list — **delegate** to same evaluator or hide mark-ready on list for volumetric.

---

## 10. QuoteWizard handoff proposed model

**IntakeDetail / QuoteHandoff must pass (typed contract):**

```typescript
interface VolumetricQuoteHandoffPayload {
  templateCode: "TPL-VOLUMETRIC-LETTERS";
  intakeRequestId: string;
  intakeDbId: number;
  clientName: string;
  productSpec: IntakeProductSpec; // normalized saved snapshot
  vectorSummary: {
    fileName?: string;
    layerMappingConfirmed: boolean;
    analysisStatus?: string;
  };
  readinessContext?: {
    lastSimulateQuoteGate?: VolumetricQuoteGate;
    missingForSimulate: string[];
    missingForFinalQuote: string[];
  };
  deliveryType?: string;
  siteAudit?: IntakeSiteAuditJson;
  fromIntake: true;
}
```

**Rules:**

- Quote tab refuses simulate if `productSpec` save timestamp older than dirty editor — show **“Save spec first”** banner.
- Embedded mode: quote fields read-only; edits only in intake stages.
- Standalone `/quotes` wizard: prefill from handoff; edits optionally **offer sync back to intake** (future build).
- Remove duplicate SvgLayerAnalysisPanel from operator path OR implement as shared module writing to same spec fields.

---

## 11. Implementation roadmap (proposal only)

### Build 1: SVG Intake Upload + Layer Mapping + Geometry Persistence

**Goal:** Vector stage feels alive — parse visible, mapping persists, Apply autosaves.

**Likely files:** `VectorIntakeFastAskPanel.tsx`, `Product001IntakeSpecEditor.tsx`, `mapSvgGeometryToSpec.ts`, `IntakeDetail.tsx` save hooks.

**Acceptance:** File attach shows parse banner; Confirm mapping persists without full Save; fast-ask Apply persists; unit tests for persist paths.

**Tests:** Extend `svgGeometryParser.test.ts`, new component tests, manual smoke on WI-* volumetric.

**Risks:** Autosave race with manual edit — use revision counter.

**No-go:** CostEngine formulas, quote_gate policy changes.

---

### Build 2: Template Form Staged UX for TPL-VOLUMETRIC-LETTERS

**Goal:** Replace 8 accordions with 7-stage stepper + collapsed summaries.

**Likely files:** `VolumetricLettersWorkspace.tsx`, new `VolumetricIntakeStageStepper.tsx`, `ProductSpecEditorSlot.tsx`, `TemplateWorkspaceLayout.tsx`.

**Acceptance:** Only one stage expanded; header CTA matches stage; Quick Start auto-confirms template.

**Tests:** `VolumetricLettersWorkspace.test.tsx` stage navigation; Playwright smoke stage visibility.

**Risks:** Large UI diff — keep styling, change structure only.

**No-go:** Broad redesign of non-volumetric intakes.

---

### Build 3: Readiness Repair Panel + Field-to-Blocker Mapping

**Goal:** Every blocker clickable → scroll/focus; single missing-items feed.

**Likely files:** `ReadinessGatePanel.tsx`, `WorkspaceSidePanel.tsx`, new `IntakeRepairPanel.tsx`, `intakeReadinessStages.ts` (+ field id map).

**Acceptance:** Each code in `missingForSimulate` / staged groups has `fieldId`; repair panel Fix scrolls to field.

**Tests:** Unit map coverage; integration test with blocked fixture intake.

**No-go:** Changing backend blocker codes without migration plan.

---

### Build 4: QuoteWizard Handoff Contract Hardening

**Goal:** Typed handoff; saved-spec gate; remove wizard-only SVG duplicate from operator path.

**Likely files:** `QuoteHandoffPanel.tsx`, `VolumetricLettersQuoteFlow.tsx`, `Quotes.tsx`, `QuoteWizard.tsx`, new `volumetricQuoteHandoff.ts`.

**Acceptance:** Simulate blocked when spec unsaved; handoff payload tested; `humanizeQuoteBlocker` import fixed if still broken.

**Tests:** Handoff unit tests; commercial-live E2E unchanged PASS.

**No-go:** Pricing formula changes; new quote_gate semantics.

---

### Build 5: Full Intake-to-Quote E2E with SVG Fixture

**Goal:** Playwright path: create/open volumetric intake → attach fixture SVG → map layer → geometry → simulate → quote.

**Likely files:** `frontend/e2e/intake-volumetric-svg.spec.ts`, `backend/scripts/seed_*` optional minimal SVG fixture.

**Acceptance:** CI-ready spec with seed prerequisite documented.

**Tests:** New E2E + existing `test:e2e:commercial` still PASS.

**No-go:** Mock-only SVG that bypasses real parser.

---

## 12. Risks and boundaries

| Risk | Mitigation |
|------|------------|
| Staged UX breaks muscle memory | Keep deep links to stages; summary chips show completed data |
| Autosave conflicts | Optimistic UI + revision tokens |
| Parser expectations | Explicit copy that area/perimeter manual until parser v2 |
| Scope creep into CostEngine | Builds 1–5 touch UI/persistence/handoff only |
| Non-volumetric regression | Stage model behind `TemplateWorkspaceRouter` |

**Explicit no-touch (this proposal):** CostEngine, pricing formulas, quote_gate policy, execution validation, status lifecycle, inventory, unsupported templates, commercial spine E2E fixtures.

---

## 13. Open questions for owner decision

1. **Auto-confirm template** when Quick Start selects volumetric — always, or operator toggle?
2. **Area/perimeter automation** — invest in parser v2 vs keep manual with better UX?
3. **Standalone quote flow edits** — sync back to intake spec or read-only forever?
4. **Pricing controls in embedded quote tab** — expose margin/VAT or keep admin-only defaults?
5. **WorkIntake mark-ready** — remove for volumetric, fix rules, or hide until detail page?
6. **SvgLayerAnalysisPanel** — deprecate for volumetric or merge into intake vector stage?

---

## Appendix — Backend contracts (read-only reference)

| Area | Location |
|------|----------|
| Intake validation | `backend/validators/intake_product_spec.py` |
| Intake CRUD | `backend/routers/intake_requests.py` |
| Quote price + gate | `backend/routers/quotes.py` |
| Simulate | `backend/routers/product_system_cost_simulation.py` |
| Vector analyze | `backend/routers/vector_assets.py`, `backend/schemas/vector_assets.py` |
| Readiness DTO | `backend/schemas/product_readiness.py` |

Frontend canonical types: `intakeProductSpec.ts`, `volumetricQuoteInput.ts`, `volumetricQuoteReady.ts`, `volumetricQuoteFlowState.ts`.

---

## 14. Implementation note (2026-06-07)

**WorkIntake V2 staged flow** is implemented as a **parallel internal route** at `/intake-v2/:id` (`WorkIntakeV2.tsx`, `WorkIntakeV2Flow.tsx`). It applies the staged-operator model from §6 for **TPL-VOLUMETRIC-LETTERS only** — one active stage, repair panel with go-to-stage actions, explicit save boundaries into the same `product_spec_json`.

**Lighting & PSU (Etapa 5)** is **job-level**, not group-based: the normal UI has no „Grupuri iluminare” / „Adaugă grup”. The app proposes an automatic PSU combination (including multi-unit configs such as `2 × 160 W`); the operator confirms it. Manual PSU override lives in a collapsed advanced section. Named lighting-group / circuit planning is deferred as a future advanced feature — readiness checks job-level consumption and PSU only.

The existing `/intake/:id` route, `VolumetricLettersWorkspace`, and `Product001IntakeSpecEditor` **remain unchanged** as the production form. V2 is labeled *Intern / experimental* and linked optionally from the volumetric workspace; it does not replace WorkIntake or alter CostEngine, pricing, or the quote/order spine.
