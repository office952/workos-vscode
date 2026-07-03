# BUILD: Intake V4 — Atoms Operator Workspace (clean shell + SVG Analyzer)

**Date:** 2026-06-20  
**Status:** Phase 1 complete — hydrate reload, readiness gates (V2 pattern), Step 3 guard stub  
**Last audit:** 2026-06-22
**Reference UI:** `docs/reference/intake-v3-operator-workspace-smart.html` (Atoms Smart Workspace)  
**Reference analyzer:** `C:\Users\offic\Desktop\nest2` (`analyzeSvgString`, layer roles, parts, nesting)

---

## 1. De ce V4 (nu mai patch pe V3)

V3 acumulează straturi incompatibile:

| Problemă | Cauză |
|----------|--------|
| Header `pbl.svg · 0 KB` după upload complex | `rawSvgAnalysis`, `vector_asset`, `sessionStorage` preview — 3 surse |
| Step 3 arată date vechi | View model derivat din state parțial actualizat + refresh async |
| Layer Publi/Media rămân | Backend merge roles când keys identice; UI nu forțează invalidare vizuală |
| UX fragmentat | Tab-uri vechi + 3-step + technical route + lazy panels |

**V4** = un singur flux operator, un singur store, UI Atoms, analiză SVG ca în nest2.

---

## 2. Principii V4

1. **Un singur source of truth în UI** — reducer central; la upload/replace se golește tot state-ul dependent (pattern `analysisRunRef` din nest2).
2. **Atoms layout fix** — smart banner → header → progress 1-2-3 → status bar → content (max 920px) → footer fix.
3. **SVG Analyzer first** — parse + layer draft client-side imediat; apoi persist backend (fail-closed).
4. **Backend V3 reutilizat** — guards, quote dry-run, layer role PUT, workspace payload — fără CostEngine/inventory mutations noi.
5. **V2 patterns** — operational header, template config, readiness handoff, finish display (read-only unde e cazul).
6. **Fără** — voice, copilot, confetti, light theme (Atoms decorative, out of scope).

---

## 3. Arhitectură

```text
┌─────────────────────────────────────────────────────────────┐
│  IntakeV4OperatorWorkspaceApp                               │
│  ├─ AtomsShell (banner, header, progress, status, footer)   │
│  ├─ Step: Layers  → preview + layer chips + role setup      │
│  ├─ Step: Review  → geometry, lighting, materials (expand)  │
│  └─ Step: Confirm → quote guard, summary                     │
└─────────────────────────────────────────────────────────────┘
         │ dispatch                    │ persist
         ▼                             ▼
┌──────────────────────┐    ┌──────────────────────────────┐
│ intakeV4Workspace    │    │ intakeV4Api.ts               │
│ Reducer (UI truth)   │───▶│ → /api/v1/intake-v4/*        │
└──────────────────────┘    └──────────────────────────────┘
         ▲
         │ analyzeSvgString (port nest2 → lib/svgAnalyzer)
         └─ client-side immediate feedback on file pick
```

### Route

- Operator (shell): `/intake-v4/:workspaceId/operator`
- Operator (standalone, no sidebar): `/intake-v4-app/:workspaceId/operator`
- Bootstrap preserves route prefix (`intakeV4OperatorRoutes.ts`)
- Hub list: `/intake-v4` (later — reuses V3 workspace list initially)

### State machine (UI)

```text
idle → loading_workspace → ready
ready → analyzing_svg → svg_ready → saving_layers → ready
any → error
```

La `analyzing_svg`: **clear** preview, layers, confirmed model refs, file metadata — apoi set new analysis atomically.

---

## 4. Ce reutilizăm vs reconstruim

| Layer | V4 approach |
|-------|-------------|
| **UI shell** | Nou — Atoms tokens + components în `intake-v4/` |
| **State** | Nou — reducer, fără sessionStorage pentru metadata |
| **SVG parse** | Port nest2 `analyzer/` → `frontend/src/lib/svgAnalyzer/` (Phase 1) |
| **Workspace CRUD** | Propriu — `/api/v1/intake-v4/*`, payload V4 |
| **SVG upload** | V4 endpoint; reutilizează libs SVG V3 (parse/geometry), nu API V3 |
| **Task preview** | ProductSystem operations + finish gates (`intake_v4_product_system_service`) |
| **V2 finish display** | Read-only panel în Review step (Phase 3) |
| **nest2 DXF/nesting** | Technical drawer only (Phase 4) |

