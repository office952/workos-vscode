# Intake V2 → Intake V3 — Audit complet de redresare (Operator Workspace)

**Date:** 2026-06-19  
**Type:** Read-only audit — singura modificare permisă: acest fișier  
**Repo:** `C:\Users\offic\workos`  
**Auditor scope:** presentation, operare, funcționalitate practică operator — fără implementare

---

## 1. Verdict scurt

**PASS (audit complet).**

Intake V3 este **arhitectural superset** față de V2 (guards, production truth, preview-uri read-only, material/procurement/task). **Nu este încă superset operațional în UI:** multe capabilități practice V2 sunt **absente, ascunse sau fragmentate** (ColorRegistry, layer-finish unitate, lighting/PSU, flow scurt, next action).

**Redresare necesară:** reorganizare presentation-only + completări UI selective — **fără** a pierde nimic util din V2 și **fără** a slăbi boundary-urile V3.

| Verdict component | Status |
|-------------------|--------|
| Fișiere V2/V3 identificate | ✅ |
| Matrice capabilități | ✅ §8 |
| Principiu superset | ✅ §3 |
| Layer-based analizat | ✅ §14 |
| Recomandare workspace | ✅ §15 |
| Cod aplicație nemodificat | ✅ |

---

## 2. Pre-flight

```text
branch: local/integration-pr4-plus-svg-path
HEAD:   b4d8500495f42cf2b8f5cebcc99571a37c9932e6
        fix(intake-v3): repair SVG file picker upload path
```

| Check | Result |
|-------|--------|
| Expected HEAD (user note) | `7f9c93c` — superseded by `1eac137`, `b4d8500` |
| Git status | `?? docs/audits/INTAKE_V2_VS_V3_OPERATOR_WORKSPACE_PRESENTATION_AUDIT.md`, `?? tmp/` |
| Tracked modifications | None |
| `backend/dev.db` | Not touched |

---

## 3. Principiul V3 superset operațional al V2

### Regula centrală

```text
Nu pierdem nicio funcționalitate practică utilă din V2.
Tot ce era util în V2 trebuie regăsit în V3,
într-o formă mai stabilă, logică, curată, sigură și mai cuprinzătoare.
```

V3 trebuie să fie: **mai stabil, logic, curat, cuprinzător, sigur, aproape de producție reală** — dar **nu mai sărac funcțional**.

### Clasificare per capabilitate V2 utilă

| Cod | Semnificație |
|-----|--------------|
| **P** | Există deja în V3 — păstrează |
| **R** | Există în V3 — repoziționează / clarifică UI |
| **A** | Lipsește din V3 — adaugă (UI sau wiring) |
| **D** | Reproiectează conform arhitecturii V3 |
| **X** | Nu prelua intenționat (cu motiv) |

### Stare actuală (rezumat)

- **Backend V3:** deja superset (raw vs confirmed, layer roles, guards, previews).
- **UI V3:** **nu** este încă superset — gap-uri la ColorRegistry, layer-finish, lighting/PSU, flow operator.
- **SVG upload:** parțial redresat la `b4d8500` (picker + auto-upload + saved message); lipsește afișarea `file_name` ca în V2.

---

## 4. Fișiere V2 inspectate

### Routes & shell
- `frontend/src/App.tsx` — `/intake-v2/:id`
- `frontend/src/pages/WorkIntakeV2.tsx`
- `frontend/src/components/workos/workIntakeV2/WorkIntakeV2Flow.tsx`
- `frontend/src/components/workos/workIntakeV2/WorkIntakeV2OperationalHeader.tsx`

### Zone cards
- `cards/WorkIntakeV2JobDetailsCard.tsx`
- `cards/WorkIntakeV2GraphicsLayersCard.tsx` — SVG + layere
- `cards/WorkIntakeV2VolumetricRulesCard.tsx` — production + lighting
- `cards/WorkIntakeV2ReadinessHandoffCard.tsx`
- `cards/WorkIntakeV2WorkFileCard.tsx`

### Stages
- `stages/V2SvgStage.tsx` — upload, drop, saved hint
- `stages/V2LayersGeometryStage.tsx` — primary layer, geometry panel
- `stages/V2ProductionStage.tsx` — Oracal/RAL, backing, mounting
- `stages/V2LightingStage.tsx` — LED, PSU, illumination mode

