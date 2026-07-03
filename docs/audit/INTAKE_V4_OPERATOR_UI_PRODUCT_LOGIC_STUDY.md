# Intake V4 — Operator UI Product Logic Study

**Date:** 2026-06-24  
**Branch:** `local/integration-pr4-plus-svg-path`  
**HEAD (local):** `53173da` *(expected `7de0f53` — one commit ahead; tracked clean)*  
**Mode:** read-only study / architecture planning — **no code changes except this doc**  
**Related audits:** `INTAKE_V4_OPERATOR_UI_COUNTS_HARD_AUDIT.md`, `INTAKE_V4_ALIGNMENT_AUDIT.md`, `BUILD_INTAKE_V4_ATOMS_OPERATOR_WORKSPACE.md`

---

## 1. Scop

Definim cum ar trebui să arate **Intake V4 ca produs operator**, nu ca expunere directă a tuturor serviciilor tehnice construite până acum.

Problema: backend-ul și lib-urile V4 conțin logică solidă (SVG analysis, nesting, material review, overrides, dry-run), dar **UI-ul principal a devenit un catalog de panouri** — operatorul vede simultan geometrie, finisaje, estimări materiale, dry-run V3, AI mock, commercial spine și task preview, fără ierarhie clară a deciziilor.

Acest document răspunde la:

1. Ce avem acum în cod  
2. Ce e util vs debug vs V3 expus greșit  
3. Cum arată un intake profesional pentru producție publicitară  
4. Cum simplificăm UI fără big-bang  
5. Dacă avem nevoie de AI/OCR  
6. ViewModel + structură UI + plan de implementare în faze  

**Out of scope acum:** CostEngine, quote final, stock, production tasks reale, AI/OCR implementare, commit/push.

---

## 2. Pre-flight (Task A)

| Check | Result |
|-------|--------|
| Branch | `local/integration-pr4-plus-svg-path` ✓ |
| HEAD | `53173da` — *not* `7de0f53`; commit `53173da fix(intake-v4): hide ambiguous production part count from operator summary` |
| Tracked dirty | **Clean** — only untracked `??` (docs/tmp/test-results) |
| Recent commits | Operator count simplification, material review labels, shared helpers, reanalysis docs |

**Notă:** HEAD ahead cu 1 commit față de expected; nu există modificări tracked unstaged/staged. Studiul continuă.

---

## 3. Starea actuală (Task B)

### 3.1 Flux operator — ce vede acum

**Route:** `/intake-v4/:workspaceId/operator` → `IntakeV4OperatorWorkspaceApp` → `IntakeV4OperatorWorkspace`

**Shell Atoms (toate step-urile):**

| Zonă | Componentă | Conținut |
|------|------------|----------|
| Smart banner | `IntakeV4SmartBanner` | Mesaj contextual pas curent / prim blocker |
| Header | `IntakeV4Header` | workspace code, titlu, fișier SVG, dimensiune |
| Progress | `IntakeV4ProgressBar` | 3 pași: `layers` → `review` → `confirm` |
| Status bar | `IntakeV4StatusBar` | readiness, layer confirmation chips |
| Footer fix | workspace shell | Back / Next, blocker în footer la Review |

**Step 1 — `layers` (`IntakeV4SvgAnalyzerStep`):**

- Upload SVG (client nest2, drag-drop global)
- Preview canvas (`IntakeV4SvgPreviewCanvas`) — raster lipsă warning
- Rezumat dimensiuni + straturi + status confirmare
- **`IntakeV4GeometryPanel`** — metrici perimetru/arie, grupuri volumetrice, piese producție *(încă vizibile aici)*
- Tabel **Layer roles** — Kind, Auto, Paint, Confirmed, State (dropdown rol)
- Confirm all auto roles

**Step 2 — `review` (`IntakeV4ReviewStep`) — cel mai încărcat:**

Panouri în ordinea render (principal, top→bottom):

| # | Panou | Rol |
|---|-------|-----|
| 1 | ProductSystem binding card | template + operation count |
| 2 | `IntakeV4OperatorWorkSummary` | artwork, goluri, layout parts, layere |
| 3 | `IntakeV4GeometryPanel` | **duplicat** față de Step 1 |
| 4 | `IntakeV4BackingAndEmblemSection` | backing mode, emblem lighting |
| 5 | `IntakeV4EdgeCantReviewCard` | cant/volum review operator |
| 6 | `IntakeV4AiSemanticAssistPanel` | AI mock suggestions |
| 7 | `IntakeV4LetterGroupFinishesSection` | finisaje per grup litere |
| 8 | `IntakeV4ArtworkComplexityCard` | complexitate artwork |
| 9 | `IntakeV4ArtworkFinishSection` | finisaje artwork per layer |
| 10 | Setări globale / iluminare LED | form mare (651, cant, PSU, module) |
| 11 | `IntakeV4MaterialBreakdownPanel` | estimare materiale + nesting + sheet quote review + override |
| 12 | **Technical accordion** | production parts count, V3 dry-run, pricing preview, handoff, task gen, order readiness, commercial spine, task preview V3 |

