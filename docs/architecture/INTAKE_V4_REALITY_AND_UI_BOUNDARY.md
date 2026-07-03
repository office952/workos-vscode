# Intake V4 — Reality and UI Boundary

**Date:** 2026-06-24  
**Branch:** `local/integration-pr4-plus-svg-path`  
**HEAD:** `53173da`  
**Status:** Canonical reference for Cursor / owner / development  
**Mode:** Architecture documentation — not a UI spec pixel-perfect  

**Related docs:**

- `docs/audit/INTAKE_V4_OPERATOR_UI_PRODUCT_LOGIC_STUDY.md`
- `docs/audit/INTAKE_V4_OPERATOR_UI_COUNTS_HARD_AUDIT.md`
- `docs/audit/INTAKE_V4_ALIGNMENT_AUDIT.md`
- `docs/qa/BUILD_INTAKE_V4_OPERATOR_UI_TRUST_ALIGNMENT.md`
- `docs/qa/BUILD_INTAKE_V4_ATOMS_OPERATOR_WORKSPACE.md`

**Rule for this document:** Adevărul tehnic trăiește aici. UI-ul principal **nu** trebuie să repete acest document ca badge-uri, banner-e sau paragrafe lungi.

---

## 1. Verdict scurt

Intake V4 **nu trebuie tratat ca un ecran tehnic complet**.

Intake V4 **trebuie tratat ca un flow de decizie operator**.

UI-ul principal trebuie să afișeze **doar ce ajută omul să decidă următorul pas**.

Adevărul tehnic rămâne în **documentație** (acest fișier) și în **technical details** (un singur accordion collapsed), **nu** în zona principală.

Nu adăugăm noise vizual (badge peste badge, „preview only” repetat, explicații lungi în carduri) ca substitut pentru arhitectură clară.

---

## 2. Ce urmărim de fapt

### Direcția produs

```text
Fișier client / SVG
  → analiză tehnică (nest2 / svgAnalyzer)
  → interpretare controlată (layer roles, template rules)
  → verificare operator (finish, backing, artwork execution)
  → material review (selected area, override, manual verification)
  → readiness pentru draft quote intern
  → abia mai târziu: CostEngine / ofertă finală / producție
```

### Ce este Intake V4 acum

| Afirmație | Adevăr |
|-----------|--------|
| Intake V4 **nu** este încă motor final de ofertare | Da — produce `pricing_input` snapshot și draft quote boundary, nu preț client final |
| Intake V4 **nu** este încă motor final de producție | Da — dry-run și task preview sunt informative |
| Intake V4 **este** stație de interpretare și review | Da — SVG → geometry → operator decisions → material review gate |

### Route operator

- `/intake-v4/:workspaceId/operator` — shell Atoms 3-step: `layers` → `review` → `confirm`
- Cod: `IntakeV4OperatorWorkspaceApp`, `IntakeV4OperatorWorkspace`, `useIntakeV4Workspace`

---

## 3. Ce este REAL acum

„Real” = persistat sau calculat determinist din snapshot analiză + confirmări operator, cu contract testat. Nu înseamnă „gata de producție” sau „preț final”.