### Finish / color / groups
- `V2LetterGroupFinishesSection.tsx`, `V2ArtworkPolicromieCard.tsx`, `LetterGroupReturnCantFields.tsx`
- `frontend/src/components/workos/colorRegistry/ColorRegistrySelect.tsx`
- `lib/workIntakeV2/letterGroupFinishUi.ts` — Oracal 651/641/8500, painted, print
- `lib/workIntakeV2/svgLetterGroups.ts`, `svgArtworkFinishAssignments.ts`
- `lib/workIntakeV2/volumetricFinishFlow.ts`

### Flow / readiness
- `lib/workIntakeV2/zoneLabels.ts` — 5 zone checklist
- `lib/workIntakeV2/templateConfig/volumetricLettersTemplateConfig.tsx`
- `lib/workIntakeV2/templateConfig/volumetricReadinessStrategy.ts`
- `previews/VolumetricLettersQuotePreview.tsx`
- `lib/workIntakeV2/svgUploadApi.ts` — `POST .../svg-upload-and-analyze`
- `WorkIntakeV2Flow.test.tsx` — upload, drop, layer confirm tests

---

## 5. Fișiere V3 inspectate

### Page & flow
- `frontend/src/pages/IntakeV3App.tsx` — panel stack ~30+ secțiuni
- `frontend/src/pages/IntakeV3App.test.tsx`
- `frontend/src/lib/intakeV3/flowState.ts` — 25 flow steps
- `frontend/src/lib/intakeV3/api.ts`
- `frontend/src/lib/intakeV3/productionPreviewSummary.ts`

### Operator input
- `IntakeV3CommandBar.tsx`, `IntakeV3FlowStepper.tsx`
- `IntakeV3SvgUploadPanel.tsx` (+ `.test.tsx`) — fix `b4d8500`
- `IntakeV3RawSvgAnalysisPanel.tsx`
- `IntakeV3ProductionModelReviewPanel.tsx`
- `IntakeV3LayerRoleConfirmationPanel.tsx` (+ test)
- `IntakeV3LayerRolePropagationPanel.tsx`
- `IntakeV3FinishAssignmentPanel.tsx` — global/group/letter
- `IntakeV3FieldEditor.tsx` — controlled fields, free-text colors

### Preview / guards / production
- `IntakeV3PreviewShell.tsx`, `IntakeV3ReadinessPanel.tsx`
- `IntakeV3ProductionPreviewPanel.tsx` (+ test)
- `IntakeV3GeometryMetricsPanel.tsx`, `PathPerimeterClassificationPanel.tsx`
- `IntakeV3MaterialBreakdownPanel.tsx`, `MaterialAvailabilityPanel.tsx`
- `IntakeV3ProcurementPreviewPanel.tsx`, `ProductionTaskDryRunPanel.tsx`
- `IntakeV3OrderProductionReadinessPanel.tsx`
- Quote stack: DryRun, GuardPolicy, Bridge, Enablement, CreateDraftQuote, DraftReview, PricingReview, AcceptConvert, GuardedAccept, GuardedConvert

### Backend contracts (referință)
- `backend/schemas/intake_v3.py` — layer_role_confirmation, finish_assignment, raw_svg_analysis
- `docs/intake-v3/00_STATUS.md`, `04_READINESS_AND_BLOCKERS_MODEL.md`

---

## 6. Intake V2 — presentation / functionality audit

### 6.1 Structura generală

| Aspect | V2 (din cod) |
|--------|--------------|
| Route | `/intake-v2/:id` — un intake request |
| Layout | **Zone scroll** (nu wizard liniar): header → job → graphics → rules → readiness |
| Prima vedere | Header operational + zone cards; checklist în readiness |
| Pași operator | 5 zone: Detalii job · SVG & layere · Producție/finisaje · Iluminare · Handoff |
| Next action | Header: Open Quote Wizard + `ctaBlockerReason`; readiness: repair items cu jump |
| Persistență | Auto-save `IntakeProductSpec` via `useWorkIntakeV2AutoSave` |

### 6.2 Upload SVG