**Step 3 — `confirm` (`IntakeV4ConfirmStep`):**

- Summary card (request, template, SVG file)
- `IntakeV4ConfirmOperationalSummary` — structură, finish, geometrie, cant, lighting, nesting flags
- Status readiness (preview / handoff / task generation labels)
- ProductSystem binding + blockers
- Quote handoff — checkboxes boundary, internal draft confirmation, create draft quote → QuoteWizard

### 3.2 Ce e în zona principală vs ascuns

| Informație | Unde apare | Principal / ascuns |
|------------|------------|-------------------|
| Nume fișier, dimensiuni | Header, Step 1 | Principal ✓ |
| Preview SVG | Step 1 | Principal ✓ |
| Layer roles table | Step 1 | Principal ✓ (core decision) |
| Geometrie quote (perimetre multiple) | Step 1 + Step 2 | Principal — **prea tehnic** |
| Rezumat lucrare (4 contoare) | Review + Confirm | Principal ✓ (recent simplificat) |
| Finisaje per layer / LED / backing | Review | Principal ✓ (decizie operator) |
| Material breakdown table | Review | Principal — **parțial prea dens** |
| Sheet quote review + footprint override | În MaterialBreakdown | Principal când `requires_manual_review` |
| Nesting canvas + alternatives | Accordion în MaterialBreakdown | Parțial ascuns ✓ |
| Production vector parts count | Technical accordion | Ascuns ✓ (commit 53173da) |
| V3 ProductionTaskDryRunPanel | Technical accordion | Ascuns dar **limbaj V3 vizibil** |
| Pricing input preview | Technical accordion | Ascuns ✓ |
| Task preview catalog V3 | Technical accordion | Ascuns dar titlu V3 |
| AI semantic assist | Review principal | **Ar trebui ascuns** (mock, non-binding) |
| Raw warnings grouped | MaterialBreakdown | operator/quoting principal, technical în accordion |

### 3.3 Surse date: V4 pur vs V3/adapters

| Informație | Sursă |
|------------|-------|
| SVG analysis client | `lib/svgAnalyzer` (nest2 port) — V4 |
| Layer roles, finish setup | `intakeV4Api` PUT + payload — V4 routes |
| Quote geometry | `intakeV4QuoteGeometry` + persisted `path_geometry_summary` — V4 |
| Material breakdown | `GET .../material-breakdown` — V4 service |
| Nesting preview | embedded in breakdown + `GET .../nesting-preview` — V4 |
| Sheet quote candidates / override | V4 material + `putIntakeV4SheetFootprintOverride` |
| ProductSystem binding | V4 adapter over template registry |
| Task preview | V4 route, **catalog wording V3** |
| Production task dry-run | V4 route → **renders `IntakeV3ProductionTaskDryRunPanel`** |
| Quote handoff | V4 `getIntakeV4QuoteHandoffPreview` |
| Commercial spine | V4 panel, quote-linked |
| AI assist | V4 mock endpoint — informational only |
| Readiness gates | V4 `intakeV4Readiness` + backend `readiness_status` |

### 3.4 Duplicate și greu de explicat

**Duplicate:**

- `IntakeV4GeometryPanel` în Step 1 și Step 2  
- Contoare artwork/goluri/layout în `OperatorWorkSummary` + `ConfirmOperationalSummary` + parțial în GeometryPanel  
- ProductSystem binding în Review și Confirm  
- Sheet review status banner duplicat (MaterialBreakdown header + SheetQuoteReviewPanel)  
- Nesting: `nesting_rows` summary + `IntakeV4NestingPreviewPanel` canvas  
- Perimetre LED/CNC/cant explicate în GeometryPanel, EdgeCantReviewCard, lighting block, Confirm summary  

**Greu de explicat operatorului:**

- Diferența Corel curve length vs LED exterior vs CNC vs cant/return  
- `Piese plasate în layout` vs `Piese producție` vs `real_letters_count`  
- `nest2`, `bbox`, `efficiency_percent`, `quantity_basis`, `confidence`  
- `is_applied_to_quote=false` vs estimare internă vs draft quote  
- „Preview only — catalog V3” / „nu consumă stoc” repetat în 6+ locuri  
- `needs_decision / policromie pending` (raw token artwork)  
- Multiple accordions „Technical details” nested  

---

## 4. Adevărurile sistemului (Task C)

### Tabel niveluri