| Capability | Unde în cod | Stabil? | UI principal? | Ofertă finală? | Producție? |
|------------|-------------|---------|---------------|----------------|------------|
| **Upload / SVG source** | `useIntakeV4Workspace`, payload `svg_source`, `intake_v4_workspace_service` | Da | Da — file card | Input | Input |
| **Analiză SVG (client nest2)** | `lib/svgAnalyzer`, `IntakeV4SvgAnalyzerStep` | Da (pilot) | Da — status analiză | Input | Input |
| **Preview geometric** | `IntakeV4SvgPreviewCanvas`, `state.svg.previewSource` | Da | Da | Nu | Nu |
| **Layer detection** | `analyzerReport.layers`, nest2 parse | Da | Da — layer table step 1 | Input | Input |
| **Layer role confirmation** | `intakeV4LayerRoleBridge`, PUT layer roles, payload `layer_role_setup` | Da | Da — decizie operator | Input | Input |
| **Geometry metrics (persisted)** | `intake_v4_quote_geometry_service`, `path_geometry_summary`, `intakeV4QuoteGeometry` | Da | Parțial — outcome, nu raw perimetre | Input draft | Input planificare |
| **Material breakdown compute** | `intake_v4_material_breakdown_service`, `GET .../material-breakdown` | Da (estimativ) | Nu — doar total/review | **Nu direct** | **Nu** |
| **Sheet quote material candidates** | `intake_v4_sheet_quote_candidate_policy_service`, breakdown embed | Da | Da — când review activ | Boundary review | Nu |
| **Selected material review area** | `selected_quote_sheet_area_sqm`, `sheet_quote_material_candidates.selection` | Da | Da | **Nu aplicat** (`is_applied_to_quote=false`) | Nu |
| **Manual footprint override** | `intake_v4_sheet_footprint_override_service`, `IntakeV4SheetFootprintOverridePanel` | Da | Da — când manual review | Estimare internă | Nu |
| **`isAppliedToQuote=false`** | Policy enforced backend + UI copy | Da — invariant | Da — „Neaplicat în ofertă finală” | **Nu** | **Nu** |
| **Re-analysis preview** | `intake_v4_reanalyze_preview_service` — read-only diff | Da | Owner note / technical | Nu | Nu |
| **Controlled re-analysis (Ana Maria)** | Documentat `9c1659b`, fixture `ana_maria_post_reanalysis_metrics.json` | Executat controlat | Technical / owner | Nu | Nu |
| **Technical diagnostics** | Grouped warnings, geometry metric display, nesting parts | Da | Technical accordion | Debug | Debug |
| **Quote handoff draft-only boundary** | `intake_v4_internal_draft_quote_policy_service`, `IntakeV4ConfirmStep` | Da | Confirm step only | Draft intern | **Nu** order/tasks/stock |
| **Finish setup (confirmed)** | payload `finish_setup`, `intake_v4_finish_truth_service` | Da | Da — finish forms | Input draft | Input planificare |
| **Readiness status** | workspace `readiness_status`, `intakeV4Readiness` | Da | Badge + blocker | Gate | Gate |
| **ProductSystem binding** | `intake_v4_product_system_service` | Da (volumetric) | Subtitle, nu catalog debug | Template context | Template context |
| **File hash / analysis identity** | `intakeV4AnalysisIdentity`, `client_analysis_hash` | Da | Technical | Handoff sync | Handoff sync |

### Invariante REAL importante

1. **`selection.is_applied_to_quote === false`** — selected review area **nu** intră automat în CostEngine / preț client.
2. **Fără stock consumption** — nesting și breakdown nu scad inventory.
3. **Fără task generation real** — dry-run nu creează task-uri în DB.
4. **Draft quote** necesită confirmări explicite (`confirm_no_order`, `confirm_no_execution`, `confirm_no_inventory`).

---

## 4. Ce NU este real / final

| Item | De ce nu este real | Risc dacă e afișat ca real | Unde rămâne |
|------|-------------------|---------------------------|-------------|
| **CostEngine final pentru Intake V4** | CostEngine rulează în QuoteWizard; V4 produce `pricing_input` preview | Preț greșit acceptat de client | QuoteWizard — out of scope V4 UI |
| **Quote final automat din V4** | Doar `createIntakeV4DraftQuote` — draft intern | Trimitere comercială prematură | Confirm step cu boundaries |
| **Preț client final** | Lipsesc markup, governance, approval | Pierdere marjă / litigii | Commercial document flow |
| **Stock consumption** | Explicit out of scope | Deduceri inventar false | Nu există — păstrăm așa |
| **Task generation real** | `task_generation_dry_run` = simulate | Producție pornită fără order | Technical accordion |
| **ExecutionPlan real** | Nu se creează din V4 operator | Handoff producție invalid | Ascuns |
| **tasks_json real** | Nu persistat din preview | Confuzie operațională | Ascuns |
| **AI semantic truth** | `mock_suggestions`, informational contract | Roluri/material greșite auto-aplicate | Technical / disabled |
| **OCR / character count truth** | Curbe ≠ caractere vizibile | Număr litere greșit la producție | **Interzis** |
| **Production-ready material consumption** | Nesting = estimare layout, nu consum atelier | Comandă material greșită | Preview only |
| **Missing prices în breakdown** | `price_source: missing` — fallback | Cost „oficial” inventat | Owner `/inventory/pricing` |