| Item | V2 |
|------|-----|
| Locație | `V2SvgStage` în `WorkIntakeV2GraphicsLayersCard` |
| Select file | Da — label „Alege SVG de pe calculator” + input opacity-0 |
| Drag & drop | Da — `work-intake-v2-svg-drop-zone` |
| One-step upload | Da — select/drop → `uploadIntakeSvgAndAnalyze` imediat |
| Nume fișier | Da — hint selectat + **„Ultima analiză salvată: {name}”** |
| Saved state | `hasSavedAnalysis` din `vector_parse_status` + layer count |
| Re-upload | Da; invalidează geometrie derivată |
| Validare | Server; erori afișate |
| Endpoint | `POST /api/v1/entities/intake_requests/by-code/{code}/svg-upload-and-analyze` |
| vs V3 | V2 mai clar la saved filename, drop, parse status badge |

### 6.3 Layere / mapping

- Detectează layere: da (`vector_detected_layers`)
- Afișează nume + element count + rol sugerat
- Mapare rol: **primary letters layer** select + confirm (nu matrice completă ca V3)
- Mapare finish: **indirect** — grupuri SVG (`svgLetterGroups`) → `V2LetterGroupFinishesSection`
- Preview grafic: listă + panou geometrie; fără canvas SVG
- Layere ignorate: rol suggested + blocked primary pentru artwork multicolor

### 6.4 Finisaje / culori / Oracal / RAL

| Control | V2 locație |
|---------|------------|
| Oracal 8500 / 651 față | `V2ProductionStage` — series toggle + `ColorRegistrySelect` |
| Oracal 641 | `letterGroupFinishUi.ts` — opțiune + hint registry lipsă |
| RAL cant | Return system „RAL vopsit” + registry |
| Colantat față | `isFaceVinylEnabled` toggle |
| Cant colantat | Oracal 651 wrapped; standard alb/negru |
| Cod + nume + swatch | `ColorRegistrySelect` (hex preview) |
| Roll width | `INTAKE_ROLL_WIDTH_OPTIONS` |
| Print / policromie | `V2ArtworkPolicromieCard` |
| Painted | finish types în group UI |

### 6.5 Materiale / structură

- Backing Forex/grosime: production stage
- Mounting: steel/aluminum bars, template area
- Illuminare: **`V2LightingStage`** — LED strip/modules, PSU allocation, `syncLightingPlanning`
- Dimensiuni: job details + sugestii SVG
- Suport comun: mounting template mode, shared support via spec fields

### 6.6 Override-uri

- Global finish form (ascuns când group mode activ)
- **Grup SVG** — finisaje per grup cu confirm
- **Literă / artwork** — `svgArtworkFinishAssignments`, policromie
- Per-letter util pentru excepții; flux principal = grup/layer-derived

### 6.7 Readiness / quote / preview

- Zone checklist cu ✅/❌ (`WORK_INTAKE_V2_ZONE_CHECKLIST`)
- Repair items cu navigare la stage
- `VolumetricLettersQuotePreview` — preview ofertă orientat operator
- Fără material availability / procurement / task dry-run (V3 only)
- Warnings în finish summary + geometry panel

### 6.8 Ce este bun în V2 (de păstrat în V3)

1. Checklist 5 zone  
2. SVG one-step + saved filename/timestamp  
3. ColorRegistry + swatch  
4. Face vinyl toggle + serie 651/8500  
5. Return tri-state (stock/RAL/Oracal)  
6. Finisaje pe grup SVG (card layout)  
7. Stage iluminare + PSU  
8. Geometry trust badges  
9. Readiness repair + jump  
10. Header save status + quote CTA cu blocker  
11. Finish summary față/cant  
12. Oracal 641 path (chiar cu registry hint)  
13. Auto-save feedback  
14. Copy operator RO validat  

### 6.9 Ce nu trebuie copiat din V2

1. Endpoint intake_requests SVG (V3 workspace endpoint e corect)  
2. Lipsă raw vs production truth  
3. Lipsă guard policy stack  
4. Lipsă material/procurement preview  
5. Mock read-only path fără workspace draft  
6. Primary-layer-only ca **substitut** pentru layer role confirmation V3  
7. Quote wizard direct fără guarded draft  
8. Fără snapshot / anti-duplicate policy  
9. Coupling strâns `IntakeProductSpec` monolith  
10. Drag-drop obligatoriu (poate rămâne opțional)  