---

## 5. Faze

### Phase 0 — Scaffold (acest build)

- [x] BUILD doc
- [x] Route + empty Atoms shell
- [x] Reducer + upload clears stale state
- [x] Adapter stub to V3 workspace GET

### Phase 1 — Backend foundation + SVG (acest build)

- [x] Schema + ORM `intake_v4_workspaces`
- [x] Services: workspace CRUD, SVG upload, layer roles, PS binding, task preview
- [x] Router `/api/v1/intake-v4`
- [x] Frontend `intakeV4Api.ts` (decoupled from V3)
- [x] Drag-and-drop + nest2-style client-first read
- [x] **Step 1 = nest2 SVG Analyzer engine** (`IntakeV4SvgAnalyzerStep`, `intakeV4ClientSvgImport`)
- [x] **Step 2 partial** — finish setup form + task preview API (`IntakeV4ReviewStep`)
- [ ] **Step 2 complete** — materials/geometry lazy panels, V2 finish display read-only
- [ ] **Step 3** — quote guard + commercial handoff (`IntakeV4ConfirmStep` stub)

---

## 8. Arhitectură țintă (decizie operator — 2026-06-22)

**Da — propunerea e corectă.** V4 nu trebuie să reinventeze analiza SVG.

```text
Pas 1 — SVG Analyzer (nest2, 100% client)
  analyzeSvgString → layers, geometry, parts, nesting, layer roles
  UI: preview + layer table + confirm roles (ca nest2)
  Handoff: buildOfficialAnalysisJson() → salvează în intake_v4 payload

Pas 2 — Operator settings (WorkOS + ProductSystem)
  template_code: TPL-VOLUMETRIC-LETTERS (header, task preview, gates)
  finish: 651/8500/cant/LED/policromie (din V2 logic)
  review + confirm + quote guard

Pas 3 — Confirm / handoff quote
```

**Ce NU facem:** iframe nest2 separat, re-upload V3 backend ca sursă de adevăr, parseSvgLayersQuick ca substitut.

**Ce facem:** copiem `nest2/src/analyzer` (+ part-extractor minim) în `frontend/src/lib/svgAnalyzer/` ca pachet shared; Step 1 = componentă `IntakeV4SvgAnalyzerStep` (fork SvgAnalyzerPage).

**Contract persistență V4 payload:**

| Câmp | Sursă |
|------|--------|
| `svg_analysis_json` | nest2 official JSON |
| `layer_role_setup` | derivat din layerRoleConfirmation |
| `product_binding` | TPL-VOLUMETRIC-LETTERS |
| `finish_setup` | operator Pas 2 |

### Phase 2 — Review + Confirm

- Geometry/lighting/materials via V3 lazy APIs (single load per step)
- Confirm step: quote guard, summary rows
- Smart banner next-action from reducer

### Phase 3 — V2 parity features

- Finish display read-only
- Template-specific fields (TPL-VOLUMETRIC-LETTERS)
- Handoff link to QuoteWizard when ready

### Phase 4 — Technical drawer (nest2 tools)

- Parts table, nesting preview, bond DXF export
- Collapsed by default; `/intake-v4/:id/technical`

---

## 6. Fișiere Phase 0

| Path | Rol |
|------|-----|
| `docs/qa/BUILD_INTAKE_V4_ATOMS_OPERATOR_WORKSPACE.md` | Contract |
| `frontend/src/pages/IntakeV4OperatorWorkspaceApp.tsx` | Entry |
| `frontend/src/lib/intakeV4/intakeV4WorkspaceReducer.ts` | UI state |
| `frontend/src/lib/intakeV4/useIntakeV4Workspace.ts` | Hook |
| `frontend/src/lib/intakeV4/intakeV4ApiAdapter.ts` | V3 bridge |
| `frontend/src/components/workos/intake-v4/atoms/*` | Shell UI |