---

## 5. Ce este doar PREVIEW

Preview = **ajută la decizie**, dar **nu produce efect final** (fără persist comercial/producție/stock).

| Preview | Sursă | UI recomandat | Nu confunda cu |
|---------|-------|---------------|----------------|
| **Nesting preview** | `intake_v4_nesting_preview_service`, `IntakeV4NestingPreviewPanel` | Technical | Consum stoc, layout producție final |
| **Material breakdown rows** | `intake_v4_material_breakdown_service` | Technical (+ status summary în principal) | Factură / CostEngine total |
| **Selected review area** | sheet quote candidates | Principal (m² + sursă) | Arie facturată clientului |
| **Pricing input preview** | `intake_v4_pricing_input_service` | Technical | Preț ofertă |
| **Quote handoff preview** | `intake_v4_internal_draft_quote_policy_service` | Confirm | Quote acceptat |
| **Task dry-run preview** | `intake_v4_production_task_dry_run_service`, V3 panel adapter | Technical | Task-uri create |
| **Commercial spine preview** | `getIntakeV4CommercialSpineState` | Technical / post-quote | Document client |
| **Candidate tasks** | task preview / dry-run counts | Technical | Backlog producție |
| **Sheet/roll alternatives** | nesting `is_active_for_breakdown=false` | Technical | Layout activ pentru material |

### Copy permis în UI principal (scurt, o singură dată)

- „Estimare internă — nu preț final”
- „Neaplicat în ofertă finală”

### Copy de eliminat din UI principal (noise)

- Repetarea „preview only / nu consumă stoc / catalog V3” în fiecare card
- `efficiency_percent`, `quantity_basis`, `bbox` în headings

---

## 6. Ce este MOCK / experimental

| Componentă | Unde | Status |
|------------|------|--------|
| **AI semantic assist panel** | `IntakeV4AiSemanticAssistPanel`, `intake_v4_ai_semantic_classification_service` | Mock suggestions — `AI_INFORMATIONAL_LAYER_CONTRACT` |
| **AI informational layer** | `getIntakeV4AiInformationalAssistCandidate` | Non-binding |
| **OCR** | Discutat, **neimplementat** | Interzis ca sursă de adevăr |
| **Polygon nesting sandbox (non-canonical)** | svg-analyzer-vs legacy | **Nu** canonical — nest2 child-parts only |
| **V3 task preview ca demo** | „Task preview producție (catalog V3)” | Adapter demo — nu producție |

### Reguli mock

- Mock **nu** în UI principal operator
- Mock **nu** la ofertă
- Mock **nu** la producție
- Mock poate rămâne collapsed în technical details sau flag-off până la contract owner

---

## 7. Ce este V3 intern — nu trebuie să apară ca V3 în UI V4

| V3 intern | Locație V4 | Regulă UI |
|-----------|------------|-----------|
| V3 dry-run panels | `IntakeV3ProductionTaskDryRunPanel` în Review accordion | Wrapper V4 fără titlu „V3” |
| V3 production task preview | Task preview card | „Preview operații” — fără „catalog V3” |
| V3 catalog wording | `IntakeV4ReviewStep` task preview heading | Eliminat în Faza 5 |
| Legacy handoff labels | Parțial curățat | RO operator-facing only |
| V3 adapters (pricing/production) | `intake_v4_*` services calling V3 chains | Backend OK — UI ascunde originea |

**Regulă:** V3 poate exista temporar ca **adapter intern**. V3 **nu** trebuie să apară ca **limbaj vizibil** în UI V4.

---

## 8. Ce este bun în Intake V4

Fără exagerare — acestea sunt boundary-uri corecte de produs:

| Lucru bun | De ce |
|-----------|-------|
| **Selected review area separată de quote final** | Owner poate verifica m² fără a polua CostEngine |
| **`isAppliedToQuote=false` invariant** | Fail-closed comercial — nu aplicăm automat estimări nesting |
| **Manual footprint override** | Operator corectează când SVG/nesting nu reflectă realitatea atelier |
| **Reanalysis preview (read-only)** | Owner vede diff înainte de execuție destructivă |
| **Controlled reanalysis (Ana Maria)** | Dovadă că pipeline-ul poate fi refăcut controlat |
| **Material review warnings** | `requires_manual_review`, stale/fresh snapshot — acționabile |
| **Layer role confirmation** | Separă analiză automată de decizie umană |
| **Technical diagnostics** | Dev/owner pot audita fără a aglomera operatorul |
| **Draft-only quote boundary** | Checkboxes + policy — fără order/execution/inventory |
| **Lipsa stock consumption** | Nesting rămâne estimativ |
| **Lipsa task generation real** | Dry-run rămâne dry-run |
| **Client nest2 + persist bundle** | Un singur engine SVG vs dual-truth V3 server parse |
| **Reducer cu clear on re-upload** | Evită stale UI V3 |

---

## 9. Ce este greșit / confuz acum

Onest — starea UI la HEAD `53173da`:

| Problemă | Detaliu |
|----------|---------|
| **UI prea aglomerat** | Review step: ~12 panouri verticale |
| **Prea multe panouri** | Geometry duplicat step 1+2, ProductSystem de 2 ori |
| **Prea multe warnings vizibile** | operator + quoting + stale + pending save + preview banners |
| **Informații tehnice în zona principală** | GeometryPanel cu 4+ perimetre; AI panel în principal |
| **V3 expus în V4** | Dry-run panel, „catalog V3” |
| **`candidate_tasks_count` confundabil** | Număr task dry-run pare backlog real |
| **`real_letters_count` / production vector parts confundabil** | Par litere vizibile — mutat parțial în technical (53173da) |
| **Nesting/material/quote/task preview amestecate** | MaterialBreakdownPanel = mega-card |
| **Operatorul nu vede clar next action** | SmartBanner există, dar e îngropat în noise |
| **UI arată ca debug screen** | Badge-uri, tabele tehnice, disclaimere repetitive |

**Notă:** Trust alignment (`BUILD_INTAKE_V4_OPERATOR_UI_TRUST_ALIGNMENT`) a îmbunătățit **copy**, nu **structura**. Următorul pas = arhitectură UI, nu încă un strat de text.

---

## 10. Regula UI principal

```text
Dacă informația nu ajută operatorul să decidă următorul pas, nu stă în UI principal.
```

### UI principal poate afișa DOAR

| Element | Exemplu |
|---------|---------|
| Fișier | `pbl-layere.svg` |
| Preview | canvas SVG |
| Dimensiuni | 5000 × 600 mm |
| Status fișier | analiză salvată / raster lipsă |
| Decizii layer/finish | roluri, 651/8500, cant, backing |
| Artwork/logo | count simplu |
| Goluri/interioare | count simplu |
| Piese plasate în layout | dacă label RO clar — altfel technical |
| Material review | arie selectată m², sursă, **Neaplicat în ofertă finală** |
| Verificare operator | review_required badge + CTA override |
| Următorul pas | un singur mesaj + buton |

### UI principal NU afișează

- Disclaimere lungi repetate
- Tabele complete material/CNC/print
- Dry-run output
- AI suggestions
- Raw tokens (`needs_decision`, `quantity_basis`)
- Metrici perimetru multiple simultan

---

## 11. Ce se mută în detalii tehnice

Un singur accordion **collapsed by default** per step:

```text
- child parts / childPartsCount methodology
- real_letters_count
- production vector parts (Piese vectoriale de producție detectate)
- nestable parts
- placements breakdown
- bbox metrics
- face union
- layout alternatives
- efficiency_percent
- quantity_basis / quantity_source
- confidence labels
- candidate_tasks_count
- V3/V4 dry-run output
- pricing input preview
- task preview list
- raw warnings (technical group)
- internal layer ids (_220…)
- nesting canvas SVG
- commercial spine (pre-quote)
- AI mock suggestions
- geometry perimeter table (Corel vs LED vs CNC vs cant)
- reanalysis before/after diff (owner)
```