| Nivel | Ce reprezintă | Unde e în cod | Cine are nevoie | UI principal? |
|-------|---------------|---------------|-----------------|----------------|
| **1. File truth** | Fișier, dimensiuni, preview, raster lipsă, SVG valid | `useIntakeV4Workspace`, `svgAnalyzer`, `IntakeV4SvgPreviewCanvas`, payload `svg_source` | Operator | **Da** — File card |
| **2. Geometry truth** | Paths, layers, holes, vector parts, perimetre, arii | `intakeV4QuoteGeometry`, `intakeV4GeometryMetricDisplay`, `IntakeV4GeometryPanel`, backend path_geometry | Operator (decizii), Owner (audit), Dev | **Parțial** — doar outcome-uri decizionale; metrici raw → detalii |
| **3. Nesting truth** | Placements, layout activ, alternative, bbox, sheet/roll | `IntakeV4NestingPreviewPanel`, breakdown `nesting_preview`, `intake_v4_nesting_*` services | Owner, Dev; Operator doar când review material | **Nu** — doar status „layout calculat / necesită review” |
| **4. Material review truth** | Selected area, source, manual review, override, not applied to quote | `IntakeV4SheetQuoteReviewPanel`, `intake-shared/materialReview*`, breakdown candidates | Operator + Owner | **Da** — Material review card când activ |
| **5. Commercial truth** | Quote, CostEngine, pricing, margin | QuoteWizard, `IntakeV4PricingInputPanel`, handoff preview | Owner, Sales | **Nu** în intake — doar „draft intern posibil / blocat” |
| **6. Production truth** | Task candidates, dry-run, handoff, ExecutionPlan | Dry-run panels, task preview, order-bound readiness | Production manager, Dev | **Nu** — detalii tehnice / owner |
| **7. Technical debug** | Raw payload, V3 adapters, internal warnings | Accordions, grouped warnings `technical`, API raw fields | Dev, Owner audit | **Nu** — un singur accordion |

### Per nivel — cine vede ce

#### 1. File truth

| Audiență | Ce vede |
|----------|---------|
| Operator | Nume fișier, dimensiuni mm, preview, „raster extern lipsă”, valid/invalid |
| Owner | + hash fișier, dată upload |
| Detalii tehnice | Parser warnings, nest2 version |
| Ascuns | Internal file ids, storage paths |

#### 2. Geometry truth

| Audiență | Ce vede |
|----------|---------|
| Operator | Layere confirmate, artwork vs litere (count simplu), goluri relevante decupaj, backing/emblem decisions |
| Owner | Perimetre breakdown, confidence surse |
| Detalii tehnice | `real_letters_count`, vector parts, Corel curve length, character count n/a note |
| Ascuns | Raw path ids, `_220xxx` layer ids |

#### 3. Nesting truth

| Audiență | Ce vede |
|----------|---------|
| Operator | „Layout sheet activ pentru estimare” + CTA review dacă manual |
| Owner | Canvas preview, efficiency, alternative layouts |
| Detalii tehnice | placements, part_id, bbox metrics |
| Ascuns | nest2 internal config ids |

#### 4. Material review truth

| Audiență | Ce vede |
|----------|---------|
| Operator | Status badge, arie selectată m², sursă (auto/nesting/manual), pași override |
| Owner | Candidați alternativi, snapshot export, stale/fresh reanalysis notes |
| Detalii tehnice | `quantity_basis`, `confidence`, floor hints |
| Ascuns | `is_applied_to_quote` flag name — înlocuit cu copy „nu e în oferta finală” |

#### 5. Commercial truth

| Audiență | Ce vede |
|----------|---------|
| Operator | Handoff allowed/blocked + motiv plain language |
| Owner | Pricing input preview, missing prices |
| Detalii tehnice | CostEngine inputs, spine state |
| Ascuns | Raw quote_input JSON |

#### 6. Production truth

| Audiență | Ce vede |
|----------|---------|
| Operator | Nimic obligatoriu pre-quote |
| Owner | Task preview list, dry-run counts |
| Detalii tehnice | ExecutionPlan, tasks_json, V3 dry-run output |
| Ascuns | Complet din flux operator standard |

#### 7. Technical debug

| Audiență | Ce vede |
|----------|---------|
| Dev/Owner audit | Raw warnings, adapter boundaries, payload excerpts |
| Ascuns complet | Din UI operator zilnic — doar mod „Advanced / Support” |

---

## 5. Patternuri existente în WorkOS (Task D)

### 5.1 Patternuri bune de copiat