---

## 7. Intake V3 — presentation / functionality audit

### 7.1 Matur — de păstrat (P)

| Capability | Evidence |
|------------|----------|
| Raw SVG ≠ production truth | `IntakeV3RawSvgAnalysisPanel`, production model panel |
| Confirmed model = truth | `IntakeV3ProductionModelReviewPanel`, holes not letters |
| Layer role confirmation | API + `IntakeV3LayerRoleConfirmationPanel`, `layerRoleConfirmationContracts.ts` |
| Layer role propagation | `IntakeV3LayerRolePropagationPanel` |
| Geometry snapshot | `IntakeV3GeometryMetricsPanel` |
| Path perimeter classification | `IntakeV3PathPerimeterClassificationPanel` |
| Material breakdown | `IntakeV3MaterialBreakdownPanel` |
| Material availability (read-only) | `IntakeV3MaterialAvailabilityPanel` |
| Procurement preview (read-only) | `IntakeV3ProcurementPreviewPanel` |
| Task dry-run (non-executable) | `IntakeV3ProductionTaskDryRunPanel` |
| Quote guards / enablement / snapshot policy | panels + `flowState` |
| Guarded draft quote | `IntakeV3CreateDraftQuotePanel` |
| Workspace draft CRUD | `IntakeV3App` workspace panel |
| Controlled field patch | `IntakeV3FieldEditor` |
| Production preview grouping | `IntakeV3ProductionPreviewPanel` (`1eac137`) |
| No inventory/execution mutation | panel copy + backend contracts |

### 7.2 Confuz în UI V3 (R)

1. ~25 flow steps vizibile (`IntakeV3FlowStepper`)  
2. Stack vertical 20+ panouri  
3. Multe „unavailable / not loaded” pre-quote/order  
4. Finish split: FieldEditor vs FinishAssignment vs layer roles — necoordonat  
5. Fără ColorRegistry — text fields  
6. Layer role panel **după** quote stack în DOM (`IntakeV3App.tsx` ~1266+)  
7. Quote/guard/accept/convert toate expanded  
8. Command bar — multe chip-uri, fără un singur next action  
9. Production preview listat prea devreme  
10. Copy „preview-only” repetat  
11. Scenario selector amestecat cu workspace operational  
12. SVG: mesaj saved da, dar **file_name** din analysis nu e afișat prominent  

### 7.3 Lipsă / ascuns ca Operator Workspace

| Zonă | Status V3 |
|------|-----------|
| Upload/Replace SVG | ✅ panel (post `b4d8500`) |
| Saved SVG state | ⚠️ parțial |
| Layer role mapping | ⚠️ există, ascuns |
| **Layer finish mapping** | ❌ nu există — doar global/group/letter |
| Oracal/RAL selectors | ❌ registry UI |
| Face colantat toggle clar | ⚠️ `face_enabled` |
| LED/PSU detail | ❌ doar `illuminated` boolean |
| Layer-based config card | ❌ UI |
| Advanced overrides collapsed | ⚠️ parțial |
| Single next action | ❌ |

---

## 8. Matrice V2 useful capability → V3 status

Legendă **Required correction:** P=păstrează | R=repoziționează | A=adaugă | D=reproiectează | X=exclude