---

## 12. Ce nu se afișează deloc operatorului

```text
- internal DB ids (workspace UUID în UI prominent)
- raw field names (is_applied_to_quote, real_letters_count)
- tasks_json
- ExecutionPlan
- CostEngine internals / formula handlers
- stock internals / inventory deductions
- V3 labels („catalog V3”, „IntakeV3*”)
- AI mock suggestions în principal
- OCR guesses / character count
- debug-only warnings (technical group) — doar în support mode
- nest2 config ids, part_id slices în canvas labels (sanitized)
```

---

## 13. AI / OCR decision

### Interzis acum

```text
Nu folosim OCR pentru numărat litere vizibile.
Nu folosim AI ca sursă de adevăr pentru material, arie, cost sau producție.
```

### Motiv

- SVG curbe ≠ text editabil; OCR pe preview e unreliable pentru producție.
- AI mock (`mock_suggestions`) nu are contract de acuratețe pentru pricing.

### Permis mai târziu (cu boundary)

```text
AI poate ajuta doar ca text explicativ sau sumarizare warnings,
cu confirmare umană explicită — niciodată auto-apply pe finish, material sau quote.
```

Referință: `docs/architecture/AI_INFORMATIONAL_LAYER_CONTRACT.md`

---

## 14. Model modular recomandat

Module simple — fiecare răspunde la **o întrebare**, nu la un catalog API.

### 1. File Check

| | |
|--|--|
| **Întrebare** | Ce a trimis clientul și e utilizabil? |
| **Input** | SVG file, `svg_source`, analyzer status |
| **Output** | fileName, dims, valid/invalid, raster missing |
| **UI** | Principal |
| **NU face** | Quote, nesting, tasks |

### 2. Visual Preview

| | |
|--|--|
| **Întrebare** | Arată corect ce am primit? |
| **Input** | `previewSource`, raster flags |
| **Output** | Canvas + status preview |
| **UI** | Principal |
| **NU face** | OCR, character count |

### 3. Layer / Role Decision

| | |
|--|--|
| **Întrebare** | Ce reprezintă fiecare strat? |
| **Input** | analyzer layers, auto-role, confirmation |
| **Output** | confirmed roles, pending count |
| **UI** | Principal (step 1) |
| **NU face** | Nesting placement |

### 4. Geometry Summary

| | |
|--|--|
| **Întrebare** | Ce producem (outcome)? |
| **Input** | quote_geometry, metrics display |
| **Output** | artwork count, holes, layout parts — **nu** production parts în principal |
| **UI** | Principal (minimal) + Technical (perimetre) |
| **NU face** | Preț, consum material |

### 5. Material Review

| | |
|--|--|
| **Întrebare** | Ce arie folosim pentru estimarea internă? |
| **Input** | sheet_quote_material_candidates, override |
| **Output** | selected m², source, review status, applied-to-quote: Nu |
| **UI** | Principal când activ |
| **NU face** | CostEngine apply, stock |

### 6. Manual Verification

| | |
|--|--|
| **Întrebare** | Trebuie să corectez manual? |
| **Input** | requires_manual_review, stale snapshot |
| **Output** | CTA footprint override, owner reanalysis note |
| **UI** | Principal (condiționat) |
| **NU face** | Auto reanalysis |

### 7. Quote Readiness Preview

| | |
|--|--|
| **Întrebare** | Pot crea draft intern? |
| **Input** | handoff preview, finish confirmed, binding blockers |
| **Output** | allowed/blocked + motiv scurt |
| **UI** | Confirm step |
| **NU face** | Quote final, order, tasks |

### 8. Technical Details

| | |
|--|--|
| **Întrebare** | Ce știe sistemul tehnic (audit)? |
| **Input** | Toate API preview/dry-run/debug |
| **Output** | Full diagnostic |
| **UI** | Technical accordion |
| **NU face** | Decizie automată |

---

## 15. ViewModel recomandat