| Pattern | Unde | De ce |
|---------|------|-------|
| **NextStepPanel** | `Quotes.tsx` | Title + blocker/warning + primary action disabled cu motiv |
| **AtomsBadge** + status tone | `intakeV4Presentation.tsx` | ok / pending / muted — deja în V4 |
| **3-step wizard + footer blocker** | `IntakeV4OperatorWorkspace` | Similar V2 readiness gates |
| **VolumetricFinishDisplayPanel** | QuoteWizard / V2 | Finish ca read-only display, nu form brut |
| **Quote handoff checkboxes** | `IntakeV4ConfirmStep` | Boundary clar: draft only, no order/inventory |
| **IntakeV4TechnicalDetailsAccordion** | V4 atoms | Un collapsible — trebuie **unul singur** per step |
| **Sheet quote review status** | `intake-shared/materialReviewStatus.ts` | Shared V3/V4 — de reutilizat |
| **Smart banner contextual** | `IntakeV4SmartBanner` | Un singur mesaj „next action” |
| **Governance badges** | `QuoteDocumentGovernancePanel`, `QuoteAcceptanceGuardIndicator` | Status + blockers list |

### 5.2 Patternuri de evitat

| Anti-pattern | Exemplu V4 |
|--------------|------------|
| Stack vertical de 15+ carduri | `IntakeV4ReviewStep` |
| Același panou în 2 step-uri | GeometryPanel layers + review |
| Component V3 cu titlu V3 în V4 | `IntakeV3ProductionTaskDryRunPanel`, „catalog V3” |
| Fetch paralel 8+ API la mount review | `IntakeV4ReviewStep` useEffects |
| Metrici tehnice fără decizie attached | 4 tipuri perimetru în panel principal |
| Multiple nested accordions | MaterialBreakdown + Review + ArtworkFinish |
| Raw field names în UI | `needs_decision`, `quantity_basis` visible |

### 5.3 Componente reutilizabile

- `NextStepPanel` — pentru Operator Action card  
- `AtomsBadge`, `v4.card`, `v4.btnPrimary/Ghost` — design tokens existente  
- `IntakeV4TechnicalDetailsAccordion` — consolidare  
- `intake-shared/materialReviewCopy.ts`, `materialReviewStatus.ts`  
- `IntakeV4OperatorWorkSummary` — baza Work decision card  
- `IntakeV4SheetQuoteReviewPanel` + `IntakeV4SheetFootprintOverridePanel` — Material review card  
- `IntakeV4SmartBanner` — rămâne header contextual  

### 5.4 Design tokens existente

```ts
// frontend/src/components/workos/intake-v4/atoms/intakeV4Presentation.tsx
v4.page, v4.card, v4.label, v4.mono, v4.btnPrimary, v4.btnGhost
AtomsBadge: ok | pending | action | muted
Culori: bg #0A0F1A, card #111827, border #2A3548
Typography: 10–13px uppercase labels, 11–12px body
Max width content: 920px
```

---

## 6. Model intake profesional (Task E)

### 6.1 Întrebările unui intake bun (producție publicitară)

| # | Întrebare | Răspuns dorit în UI |
|---|-----------|---------------------|
| 1 | Ce a trimis clientul? | File card: nume, preview, dimensiuni |
| 2 | Fișier utilizabil? | Valid/invalid, raster lipsă, layer scope warnings |
| 3 | Ce se produce? | Litere volumetrice + artwork + backing — în limbaj product |
| 4 | Ce nu e clar? | Decision card: roluri layer pending, artwork needs_decision, manual material review |
| 5 | Ce decide operatorul? | Roluri → finisaje → backing/emblem → material footprint override |
| 6 | Impact material? | Material review card: m² selectat, sursă, estimare internă disclaimer |
| 7 | Impact ofertă? | „Draft quote posibil / blocat” + blockers — fără CostEngine |
| 8 | Ce nu e aplicat final? | Copy uniform: estimări interne, nesting preview, nu preț client |
| 9 | Ce aprobă înainte de producție? | Confirm step boundaries — draft intern only |

### 6.2 Pipeline logic

```text
Intake file
  → File validation
  → Geometry interpretation
  → Operator review
  → Material review
  → Commercial readiness
  → Production readiness
```

| Etapă | Input | Output | Decide | Automat | Manual | Blochează | Avertizează |
|-------|-------|--------|--------|---------|--------|-----------|-------------|
| **File validation** | SVG upload | parse report, preview | — | nest2 parse, dims | — | invalid SVG | raster extern lipsă |
| **Geometry interpretation** | report + template | layer auto-roles, quote_geometry | — | auto-role, metrics | — | — | out-of-scope layers |
| **Operator review** | roles + finish form | confirmed finish_setup | Operator | LED calc, cant derive | layer roles, finishes, backing, artwork execution | unconfirmed layers/finish | artwork complexity |
| **Material review** | breakdown + nesting | selected sheet area, override | Operator/Owner | auto candidate | footprint override, manual confirm | review_required fără override | review_recommended |
| **Commercial readiness** | finish + geometry + binding | handoff preview, blockers | Operator confirm | readiness_status | internal draft checkbox | fatal blockers | review_warnings |
| **Production readiness** | quote exists | task dry-run, order readiness | Production | — | — | — | task preview info |