| V2 useful capability | V2 evidence | Current V3 status | Required V3 correction | Priority | Keep? |
|----------------------|-------------|-------------------|------------------------|----------|-------|
| SVG upload | `V2SvgStage.tsx` | Good post-`b4d8500`; auto on select | P | P0 | Da |
| SVG re-upload / replace | same | Supported; input reset | P | P0 | Da |
| File picker reliability | `WorkIntakeV2Flow.test.tsx` | Fixed hidden input + ref.click | P | P0 | Da |
| Drag/drop | `V2SvgStage` drop zone | **Missing** | X (optional later) or A low | P3 | Opțional |
| Saved SVG state | saved file hint | Message yes; **no filename** | R + A display `file_name` | P0 | Da |
| Raw SVG analysis | parse fields in spec | `IntakeV3RawSvgAnalysisPanel` | P | P1 | Da |
| Production model confirmation | N/A in V2 | `ProductionModelReviewPanel` | P (V3-only, keep) | P0 | Da |
| Layer detection | layers list stage | Raw analysis stats | R merge in C2 card | P1 | Da |
| Layer role mapping | primary layer only | Full per-layer API | D expand UI; R co-locate | P0 | Da |
| **Layer finish mapping** | group cards | **Missing** — group≠layer | **D** layer-primary finish UI | P0 | Da |
| Oracal 8500 selection | `V2ProductionStage` | enum + text in FieldEditor | A ColorRegistry + R | P0 | Da |
| Oracal 651 selection | same + group UI | enum + text | A + R | P0 | Da |
| Oracal 641 selection | `letterGroupFinishUi.ts` | Not in V3 UI | A | P2 | Da |
| RAL selection | return system RAL | text fields painted return | A registry + R | P0 | Da |
| Face vinyl / no face vinyl | toggle | `face_enabled` | R V2-style toggle | P1 | Da |
| Printed vinyl | group UI kind | enum exists | P + R visibility | P2 | Da |
| Painted face | group/global | enum | P | P2 | Da |
| Return cant raw/stock | standard return | enums partial | P | P2 | Da |
| Return cant painted RAL | RAL system | text fields | A + R | P1 | Da |
| Return cant Oracal wrapped | Oracal return | `oracal_wrapped` enum | P + R | P1 | Da |
| Backing material | production stage | FieldEditor | P | P1 | Da |
| Backing thickness | same | FieldEditor | P | P1 | Da |
| Support mode | mounting fields | `support_mode` enum | P | P1 | Da |
| Illumination on/off | lighting stage | boolean only | A subsection | P1 | Da |
| LED / PSU inputs | `V2LightingStage` | **Missing** | A (fields exist in volumetric libs) | P1 | Da |
| Dimensions W/H/D | job + geometry | FieldEditor | P | P0 | Da |
| Roll width | roll width options | FieldEditor field | P | P1 | Da |
| Return depth | production | FieldEditor | P | P1 | Da |
| Color code | ColorRegistrySelect | free text | A registry | P0 | Da |
| Color name | registry | free text | A registry | P0 | Da |
| Swatch / preview hex | registry | **Missing** | A | P0 | Da |
| Group override | `V2LetterGroupFinishesSection` | FinishAssignmentPanel plain | R layout from V2 | P1 | Da |
| Letter override | artwork assignments | FinishAssignment letter | R → **advanced only** | P2 | Da |
| Operator notes | various | prod model + layer roles | P | P2 | Da |
| Readiness | zone checklist + repairs | preview + many panels | R single card + jumps | P0 | Da |
| Quote preview | `VolumetricLettersQuotePreview` | PreviewShell | P | P1 | Da |
| Draft quote action | quote wizard CTA | guarded CreateDraftQuote | P (safer) | P0 | Da |
| Production preview | minimal | full grouped stack | R collapse until stage | P1 | Da |
| Material breakdown | N/A | panel | P (V3-only) | P2 | Da |
| Material availability | N/A | read-only panel | P (V3-only) | P2 | Da |
| Procurement preview | N/A | read-only panel | P (V3-only) | P2 | Da |
| Task dry-run | N/A | non-exec panel | P (V3-only) | P2 | Da |
| Technical details | geometry debug lines | 25 steps + guards | R → section F collapsed | P1 | Da |
| Operator next action | header CTA + repairs | scattered | A derive from readiness | P0 | Da |

### Matrice scurtă — numărare status

| Category | Count | % |
|----------|-------|---|
| **Already good (P)** — păstrează | 22 | 44% |
| **Present but confusing (R)** | 14 | 28% |
| **Missing (A)** | 9 | 18% |
| **Redesign (D)** | 2 | 4% |
| **Excluded intentionally (X)** | 1 | 2% |
| **V3-only keep (no V2)** | 4 | (production model, mat/proc/task previews) |

*(50 rows capability incl. V3-only; categorii P/R/A/D/X pe fluxuri operator)*

---

## 9. V2 vs V3 — comparison table (rezumat)