Single read model — traduce adevărul tehnic (acest doc) în UI simplu.

```ts
/** frontend/src/lib/intakeV4/intakeV4OperatorReviewViewModel.ts — proposed */
export interface IntakeV4OperatorReviewViewModel {
  fileCheck: IntakeV4VmFileCheck;
  visualPreview: IntakeV4VmVisualPreview;
  layerDecision: IntakeV4VmLayerDecision;
  geometrySummary: IntakeV4VmGeometrySummary;
  materialReview: IntakeV4VmMaterialReview;
  manualVerification: IntakeV4VmManualVerification;
  quoteReadiness: IntakeV4VmQuoteReadiness;
  technicalDetails: IntakeV4VmTechnicalDetails;
}
```

### Mapare secțiuni

| Secțiune | Conține | Sursă actuală | UI principal | Technical |
|----------|---------|---------------|--------------|-----------|
| **fileCheck** | fileName, size, dims, analysisPersisted, fileHash | workspace payload, analyzer report | Da | hash full |
| **visualPreview** | previewStatus, missingRaster | SvgPreviewCanvas flags | Da | parser warnings |
| **layerDecision** | pendingRoles, confirmedRoles, layerCount | layer_role_setup, layer chips | Da (step 1) | layer ids |
| **geometrySummary** | artworkCount, innerHoles, layoutParts | `buildIntakeV4OperatorWorkSummaryCounts` | Da | productionParts, perimetre |
| **materialReview** | selectedSqm, sourceLabel, appliedToQuote:false, reviewStatus | material breakdown candidates | Da | candidates table, bbox |
| **manualVerification** | requiresManualReview, staleSnapshot, overrideSaved | sheet quote policy, override payload | Da (condiționat) | reanalysis diff |
| **quoteReadiness** | finishConfirmed, handoffAllowed, blockers | readiness, handoff preview | Confirm | pricing preview |
| **technicalDetails** | nesting, dry-runs, warnings raw, AI mock | toate GET preview endpoints | Nu | Da |

### Builder

```text
buildIntakeV4OperatorReviewViewModel(state, apiSnapshots) → pure function, Vitest fixtures PBL/Ana Maria
```

Nu duplică calcule backend — **agregă și clasifică** pentru UI boundary.

---

## 16. Plan de implementare

### Faza 1 — Reality boundary doc ✓

| | |
|--|--|
| **Scop** | Acest document — single truth for dev |
| **Schimbă** | `docs/architecture/INTAKE_V4_REALITY_AND_UI_BOUNDARY.md` |
| **NU atinge** | Cod |
| **Test** | Review owner |

### Faza 2 — ViewModel read-only builder

| | |
|--|--|
| **Scop** | `buildIntakeV4OperatorReviewViewModel` + tests |
| **Schimbă** | `frontend/src/lib/intakeV4/intakeV4OperatorReviewViewModel.ts` |
| **NU atinge** | Backend, UI layout |
| **Test** | Vitest PBL + Ana Maria expected values |

### Faza 3 — Module UI simple

| | |
|--|--|
| **Scop** | 6-zone layout Review; elimină duplicate GeometryPanel |
| **Schimbă** | `IntakeV4ReviewStep`, new `*Card` components |
| **NU atinge** | CostEngine, payload shapes |
| **Test** | `IntakeV4OperatorUiPolish.test.tsx`, confirm step tests |

### Faza 4 — Technical details consolidation

| | |
|--|--|
| **Scop** | Un accordion; mută AI, dry-run, nesting canvas, full tables |
| **Schimbă** | MaterialBreakdownPanel split display vs technical |
| **NU atinge** | Breakdown compute |
| **Test** | MaterialBreakdownPanel tests — testids moved |

### Faza 5 — Remove visible V3 language

| | |
|--|--|
| **Scop** | V4 wrapper for dry-run; rename headings |
| **Schimbă** | Review technical section copy |
| **NU atinge** | V3 backend routes |
| **Test** | grep snapshot: no „V3" in operator DOM |

### Faza 6 — Owner review