---

## 7. Decizie AI / OCR (Task F)

| Use case | Merită acum? | Risc | De ce | Alternativă non-AI | Dacă AI, unde + confirmare |
|----------|--------------|------|-------|-------------------|---------------------------|
| **1. OCR număr litere vizibile** | **Nu** | Mare — curbe ≠ caractere; clientul poate avea logo nu text | Producția necesită vector truth; OCR pe preview e unreliable | `real_letters_count` / vector parts în detalii tehnice; copy „n/a caractere” | N/A — nu recomandat ca sursă de adevăr |
| **2. AI interpretare SVG** | **Nu** (doar R&D) | Mediu — hallucination roluri | Avem nest2 + auto-role + operator confirm | Layer auto-role + confirm table | `IntakeV4AiSemanticAssistPanel` rămâne mock collapsed; apply only after operator click |
| **3. AI sumarizare warnings** | **Poate later** | Mic-Mediu | Multe warnings grouped — operator pierde timp | `groupIntakeV4Warnings` + plain RO copy (deja parțial) | Banner + 3 bullets max; expandable full list |
| **4. AI recomandare acțiune operator** | **Nu** | Mediu — override readiness gates | `getIntakeV4FirstBlocker` + SmartBanner acoperă | Rule-based next step din ViewModel | Doar sugestie text, never auto-navigate |
| **5. AI material selection** | **Nu** | Mare — pricing impact | Sheet quote candidates + rules exist | nesting floor + manual override | N/A |
| **6. AI quote final** | **Nu** | Critic — CostEngine boundary | Quote = CostEngine + governance | Draft quote handoff existent | N/A |

**Verdict AI/OCR:** Nu investim acum. Prioritate: **ViewModel rule-based + copy + ierarhie UI**. AI Informational Layer rămâne ascuns/disabled până la contract explicit cu human-in-the-loop.

---

## 8. ViewModel propus (Task G)

```ts
/** Single read model for operator-facing UI — built client-side, no new backend */
export interface IntakeV4OperatorReviewViewModel {
  file: IntakeV4VmFile;
  work: IntakeV4VmWork;
  materialReview: IntakeV4VmMaterialReview;
  operatorAction: IntakeV4VmOperatorAction;
  readiness: IntakeV4VmReadiness;
  technicalDetails: IntakeV4VmTechnicalDetails;
}
```

### 8.1 `file`

| Câmp | Sursă API / state | Componentă actuală | UI zone | Fallback |
|------|-------------------|--------------------|---------|----------|
| `fileName` | `state.svg.fileName`, payload `svg_source` | Header, Confirm | File card | „—" |
| `widthMm`, `heightMm` | `analyzerReport.document` | SvgAnalyzerStep summary | File card | „—" |
| `fileSizeLabel` | header hook | IntakeV4Header | File card | omit |
| `layerCount` | `report.layers.length` | OperatorWorkSummary | File card | 0 |
| `previewStatus` | `previewSource` + raster flags | SvgPreviewCanvas | File card | `missing` / `ok` / `partial` |
| `missingRasterCount` | artworkComplexity assessments | SvgPreviewCanvas banner | File card badge | 0 |
| `analysisPersisted` | `isAnalysisPersisted(payload)` | SmartBanner | File card status | false |
| `fileHashShort` | `localFileHash` | — | Technical only | null |

### 8.2 `work`

| Câmp | Sursă | Componentă | UI zone | Fallback |
|------|-------|------------|---------|----------|
| `artworkCount` | `buildIntakeV4OperatorWorkSummaryCounts` | OperatorWorkSummary | Work card | — |
| `innerHolesCount` | quote_geometry | OperatorWorkSummary | Work card | — |
| `placedLayoutCount` | nesting summary | OperatorWorkSummary | Work card | — |
| `backingModeLabel` | `intakeV4BackingMode` | BackingAndEmblemSection | Work card | — |
| `emblemLightingLabel` | finish_setup | BackingAndEmblemSection | Work card | — |
| `templateLabel` | product binding | Review binding card | Work card subtitle | — |
| `productionVectorPartCountTechnical` | geometry `real_letters_count` | OperatorWorkSummaryTechnicalDetails | **Technical** | — |
| `layerRolesPendingCount` | layer chips | StatusBar | Operator action input | 0 |

### 8.3 `materialReview`