---

## 7. Validare

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/lib/intakeV4/
```

Manual: `/intake-v4/{workspaceId}/operator` — upload pbl-complex.svg → header + summary trebuie să arate același fișier și 5 straturi.

### Post-Open race fix (2026-06-22)

- **Symptom:** dialog OK, dar după Open preview/nume fișier dispăreau.
- **Cause:** `LOAD_SUCCESS` rescria state din payload server gol după `ANALYZER_READY`.
- **Fix:** `preserveLocalAnalyzerState` în `intakeV4WorkspaceReducer.ts`.
- **E2E:** `pnpm test:e2e:intake-v4-open` (stack live, `PW_SKIP_WEB_SERVER=1`).

### Auth focus fix (2026-06-22)

- **Symptom:** browse Open / tab switch ștergea workspace-ul (spinner „Se verifică sesiunea…”).
- **Fix:** `refreshAuthSilently` în `AuthContext.tsx` — fără `loading=true` după mount inițial.
- **Scope:** global WorkOS (V2/V3/V4 beneficiază); nu e patch V4-specific.

### Import paths unificate (2026-06-22)

| Path | Componentă | Handler |
|------|------------|---------|
| Browse | `IntakeV4Nest2SvgUploader` | `hook.importSvgFile` → `analyzeSvgFileForIntakeV4Client` |
| Drag-drop | `IntakeV4OperatorWorkspaceFileDrop` | același `hook.importSvgFile` |
| Persist | Next din Step 1 | `continueFromAnalyzer` → `PUT /analysis-bundle` |

E2E drag-drop: al treilea test din `intake-v4-svg-open-after-bootstrap.spec.ts`.

### Ce rămâne (prioritate)

1. **Hydrate reload** — la refresh, reconstituie preview/layers din `svg_analysis_json` persistat.
2. **Phase 2** — quote guard, confirm summary complet, smart banner next-action.
3. **Phase 3** — V2 finish display read-only în Review.
4. **Phase 4** — technical drawer (parts, nesting, DXF).
5. **Hub** — `/intake-v4` listă workspace-uri.
6. **Cleanup** — ~~șterge `IntakeV4LayersStep.tsx`~~ done; ~~diagnostics dev~~ removed.
7. **Quote handoff** — Confirm step shows readiness + ProductSystem blockers; `Open QuoteWizard` API Phase 2.

### Sprint 1 — V2 / V3 alignment (2026-06-22)

- [x] `intake_v4_finish_adapter.py` — V4 `finish_setup` → V3 `FinishAssignment` (per-layer groups)
- [x] `derive_operation_flags_from_v4_finish()` — OR flags across all letter groups
- [x] `intake_v4_production_preview_service.py` — task preview via `build_task_seed_candidates()` (V3 catalog)
- [x] Task preview API returns `operation_catalog` seeds + `operation_flags` + `preview_engine`
- [x] Sprint 2 — pricing_input adapter + production dry-run endpoint
  - `intake_v4_pricing_input_service.py` → `GET /pricing-input-preview`
  - `intake_v4_production_task_dry_run_service.py` → `GET /production-task-dry-run` (V3 response shape)
  - Review step: `IntakeV4PricingInputPanel` + reuse `IntakeV3ProductionTaskDryRunPanel`
  - Tests: `test_intake_v4_pricing_input.py`, `TestIntakeV4Sprint2Previews` — **23/23** backend V4 targeted
- [x] Sprint 3 — quote handoff bridge
  - `intake_v4_commercial_quote_service.py` → `POST /create-draft-quote` (snapshot + IV4 linkage)
  - Confirm step: guarded checkboxes + navigate QuoteWizard cu `quote_input` prefill
  - Artwork volumetric în material breakdown (`separate_emblem` → plexi + cant emblemă)
  - Tests: `test_intake_v4_commercial_quote.py`, `test_intake_v4_material_breakdown.py` artwork — **5/5** targeted


- Backend persist `svg_source_text` în payload la `PUT /analysis-bundle`.
- Frontend `intakeV4PayloadHydrate.ts` — reconstituie report, roles, preview, step din `readiness_status`.
- Pattern V2: server = source of truth on reload; local state preserved only during active analyze/persist.

---

## 8. Boundary (protected)

- Nu modificăm CostEngine, inventory mutation, quote pricing logic
- Nu activăm ACM fără build dedicat
- V3 rămâne funcțional — V4 e rută paralelă până la cutover

---

## 9. Scope produse (decizie operator — 2026-06-22)

### În scope V4 (acum)

| Produs | Template ProductSystem | Note |
|--------|------------------------|------|
| **Litere volumetrice** | `TPL-VOLUMETRIC-LETTERS` | Pilot activ — singurul template V4 wired end-to-end |
| **Logo / emblemă** (volumetric front-lit) | Același `TPL-VOLUMETRIC-LETTERS` | Roluri SVG `face` / `logo` / `printed_artwork`; finisaje per grup ca V2 |

### Standby — **nu implementăm, nu selectăm în UI**

| Produs | Template | Motiv |
|--------|----------|--------|
| **ACM bond casetat** | `TPL-ACM-CASSETTED-PANEL` | Așteaptă șablon ProductSystem dedicat + build separat |
| **Litere slogan** | (TBD în ProductSystem) | Out of scope până la șablon PS |

Guardrails: workspace V4 create doar cu `TPL-VOLUMETRIC-LETTERS`; fără dropdown template; fără layer→ACM mapping.

### Finisaje de aliniat cu V2 (per șablon activ)

Pentru `TPL-VOLUMETRIC-LETTERS`, Step 2 Review trebuie să acopere aceleași câmpuri ca V2 `V2ProductionStage` + `V2LightingStage`:

| Câmp V2 (`IntakeProductSpec`) | V4 `finish_setup` (extindere) | Sursă adevăr |
|-------------------------------|------------------------------|--------------|
| Față Oracal 651 / 8500 / policromie | `face_finish_type` (+ cod culoare per grup) | Registry Oracal + `letter_group_finishes` |
| Cant / return Oracal / RAL | `return_finish_type` + `return_depth_mm` | Per grup + global fallback V2 |
| Iluminare on/off | `illuminated` | `illumination_family` |
| Tip LED (modul / bandă) | `lighting_system_type` | `lightingPlanning.ts` |
| Temperatură culoare LED | `light_color` | V2 lighting stage |
| Consum + PSU | `required_psu_watts`, `psu_configuration` | `lightingPlanning.ts` + `psuAllocation.ts` |
| Adâncime carcasă Bond | `return_depth_mm` / per-layer din nest2 | Layer role `return` / inner_hole |

V4 Step 2 actual: doar 4 câmpuri simple — **insuficient** vs V2; următorul build extinde `finish_setup` + UI read-only preview V2.

### Aliniere task-uri ↔ ProductSystem

Flux țintă (backend există parțial în `intake_v4_product_system_service.py`):

```text
finish_setup (operator) → _finish_context → _gate_active / _operation_active
  → task preview (operații active/inactive + inactive_reason)
  → quote handoff (Phase 2)
```

| Pas | Acțiune |
|-----|---------|
| 1 | Inventariază `formula_params.gate` pe operațiile din `TPL-VOLUMETRIC-LETTERS` (DB `product_templates.operations_json`) |
| 2 | Extinde `_finish_context` cu câmpurile LED/PSU din V2 |
| 3 | Port `build_task_preview_items` gates: `return_finish_type`, `illuminated`, policromie |
| 4 | Frontend Review: task preview din **draft form** (query/body) sau save debounced ca V2 |
| 5 | Confirm: repair list ca V2 `repairPanel` — LED/PSU/finisaj blochează handoff |

### Ordine implementare recomandată

1. **Extindere finish_setup + UI V2 parity** (651/8500/cant/LED/PSU) — doar volumetric + logo/emblemă
2. **Task preview gates** aliniate la operațiile reale din ProductSystem
3. **Quote handoff** (persist → guard → QuoteWizard)
4. Hub `/intake-v4`
5. Technical drawer (parts/nesting) — nest2 JSON deja local
6. *Standby* ACM / slogan — doar după șablon PS + BUILD dedicat

---