| Feature / UX area | Intake V2 | Intake V3 current | Recommendation |
|-------------------|-----------|-------------------|----------------|
| SVG upload | One-step; drop+picker; saved name | Picker; auto-upload; saved message | P + show filename |
| Layer workflow | Primary layer + SVG groups | Full layer roles; finish on group/letter | **Layer-based primary (D)** |
| Finish workflow | Registry + cards per group | Enums + text; split panels | Port registry + unify C2 |
| Color/material workflow | ColorRegistry, swatch | Text fields | A registry |
| Quote/readiness workflow | 5 zones + repair jumps | 25 steps + guard stack | R checklist + collapse guards |
| Production preview workflow | Minimal | Rich; early visibility | R section E collapsed |
| Operator clarity | High (zone model) | Low (debug stack) | A–F workspace shell |
| Technical safety | Low | High | **Keep V3** |
| Implementation maturity | Production path legacy | Contract-first, guards | **Keep V3 backend** |

---

## 10. Ce merită preluat din V2

1. Five-zone checklist  
2. Saved SVG filename + timestamp + parse badge  
3. `ColorRegistrySelect` (Oracal + RAL + swatch)  
4. Face vinyl toggle + 651/8500/641 paths  
5. Return finish system selector  
6. Group finish card layout (adapt to **layer** rows)  
7. `V2LightingStage` PSU/LED block  
8. Geometry trust/stale badges  
9. Readiness repair list with scroll-to-zone  
10. Finish summary mini-card  
11. Header: save status + one next action + quote blocker  
12. One-step file select → analyze  
13. Oracal 641 manual path with registry hint  
14. RO operator copy where validated  

---

## 11. Ce nu trebuie copiat din V2

1. intake_requests SVG endpoint  
2. Absence of production truth / guards  
3. Quote wizard fără guarded draft  
4. Mock-only flows as source of truth  
5. Primary-layer-only **instead of** V3 layer role matrix  
6. Monolithic spec fără workspace payload  
7. Fără material/procurement/task preview  
8. Drag-drop ca requirement  
9. Auto-save fără patch validation  
10. Lipsă snapshot / idempotency policy  

---

## 12. Ce trebuie păstrat din V3

Tot ce e listat în §7.1 — în special: production truth split, layer role confirmation API, guard chain, read-only previews, workspace persistence, fail-closed boundaries.

---

## 13. Ce trebuie corectat în V3 UI

1. Shell A–F (§15) — fără schimbare business logic  
2. Layer finish = unitate principală în C2 (**D**)  
3. ColorRegistry în FieldEditor / layer finish rows (**A**)  
4. Reorder DOM: Input before Quote guards  
5. Collapse quote stack → section F  
6. Collapse production preview → section E until stage  
7. Map 25 steps → 5 checklist items (presentation)  
8. Single next action in header  
9. Show `raw_svg_analysis.file_name` in C1  
10. LED/PSU fields from volumetric libs (**A**)  
11. Per-letter override → C5 advanced only (**R**)  
12. Reduce „preview-only” repetition — one banner per zone  

---

## 14. Recomandare layer-based workflow

### Ce face V2

- **Parțial layer-based:** layere detectate → primary letters layer → **grupuri SVG derivate** → finisaje pe grup.
- Finish pe layer direct: **nu** — finish pe grup/artwork.

### Ce face V3

- **Layer role confirmation:** da — per `layer_key` (`IntakeV3LayerRoleConfirmationPanel`, backend snapshot).
- **Finish mapping:** global + `letter_group` + `letter` — **nu** per layer (`backend/schemas/intake_v3.py`).
- Gap: rol layer și finish sunt **decouple** în UI și model.

### Regulă recomandată (compatibilă cu ambele)

```text
Primary assignment = layer-based (role + finish on same row/card).
Advanced override = group/letter — collapsed, rare, when SVG not split cleanly.
```

### Ce trebuie schimbat în V3 (viitor build — nu acum)

| Item | Action |
|------|--------|
| UI C2 | Un card per layer: role dropdown + face/return finish + Oracal/RAL |
| Backend | Opțional: `layer_finish_assignments[]` sau map group→layer_key explicit |
| FinishAssignmentPanel | Păstrează API group/letter în C5 advanced |
| V2 group cards | **D** → layer rows, nu invers |

### Per-letter override

- **Păstrează** ca advanced/rare (C5) — confirmat compatibil cu V2 (artwork path) și V3 API.

---

## 15. Structura recomandată V3 Operator Workspace