| Câmp | Sursă | Componentă | UI zone | Fallback |
|------|-------|------------|---------|----------|
| `selectedAreaSqm` | `sheet_quote_material_candidates.selection` | SheetQuoteReviewPanel | Material card | null |
| `selectedSourceLabel` | `formatSheetQuoteSourceLabel` | SheetQuoteReviewPanel | Material card | „nest2 auto" |
| `appliedToQuote` | `selection.is_applied_to_quote` | SheetQuoteReviewPanel | Material card copy | false → „nu în oferta finală" |
| `requiresManualReview` | candidates flag | materialReviewStatus | Material card badge | false |
| `confidenceLabel` | recommended_auto_candidate | SheetQuoteReviewPanel | Material card | omit |
| `reviewStatus` | `resolveSheetQuoteReviewStatus` | SheetQuoteReviewPanel | Material card | ok_auto |
| `hasFootprintOverride` | payload `sheet_quote_override` | SheetFootprintOverridePanel | Material card action | false |
| `internalEstimateTotal` | breakdown.totals | MaterialBreakdownPanel | Material card (collapsed) | — |
| `missingPrices` | breakdown.totals.contains_missing_prices | MaterialBreakdownPanel badge | Material card warn | false |

### 8.4 `operatorAction`

| Câmp | Sursă | Componentă | UI zone | Fallback |
|------|-------|------------|---------|----------|
| `required` | derived: any blocker | SmartBanner, footer | Action card | false |
| `title` | rule engine | — | Action card | „Continuă" |
| `steps` | ordered CTAs | SmartBanner messages | Action card list | [] |
| `primaryCta` | step + blocker | footer Next | Action card button | — |
| `overrideAvailable` | sheet review + footprint | SheetFootprintOverridePanel | Material/Action | false |
| `blockerMessage` | `getIntakeV4FirstBlocker` | footer, SmartBanner | Action card | null |

### 8.5 `readiness`

| Câmp | Sursă | Componentă | UI zone | Fallback |
|------|-------|------------|---------|----------|
| `workspaceReadiness` | workspace.readiness_status | StatusBar | Header badge | — |
| `finishConfirmed` | finish_setup.confirmed | Review save | Readiness row | false |
| `handoffAllowed` | quote handoff preview | ConfirmStep | Confirm only | false |
| `handoffBlockers` | handoff fatal_blockers | ConfirmStep | Confirm | [] |
| `reviewWarnings` | handoff preview | ConfirmStep | Confirm warn | [] |
| `canCreateDraftQuote` | canSubmit logic | ConfirmStep | Confirm | false |

### 8.6 `technicalDetails`

| Câmp | Sursă | Componentă | UI zone | Fallback |
|------|-------|------------|---------|----------|
| `vectorParts` | geometry metrics | GeometryPanel, TechnicalDetails | Accordion | — |
| `nestableParts` | nesting summary | NestingPreviewPanel | Accordion | — |
| `placements` | nesting parts[] | NestingPreviewPanel | Accordion | — |
| `sheetLayouts` | nesting sheets | NestingPreviewPanel | Accordion | — |
| `perimeterBreakdown` | geometryMetrics | GeometryPanel | Accordion | — |
| `candidateTasks` | task preview / dry-run | TaskGenerationDryRunPanel | Accordion | — |
| `pricingInputPreview` | pricing preview API | PricingInputPanel | Accordion | — |
| `rawWarnings` | breakdown.warnings technical group | MaterialBreakdownPanel | Accordion | — |
| `v3DryRunOutput` | production dry-run | IntakeV3ProductionTaskDryRunPanel | Accordion | — |
| `aiSuggestions` | AI assist API | AiSemanticAssistPanel | Accordion (off by default) | — |

**Builder propus:** `buildIntakeV4OperatorReviewViewModel(state, apiSnapshots)` în `frontend/src/lib/intakeV4/intakeV4OperatorReviewViewModel.ts` — pure function, testabil.

---

## 9. UI simplificat propus (Task H)

Regulă: *dacă nu ajută la următorul pas, nu e în UI principal.*

### Structură per step

#### Step 1 — Layers (File + Geometry decisions)

```text
1. Header compact (existent)
2. File card — preview, nume, dims, raster status, analysis save state
3. Work decision card — „Confirmă rolul straturilor" + pending count + layer table (simplified)
4. Operator action card — Save analysis / Confirm all / Next
5. Technical details accordion — GeometryPanel metrici perimetru, scope warnings
```

**Nu afișăm în principal:** Corel curve length, production parts count, nesting.

#### Step 2 — Review (Finish + Material)

```text
1. Header compact
2. File card (read-only mini)
3. Work decision card — Rezumat lucrare + backing/emblem + edge cant status
4. Finish sections (collapsible group) — letter groups, artwork, LED global
5. Material review card — status badge, selected m², override CTA, top 3 material rows
6. Operator action card — Save draft / Confirm finishes / blocker
7. Technical details accordion — EVERYTHING ELSE (single accordion)
```

**Nu afișăm în principal:** AI panel, ProductSystem ops count, full material table, nesting canvas, V3 dry-run, pricing preview, task lists.

#### Step 3 — Confirm