| | |
|--|--|
| **Scop** | Nesting canvas, snapshot export, reanalysis diff prominent for owner |
| **Schimbă** | SheetQuoteReviewPanel owner mode |
| **NU atinge** | CostEngine apply |
| **Test** | Owner banner visibility |

### Faza 7 — CostEngine / quote final / production handoff

| | |
|--|--|
| **Scop** | **Abia după** material review owner-approved boundary |
| **Schimbă** | QuoteWizard integration, eventual `is_applied_to_quote` policy change — **decizie separată** |
| **NU atinge** | Fără skip pe Faze 2–6 |
| **Test** | Dedicated BUILD + pytest pricing regression |

---

## 17. Reguli pentru dezvoltare viitoare

Reguli stricte — pentru Cursor, owner, orice PR Intake V4:

```text
1. Nu adăuga badge/warning nou în UI principal fără decizie clară documentată aici.
2. Nu expune field raw în UI principal (folosește copy RO din intakeV4OperatorUiDisplay / intake-shared).
3. Nu expune V3 în V4 (adapters OK backend, nu titluri UI).
4. Nu afișa preview ca adevăr final (o etichetă scurtă e suficientă).
5. Nu lega CostEngine până când material review are owner-approved boundary.
6. Nu crea taskuri reale din preview / dry-run.
7. Nu folosi OCR pentru adevăr de producție.
8. Nu adăuga AI fără human confirmation contract.
9. Nu duplica panouri între steps (DRY ViewModel).
10. Nu adăuga „preview only" banner per card — boundary e global în doc + un hint scurt.
11. Orice counter nou: documentează entitatea numărată în acest fișier înainte de UI.
12. Fail-closed: missing data → blocker, nu default silent.
```

### Anti-patterns explicit interzise

- Badge peste badge (status + warning + preview + missing price simultan pe același card)
- Explicații de 3+ rânduri în card principal
- Tabele tehnice full-width în Review principal
- Componente noi informaționale fără `operatorAction` linkage

---

## 18. Concluzie

Intake V4 trebuie **simplificat prin arhitectură**, nu prin încă un layer vizual de avertizări.

- **UI principal** = flow de decizie (file → layer → finish → material review → draft readiness).
- **Acest document** = adevărul tehnic (real / preview / mock / V3 intern).
- **ViewModel** = traducere deterministă doc → UI simplu.
- **Technical details** = audit și owner, collapsed.

Următorul pas recomandat: **Faza 2** — ViewModel builder + teste fixture, fără schimbări vizuale majore până la review owner pe acest boundary doc.

---

## Appendix A — Code map (quick reference)

```text
Frontend shell:     frontend/src/components/workos/intake-v4/IntakeV4OperatorWorkspace.tsx
Steps:              steps/IntakeV4SvgAnalyzerStep | Review | Confirm
State:              frontend/src/lib/intakeV4/useIntakeV4Workspace.ts
API client:         frontend/src/lib/intakeV4/intakeV4Api.ts
Readiness:          frontend/src/lib/intakeV4/intakeV4Readiness.ts
Material review UI: IntakeV4SheetQuoteReviewPanel, intake-shared/materialReview*
Backend router:     backend/routers/intake_v4_workspaces.py
Material breakdown: backend/services/intake_v4_material_breakdown_service.py
Sheet quote policy: backend/services/intake_v4_sheet_quote_candidate_policy_service.py
Draft quote policy: backend/services/intake_v4_internal_draft_quote_policy_service.py
Reanalysis preview: backend/services/intake_v4_reanalyze_preview_service.py
SVG engine:         frontend/src/lib/svgAnalyzer/
```

## Appendix B — Fixture references (operator counts)

| Workspace | Principal (trust alignment) | Technical production parts |
|-----------|----------------------------|----------------------------|
| Ana Maria | 2 artwork · 7 goluri · 21 layout · 6 layere | 19 vector parts |
| PBL | 1 · 2 · 11 · 3 layere | 10 vector parts |

Material review ambele: **Neaplicat în ofertă finală** (`is_applied_to_quote=false`).

---

*Document version: 1.0 — 2026-06-24 — HEAD 53173da*