Validată pe V2 zones + V3 capabilities.

### A. Header + current stage + next action
- Din V3: workspace code, command bar status  
- Din V2: save dirty/saving, **single CTA** + blocker din `quote_readiness.next_recommended_action`

### B. Current Stage Checklist (5 items)
- Din V2: `WORK_INTAKE_V2_ZONE_CHECKLIST` pattern  
- Din V3: agregat din `flowState.ts` (logic unchanged, display simplified)

### C. Input & Setup

| Section | Din V2 | Din V3 | Mutare |
|---------|--------|--------|--------|
| **C1** SVG upload/replace | saved filename, one-step | SvgUploadPanel, RawAnalysis, ProdModelReview | Mută sus; afișează file_name |
| **C2** Layers, roles & finishes | layer list, group cards, registry | LayerRoleConfirmation + **new layer finish UI** + FinishAssignment advanced | **Unifică aici**; layer-based **D** |
| **C3** Dimensions | job fields | FieldEditor dimensions | Păstrează |
| **C4** Backing/support/illumination | production + lighting stages | FieldEditor + **A** LED/PSU | Completează din V2 |
| **C5** Advanced overrides | letter/artwork | group/letter FinishAssignment | **Ascunde** default |

### D. Quote Readiness / Guarded Draft Quote
- Din V3: PreviewShell readiness, blockers, CreateDraftQuote when enabled  
- Din V2: repair-style list  
- **Ascunde** dry-run/guard/bridge/enabled details → F

### E. Production Preview (collapsed default)
- Din V3: `ProductionPreviewPanel` subsections  
- Din V2: nimic echivalent — **V3-only, păstrează**  
- **Ascunde** până la draft quote / order stage

### F. Advanced Technical Details (collapsed)
- Din V3: full flow stepper, guard stack, accept/convert, propagation audit  
- **Elimină** din viewport default — nu elimina funcționalitate

### Ce se elimină intenționat (X)

- Drag-drop obligatoriu  
- V2 intake_requests endpoint  
- Primary-layer-only ca model final  
- Quote wizard fără guards  

---

## 16. Riscuri

| Risk | Mitigation |
|------|------------|
| UI refactor breaks contracts | Presentation-only; same API clients |
| Layer finish needs schema | Phase 1 UI map layer→existing group; Phase 2 backend |
| Color registry → pricing | Registry display-only per AGENTS.md |
| Hiding guards | Blocker summary always in D |
| Per-letter removal | Keep C5 — do not delete API |
| Atoms mock with fake actions | Boundaries in prompt |

---

## 17. Prompt recomandat pentru Atoms refinement

```
Refine the mock so V3 keeps all useful V2 functionality, but organizes it in a cleaner, layer-based operator workspace.
Do not make per-letter selection the main workflow.
Use SVG layers as the primary control unit.
Show upload, layer role, layer finish, Oracal/RAL, backing/support, quote readiness, production preview.
No Generate Tasks, Reserve Inventory, Purchase Orders, or status mutations.
Reference: docs/audits/INTAKE_V2_VS_V3_OPERATOR_WORKSPACE_PRESENTATION_AUDIT.md
```

---

## 18. Prompt recomandat pentru Cursor implementation

```
Implement V3 Operator Workspace as a functional superset of V2.
Do not remove V2-useful capabilities.
Restructure V3 into Input & Setup + Review & Preview.
Keep all V3 safety boundaries.
Fix SVG file picker if broken.
Make layer-based mapping primary.
Keep per-letter overrides collapsed/advanced only.
No execution/inventory/procurement mutations.
Read: docs/audits/INTAKE_V2_VS_V3_OPERATOR_WORKSPACE_PRESENTATION_AUDIT.md
Frontend only unless layer_finish schema approved.
```

---

## 19. Autoevaluare

| Criterion | Score | Notes |
|-----------|-------|-------|
| Corectitudine față de surse | **9/10** | HEAD `b4d8500`; cod TSX/schemas citite direct |
| Utilitate pentru UI | **9/10** | Matrice 50 capabilități + layer-based §14 |
| Risc de presupuneri | **3/10** (low) | Layer finish backend gap marcat explicit; fără browser runtime |

---

*End of audit. No application source modified except this document.*