```text
1. Header compact
2. File card mini
3. Work + Finish summary (from ViewModel — 1 card)
4. Material review status (1 card)
5. Operator action card — handoff checkboxes + Create draft quote
6. Technical details — ConfirmOperationalSummary extended metrics
```

### Card specs

| Card | Afișează | Nu afișează | Acțiuni | Statusuri | Test |
|------|----------|-------------|---------|-----------|------|
| **File** | name, dims, preview, raster | hash, parser internals | Load SVG (step1) | ok/warn/error | `intake-v4-file-card` |
| **Work decision** | artwork, holes, layout, backing | vector parts, real_letters | backing toggles | — | `intake-v4-work-card` |
| **Material review** | status, m², source, override | quantity_basis raw | footprint save | ok_auto/review_* | sheet quote tests |
| **Operator action** | title, steps, primary CTA | — | Next/Save | blocked/ready | footer blocker tests |
| **Technical accordion** | geometry, nesting, dry-run | — | expand | — | collapsed by default |

---

## 10. Plan implementare în faze (Task I)

### Faza 1 — ViewModel read-only builder

| | |
|--|--|
| **Scop** | `buildIntakeV4OperatorReviewViewModel` + tests; zero UI change |
| **Fișiere** | `intakeV4OperatorReviewViewModel.ts`, `.test.ts`, wire minimal in hook for dev |
| **Riscuri** | Low — additive |
| **Teste** | Vitest fixtures Ana Maria / PBL geometry from existing tests |
| **Commit** | `feat(intake-v4): add operator review ViewModel builder` |
| **NU atinge** | Backend, CostEngine, DB |

### Faza 2 — UI recompus pe ViewModel (Review step)

| | |
|--|--|
| **Scop** | Review step: 6-zone layout; GeometryPanel doar step1; remove duplicate fetches where ViewModel centralizes |
| **Fișiere** | `IntakeV4ReviewStep.tsx`, new `IntakeV4*Card.tsx` atoms, `IntakeV4OperatorWorkspace.tsx` |
| **Riscuri** | Mediu — regression pe finish save flow |
| **Teste** | `IntakeV4OperatorUiPolish.test.tsx`, material breakdown tests |
| **Commit** | `refactor(intake-v4): recompose review step around operator ViewModel` |
| **NU atinge** | CostEngine, quote creation logic |

### Faza 3 — Technical details consolidation

| | |
|--|--|
| **Scop** | Un singur `IntakeV4TechnicalDetailsDrawer` per step; move AI, V3 dry-run, nesting canvas |
| **Fișiere** | `IntakeV4MaterialBreakdownPanel.tsx`, accordions, `IntakeV4ReviewStep.tsx` |
| **Riscuri** | Low-Med — testid moves |
| **Teste** | Existing accordion tests update |
| **Commit** | `refactor(intake-v4): consolidate technical details accordion` |
| **NU atinge** | Backend services |

### Faza 4 — Tests Ana Maria / PBL

| | |
|--|--|
| **Scop** | Vitest + optional Playwright smoke: ViewModel outputs match hard audit expectations |
| **Fișiere** | tests, fixtures from `backend/tests/fixtures/intake_v4/` |
| **Riscuri** | Low |
| **Teste** | PBL smoke spec, Ana Maria regression |
| **Commit** | `test(intake-v4): lock operator ViewModel against PBL and Ana Maria fixtures` |
| **NU atinge** | Production data |

### Faza 5 — Remove visible V3 language

| | |
|--|--|
| **Scop** | Rename „catalog V3”, wrap/replace `IntakeV3ProductionTaskDryRunPanel` cu V4 shell |
| **Fișiere** | Review technical section, dry-run panel adapter |
| **Riscuri** | Low — copy only + thin wrapper |
| **Teste** | grep snapshot tests for „V3" in operator DOM |
| **Commit** | `fix(intake-v4): remove V3 wording from operator-facing UI` |
| **NU atinge** | V3 routes/backend |

### Faza 6 — Owner review

| | |
|--|--|
| **Scop** | Owner mode: nesting canvas, candidate list, material snapshot export prominent |
| **Fișiere** | SheetQuoteReviewPanel owner sections, optional route query `?mode=owner` |
| **Riscuri** | Mediu — role gating TBD |
| **Teste** | Owner banner visibility |
| **Commit** | `feat(intake-v4): owner review surfaces for material and nesting` |
| **NU atinge** | CostEngine apply |

---

## 11. Ce eliminăm / păstrăm / mutăm (Task J)

### Păstrăm (capability)

- SVG analysis (nest2 client + persist bundle)  
- Material review + sheet quote candidates  
- Operator footprint override (`IntakeV4SheetFootprintOverridePanel`)  
- Reanalysis preview/execution history (owner notes — stale/fresh snapshot)  
- Technical diagnostics (consolidated accordion)  
- Finish setup per layer + LED sync  
- Quote handoff draft-only boundaries  
- Readiness gates (`intakeV4Readiness`)  
- Shared material review helpers (`intake-shared/*`)  

### Mutăm în detalii tehnice

- Child parts / layout parts breakdown methodology  
- `real_letters_count` / production vector parts  
- `candidate_tasks_count`, task preview lists  
- Bbox metrics, efficiency_percent, alternative layouts  
- V3/V4 dry-run output (tasks_json, ExecutionPlan)  
- Full material table (all rows, consumables breakdown)  
- CNC/print/cant operation rows  
- Pricing input preview  
- AI Informational Layer  
- Geometry perimeter table (4+ metrics)  
- Nesting canvas SVG  
- Commercial spine panel (pre-quote)  

### Ascundem complet din UI principal

- Raw field names (`needs_decision`, `quantity_basis`, `is_applied_to_quote`)  
- Internal layer ids (`_220…`) — sanitize only in details  
- „V3", „catalog V3", „IntakeV3*" component titles  
- ExecutionPlan / tasks_json labels  
- nest2 / path_geometry jargon in headings  
- Duplicate ProductSystem cards  
- Multiple „preview only" banners — **un disclaimer global**  

### Nu atingem acum

- CostEngine formulas / handlers  
- Quote final pricing / client send  
- Stock / inventory deductions  
- Production task creation  
- AI/OCR implementation  
- DB schema / migrations  
- WorkIntake V2 shell  

---

## 12. Riscuri

| Risc | Mitigare |
|------|----------|
| Operator pierde acces la metrici folosite zilnic | Faza 2 cu owner feedback; accordion default collapsed not removed |
| ViewModel drift vs API | Contract tests + hard audit fixtures |
| Regression finish save | Nu schimbăm payload shape; doar layout |
| Material review buried | Material review card promoted when `review_required` |
| Scope creep spre QuoteWizard | Confirm step rămâne draft-only boundary |

---

## 13. Ce nu facem acum

- Implementare cod (except acest doc)  
- Commit / push  
- Re-analysis SVG  
- DB mutations  
- Quote/order/task creation în studiu  
- CostEngine / stock changes  
- AI/OCR production rollout  
- Big-bang UI rewrite  

---

## 14. Verdict

Intake V4 are **fundament tehnic corect** dar **produs UI neconsolidat**: Review step expune paralel toate straturile de adevăr (file, geometry, nesting, material, commercial, production, debug) ca listă verticală de panouri. Operatorul nu are un singur „what do I do next?" — are 20 de carduri.

**Direcția:** un **ViewModel operator** + **6-zone layout** (file, work, material, action, finish group, technical accordion) cu regula strictă: principal = decizie, detalii = diagnostic.

**AI/OCR:** nu acum; rule-based blocker + copy RO + consolidare UI.

**Următorul pas recomandat:** Faza 1 — implementare `buildIntakeV4OperatorReviewViewModel` + teste fixture PBL/Ana Maria; review owner pe acest doc; apoi Faza 2 Review recomposition.

---

## Appendix A — Fișiere studiate

```text
frontend/src/pages/IntakeV4OperatorWorkspaceApp.tsx
frontend/src/components/workos/intake-v4/IntakeV4OperatorWorkspace.tsx
frontend/src/components/workos/intake-v4/steps/IntakeV4SvgAnalyzerStep.tsx
frontend/src/components/workos/intake-v4/steps/IntakeV4ReviewStep.tsx
frontend/src/components/workos/intake-v4/steps/IntakeV4ConfirmStep.tsx
frontend/src/components/workos/intake-v4/IntakeV4OperatorWorkSummary.tsx
frontend/src/components/workos/intake-v4/IntakeV4MaterialBreakdownPanel.tsx
frontend/src/components/workos/intake-v4/IntakeV4NestingPreviewPanel.tsx
frontend/src/components/workos/intake-v4/IntakeV4SheetQuoteReviewPanel.tsx
frontend/src/components/workos/intake-v4/IntakeV4SheetFootprintOverridePanel.tsx
frontend/src/components/workos/intake-v4/IntakeV4GeometryPanel.tsx
frontend/src/components/workos/intake-v4/IntakeV4SvgPreviewCanvas.tsx
frontend/src/lib/intakeV4/intakeV4ConfirmSummary.ts
frontend/src/lib/intakeV4/intakeV4Readiness.ts
frontend/src/lib/intakeV4/intakeV4OperatorUiDisplay.ts
frontend/src/lib/intake-shared/materialReviewStatus.ts
docs/audit/INTAKE_V4_OPERATOR_UI_COUNTS_HARD_AUDIT.md
docs/qa/BUILD_INTAKE_V4_ATOMS_OPERATOR_WORKSPACE.md
```
