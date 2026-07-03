# Intake V4 — Drastic UI Simplification Audit (Operator Review)

**Date:** 2026-06-24  
**Branch:** `local/integration-pr4-plus-svg-path`  
**HEAD:** `d8b5a34` (`feat(intake-v4): show face-back prep CNC cost draft`)  
**Mode:** read-only audit — **no code, no commit, no push**

---

## 1. Verdict scurt

Intake V4 Review este **supraîncărcat**: operatorul vede simultan geometrie multi-perimetru, contoare tehnice, finisaje, estimări materiale, dry-run V3 și panoul nou Face/Back Prep — majoritatea **fără ierarhie clară** între decizie operator vs debug.

**Recomandare:** restructurare în **3 zone** (Operator summary → Review actions → Technical details collapsed), cu **max 5–6 câmpuri** în summary principal: fișier, lățime, înălțime, **perimetru total vectorial**, template/proces, status. Tot restul metricilor paralele, dry-run-urile și tabelele dense **mutate sau eliminate** din fluxul principal.

Perimetrul vectorial rămâne **adevărul de calcul** (backend neschimbat); UI principal afișează **un singur** perimetru canonic pentru operator, nu 6–8 variante.

---

## 2. Scope

| In scope | Out of scope |
|----------|--------------|
| Inventar UI Review + Layers + Confirm (operator-facing) | Implementare UI |
| Recomandări move/remove/replace | Backend, SVG analysis, nesting, pass-count, CostEngine |
| Layout + terminologie + faze | ProductSystem registry, quote/order/tasks, stock |
| Clasificare warnings | Modificare endpoint Face/Back Prep |

**Docs studiate:**

| Document | Status |
|----------|--------|
| `docs/audit/INTAKE_V4_OPERATOR_UI_PRODUCT_LOGIC_STUDY.md` | ✓ |
| `docs/audit/INTAKE_V4_OPERATOR_UI_COUNTS_HARD_AUDIT.md` | ✓ |
| `docs/qa/BUILD_INTAKE_V4_OPERATOR_UI_TRUST_ALIGNMENT.md` | ✓ |
| `docs/qa/BUILD_INTAKE_V4_FACE_BACK_PREP_COST_DRAFT_UI_PANEL_READ_ONLY.md` | ✓ |
| `docs/architecture/TPL_VOLUMETRIC_FACE_BACK_PREP_TEMPLATE_CONTRACT.md` | ✓ (referință cost draft) |
| `docs/qa/FIX_TPL_VOLUMETRIC_FACE_BACK_PREP_CNC_PASS_COUNTS_AND_VECTOR_PERIMETER_TRUTH.md` | ✓ |

---

## 3. Surse citite (cod)

| Area | Paths |
|------|-------|
| Review step | `frontend/src/components/workos/intake-v4/steps/IntakeV4ReviewStep.tsx` |
| Layers step | `frontend/src/components/workos/intake-v4/steps/IntakeV4SvgAnalyzerStep.tsx` |
| Confirm step | `frontend/src/components/workos/intake-v4/steps/IntakeV4ConfirmStep.tsx`, `IntakeV4ConfirmOperationalSummary.tsx` |
| Geometry | `IntakeV4GeometryPanel.tsx`, `intakeV4GeometryMetricDisplay.ts`, `intakeV4QuoteGeometry.ts` |
| Summary | `IntakeV4OperatorWorkSummary.tsx`, `IntakeV4OperatorWorkSummaryTechnicalDetails.tsx` |
| Materials | `IntakeV4MaterialBreakdownPanel.tsx` (+ nesting/sheet accordions) |
| Face/Back draft | `IntakeV4FaceBackPrepCostDraftPanel.tsx` |
| Finishes / cant | `IntakeV4LetterGroupFinishesSection.tsx`, `IntakeV4EdgeCantReviewCard.tsx`, … |
| Technical shell | `atoms/IntakeV4TechnicalDetailsAccordion.tsx` |
| Workspace shell | `IntakeV4OperatorWorkspace.tsx`, header/status/progress |

---

## 4. Inventar UI actual

### 4.1 Review step — zonă principală (înainte de accordion)

| Panel | Component | Current location | Data shown | Audience | Recommendation |
|-------|-----------|------------------|------------|----------|----------------|
| ProductSystem binding | inline card | Review top | template label, operation count | Mixed | **Move → debug** sau 1 linie în summary |
| Rezumat lucrare | `IntakeV4OperatorWorkSummary` | Review main | artwork, goluri, layout parts, layere SVG | Operator | **Simplify → 2–3 rows max** sau mută goluri/layout în debug |
| Geometrie quote | `IntakeV4GeometryPanel` | Review main | 4 contoare, 5+ perimetre, arii, cant section, goluri, warnings | **Debug masquerading as main** | **Replace** cu card compact 3 câmpuri; **move full panel → debug** |
| Backing & emblem | `IntakeV4BackingAndEmblemSection` | Review main | backing_mode, emblem lighting | Operator decision | **Keep** în Review actions |
| Cant review | `IntakeV4EdgeCantReviewCard` | Review main | cant/volum, Oracal impact preview | Operator (decizie) | **Keep** (decizie finisaj) |
| AI semantic assist | `IntakeV4AiSemanticAssistPanel` | Review main | mock AI suggestions | Developer | **Move → debug** sau **remove** din operator |
| Finisaje per grup | `IntakeV4LetterGroupFinishesSection` | Review main | face/cant per letter group | Operator | **Keep** |
| Artwork complexity | `IntakeV4ArtworkComplexityCard` | Review main | vinyl/print decisions | Operator (conditional) | **Keep** când există artwork |
| Finisaje artwork | `IntakeV4ArtworkFinishSection` | Review main | per-layer artwork finish | Operator | **Keep** când există artwork |
| Setări globale / LED | inline form | Review main | Oracal 651, cant global, LED, PSU, module counts | Operator + **tehnic LED** | **Split**: LED summary compact; detalii module → debug |
| Estimare materiale | `IntakeV4MaterialBreakdownPanel` | Review main | tables materiale, consumabile, CNC rows, warnings, sheet review | Mixed quote/internal | **Move tables → debug**; **Keep** compact: total est. + blocaje + sheet review dacă manual |
| Blocked banner | inline | Review | analysis not ready | Operator | **Keep** |

### 4.2 Review step — Detalii tehnice / debug (accordion, default closed)

| Panel | Component | Data shown | Recommendation |
|-------|-----------|------------|----------------|
| Contoare geometrie | `IntakeV4OperatorWorkSummaryTechnicalDetails` | piese vectoriale producție, notă anti-OCR | **Keep in debug** ✓ |
| Face/Back CNC draft | `IntakeV4FaceBackPrepCostDraftPanel` | full tables, formulas, pass_count, tasks, warnings | **Split**: compact card în main; **detalii rămân aici** |
| V3 production dry-run | `IntakeV3ProductionTaskDryRunPanel` | V3 task candidates, internal naming | **Keep in debug**; hide V3 label în main |
| Pricing input preview | `IntakeV4PricingInputPanel` | quote_input keys | **Keep in debug** |
| Production handoff | `IntakeV4ProductionHandoffPreviewPanel` | handoff preview | **Keep in debug** |
| Task generation dry-run | `IntakeV4TaskGenerationDryRunPanel` | candidate tasks | **Keep in debug** |
| Order-bound readiness | `IntakeV4OrderBoundTaskReadinessPanel` | quote/order linkage | **Keep in debug** (pre-quote) |
| Commercial spine | `IntakeV4QuoteCommercialSpinePanel` | quote spine actions | **Amână** sau debug-only până la confirm |
| Task preview V3 | inline card | catalog V3 operations | **Keep in debug** |

### 4.3 Layers step (Step 1)

| Panel | Component | Recommendation |
|-------|-----------|----------------|
| Upload + preview | `IntakeV4Nest2SvgUploader`, `IntakeV4SvgPreviewCanvas` | **Keep** — core |
| Dimensiuni + straturi summary | inline | **Keep** — merge în viitorul Operator summary |
| Geometrie quote | `IntakeV4GeometryPanel` | **Remove from Layers** — duplicat; doar în debug sau după simplificare |
| Layer roles table | inline | **Keep** — core decision |

### 4.4 Confirm step (Step 3)

| Panel | Component | Recommendation |
|-------|-----------|----------------|
| Summary card | inline | **Keep** |
| Operational summary | `IntakeV4ConfirmOperationalSummary` | **Simplify** — multe secțiuni repetă Review; păstrează checklist + blockers |
| Quote handoff | inline | **Keep** — acțiune finală |

### 4.5 Material breakdown — sub-panouri (unele în accordion intern)

| Sub-panel | Recommendation |
|-----------|----------------|
| Nesting nest2 summary | **Debug** ✓ (deja parțial) |
| Nesting canvas | **Debug** ✓ |
| Sheet quote review + footprint override | **Keep visible** când `requires_manual_review` |
| CNC operation rows din breakdown | **Debug** (suprapune Face/Back draft + geometry) |
| Edge cant quote impact | **Keep** lângă cant decision sau debug |
| Grouped warnings (operator vs technical) | **Split** — operator în main, technical în debug |

---

## 5. Probleme UI principale

1. **`IntakeV4GeometryPanel` este hub-ul de zgomot** — titlu „Geometrie quote”, 4 contoare, 5+ perimetre paralele, secțiune cant, mesaje Soare/OCR, pending fără acțiune clară pe Layers.
2. **Duplicare Layers + Review** — același geometry panel de două ori.
3. **Prea multe perimetre operator-facing** — LED, CNC față, cant, artwork, Corel layer-sum — confundă cu „litere reale”.
4. **Rezumat lucrare + GeometryPanel overlap** — artwork/goluri apar de 2–3 ori.
5. **Material breakdown prea comercial/tehnic** pentru Review — pare quote final, nu draft intern.
6. **Face/Back Prep panel full-table în debug** — util pentru dev, prea greu pentru verificare rapidă; lipsește **compact summary în main**.
7. **AI mock + V3 dry-run labels** — subminează încrederea („catalog V3”, „mock”).
8. **„pending” fără CTA** — cant/volum pending pe Layers fără buton clar (salvează Review).
9. **Mesaje lungi developer-facing** — Soare emblem note, diagnostic artwork perimeter, source badges (`shared_edge_cant_rules`).

---

## 6. Ce trebuie să vadă operatorul (UI principal)

Maxim **5–6 informații** + acțiuni clare:

| # | Informație | Sursă canonică (neschimbată) |
|---|------------|------------------------------|
| 1 | Nume fișier + status analiză/confirmare | header + layer confirmation |
| 2 | Lățime / Înălțime (mm) | `analyzerReport.document.widthMm/heightMm` |
| 3 | **Perimetru total vectorial** | `buildIntakeV4GeometryMetricDisplay.corelComparableCurveLengthM` (layer-sum fețe volumetrice) — **UI label only** |
| 4 | Template / proces | `product_binding.template_code` (+ badge draft/read-only) |
| 5 | Blocaj principal (dacă există) | `firstBlocker` / readiness |
| 6 | Cost intern CNC față/spate — **total compact** (optional context) | Face/Back Prep endpoint totals |

Plus **decizii operator** (nu debug): layer roles (Step 1), finisaje, backing, cant, confirmare.

---

## 7. Ce mutăm în technical/debug

| Element | Motiv |
|---------|--------|
| Grupuri volumetrice, piese producție, caractere n/a | Confundă cu text real |
| Perimetru LED, CNC față, cant, artwork logo | Perimetre de rol — nu summary |
| Suprafețe față/emblemă, layer principal | Quote geometry detail |
| Goluri / contururi tăiere (detaliu) | Deja parțial în summary — mută duplicate |
| V3 dry-run, task preview, handoff, pricing preview | Developer / pre-quote |
| Face/Back Prep: operații, pass_count, task order, warnings list | Verificare tehnică |
| Material breakdown tables, nesting canvas, CNC rows | Estimare internă detaliată |
| AI semantic assist | Non-binding mock |
| ProductSystem operation count card | Registry metadata |
| Source badges, JSON-ish labels | Developer |

---

## 8. Ce eliminăm / înlocuim din zona principală

| Element | Acțiune | Înlocuire |
|---------|---------|-----------|
| Titlu „GEOMETRIE QUOTE” | **Replace** | „Dimensiuni și perimetru” |
| „Corel curve length / layer-sum” | **Replace** (main) | „Perimetru total vectorial” |
| „Caractere text: n/a” | **Remove** | Ascuns complet |
| „Soare = piesă volumetrică…” | **Move → debug** | — |
| „Metrici etichetate după sursă…” paragraph | **Remove** din main | — |
| „pending” cant fără acțiune | **Replace** | „Salvează finisaje pentru calcul cant” + buton |
| Duplicate GeometryPanel on Layers | **Remove** | Un singur loc (summary sau debug) |
| „catalog V3” în titluri | **Replace** | „Preview taskuri (intern)” în debug |
| Layout parts + goluri + artwork (3+ surfaces) | **Reduce** | Max 1 rând sau debug |
| Face/Back full tables în main | **Remove** | Compact totals card |

---

## 9. Regula pentru dimensiuni + perimetru total

### Adevăr de calcul (neschimbat)

- CNC cost draft: `cnc_cutting_perimeter_ml`, `backing_cnc_cutting_perimeter_ml` (vector, fără bbox fallback).
- Cant/LED/quote: câmpuri separate în `quote_geometry` / analyzer.

### Adevăr de afișare operator (UI nou)

**Card principal — doar 3 metrici geometrice:**

```txt
Lățime          → document.widthMm
Înălțime        → document.heightMm
Perimetru total vectorial → corelComparableCurveLengthM (sumă perimetru straturi face confirmate)
```

**Nu afișa în cardul principal:**

- LED perimeter (`led_perimeter_ml`)
- CNC face perimeter (`cutting_perimeter_ml` / `cnc_cutting_perimeter_ml`)
- Cant/return perimeter
- Artwork logo perimeter
- Bbox / nesting footprint
- OCR / character count

**Debug panel** poate păstra tabelul complet de perimetre cu labels tehnice pentru support/dev.

**Notă:** Perimetrul total vectorial (layer-sum face) ≠ perimetru CNC cu goluri; operatorul vede **un număr**; detaliile de rol rămân în debug pentru reconciliere.

---

## 10. Regula pentru panoul Face/Back Prep cost draft

**Stare actuală (HEAD `d8b5a34`):** panou complet în **Technical accordion** — materiale, operații, pass_count, formulas, warnings, task order.

**Recomandare:**

| Zone | Conținut |
|------|----------|
| **UI principal Review** | Card compact „Cost intern CNC față/spate — draft”: Total materiale, Total CNC, Total intern, toggle Șanfren Forex, status read-only (manual_required / OK), 1 warning operator dacă `vector_perimeter_missing` |
| **Technical accordion** | Detaliu: tables materiale/operații, pass_count per row, perimeter_source, formulas, task draft order, toate warnings, boundary line |

**Nu** muta panoul înapoi ca tabel full în main. **Da** extrage un **`IntakeV4FaceBackPrepCostDraftSummaryCard`** (component nou — faza 2) care refolosește același endpoint.

Template context: afișează `TPL-VOLUMETRIC-FACE-BACK-PREP` ca mod draft intern; workspace-ul rămâne legat de `TPL-VOLUMETRIC-LETTERS` — clarifică în summary, nu în 3 locuri.

---

## 11. Warnings classification

| Code / tip | Class | Unde apare |
|------------|-------|------------|
| `vector_perimeter_missing_or_low_confidence` | **operator_action_required** | Main (banner) + Face/Back compact |
| `missing_prices` / preț registry lipsă | **operator_action_required** | Main badge |
| `sheet_nesting_quantity_floor_applied` | **quote_only_warning** | Material review / debug |
| `analysis_bundle_pending` / cant pending | **operator_action_required** (cu CTA save) | Main — scurt |
| `v1_cnc_only_scope`, `task_order_logical_not_physical` | **technical_debug** | Debug only |
| `back_area_face_fallback` (material only) | **technical_debug** | Debug |
| `no_stock_consumption` / boundary notes | **developer_debug** | Footer mic, nu warning box |
| Artwork logo diagnostic / Soare note | **developer_debug** | Debug |
| Grouped `technical` warnings din material breakdown | **technical_debug** | Accordion |
| Grouped `operator` warnings | **operator_action_required** | Main |

---

## 12. Terminologie recomandată

| Actual | Recomandat | Unde |
|--------|------------|------|
| Geometrie quote | Dimensiuni și perimetru | Main card |
| Corel curve length / layer-sum | Perimetru total vectorial | Main |
| Piese producție | Piese vectoriale de producție detectate | Debug only (deja parțial) |
| Caractere text n/a | *(ascuns)* | — |
| Grupuri volumetrice | Straturi față (debug) | Debug |
| Cant / volum pending | Cant — necesită salvare finisaje | Main CTA |
| Estimare internă materiale — informativ | Materiale — estimare draft | Main compact |
| Cost intern CNC față/spate — draft | CNC față/spate — draft intern | Main compact |
| Detalii tehnice / debug | Detalii tehnice | Accordion (OK) |
| Task preview producție (catalog V3) | Preview taskuri interne | Debug |
| Piese plasate în layout | *(debug)* Layout nesting — piese | Debug |

---

## 13. Layout propus (3 zone)

```txt
┌─────────────────────────────────────────────────────────┐
│ ZONE 1 — OPERATOR SUMMARY (always visible, max ~6 lines) │
│  Fișier · L×H · Perimetru total vectorial · Template     │
│  Status · Blocaj principal (if any)                        │
│  [optional] CNC draft totals compact                       │
└─────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────┐
│ ZONE 2 — REVIEW ACTIONS                                  │
│  Layer roles (Step 1) / Finisaje / Backing / Cant        │
│  Confirm finisaje · Toggle shanfren Forex (compact)      │
│  Material review banner (only if manual sheet review)    │
└─────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────┐
│ ZONE 3 — TECHNICAL DETAILS (accordion, default closed)   │
│  Geometry advanced · Material tables · Nesting           │
│  Face/Back Prep detail · CNC ops · Pass-count · Tasks     │
│  V3 dry-runs · Pricing/handoff · AI mock · Registry      │
└─────────────────────────────────────────────────────────┘
```

**Steps mapping:**

- **Layers:** Zone 1 (file/dims) + layer table + preview; **fără** GeometryPanel full.
- **Review:** Zone 1 + 2 + 3.
- **Confirm:** Zone 1 recap + handoff checklist; **fără** re-expunere geometry full.

---

## 14. Plan de implementare în faze

### Faza 1 — Geometry summary cleanup

- Creează `IntakeV4OperatorGeometrySummaryCard` (L, H, perimetru total vectorial, status).
- Elimină `IntakeV4GeometryPanel` din Layers + Review main.
- Mută `IntakeV4GeometryPanel` integral în Technical accordion (sau redenumește „Geometrie avansată”).
- Tests: main view nu conține `intake-v4-geometry-led-perimeter`, `geometry-cutting-perimeter`.

### Faza 2 — Face/Back Prep compact card

- Extrage `IntakeV4FaceBackPrepCostDraftSummaryCard` (totals + toggle + 1 warning).
- Păstrează `IntakeV4FaceBackPrepCostDraftPanel` detaliat doar în accordion.
- Mount summary în Zone 1 Review (sub template/status).

### Faza 3 — Warnings cleanup

- Clasifică warnings în `intakeV4OperatorUiDisplay` (operator vs technical).
- Main: max 3 actionable warnings; rest în accordion.
- Înlocuiește „pending” cu CTA scurt.

### Faza 4 — Terminology cleanup

- Rename labels conform secțiunea 12.
- Elimină paragrafe developer din main (`GeometryPanel` intro, Soare note, OCR note din main).

### Faza 5 — Teste UI

- Vitest: Review main DOM nu conține zgomot tehnic (grep testids).
- Extend `IntakeV4OperatorUiPolish.test.tsx`.
- Manual smoke: Ana Maria + PBL — operator vede ≤6 facts în summary.

**Estimare efort:** 5 PR-uri mici, fiecare cu tests targeted; **fără** backend changes.

---

## 15. Riscuri

| Risk | Mitigation |
|------|------------|
| Operator pierde visibility pe perimetru CNC pentru debugging live | Păstrează full geometry în accordion; link „Vezi detalii tehnice” |
| Perimetru total (layer-sum) ≠ CNC cut perimeter — confuzie support | Tooltip: „Total contur fețe; CNC și cant folosesc reguli separate — vezi detalii” |
| Material breakdown mutat prea adânc — pierdere sheet review | Păstrează sheet review **promoted** când `requires_manual_review` |
| Face/Back compact fără pass_count — dev regression | Detaliu rămâne în accordion + tests |
| Scope creep spre CostEngine/quote | Boundary strict per fază |

---

## 16. Ce nu se schimbă (confirmat)

- Backend services, calcule geometrie, nesting, material policy
- Perimetru vectorial ca sursă CNC (pass-count, endpoint Face/Back Prep)
- ProductSystem registry, CostEngine, quote/order/tasks
- ExecutionPlan, `tasks_json`, stock consumption
- SVG analyzer algorithms

---

## 17. Recomandare finală

**Prioritate 1:** Faza 1 (Geometry summary) — cel mai mare câștig UX / reducere zgomot.  
**Prioritate 2:** Faza 2 (Face/Back compact) — aliniază panoul nou cu principiul „verificare mică în main, detaliu în debug”.  
**Prioritate 3:** Faze 3–4 (warnings + terminology) — consolidare încredere operator.  

Nu faceți un redesign big-bang al ReviewStep: **mutați și comprimați** folosind accordion-ul existent și un summary card nou. Păstrați toate datele pentru dev/support — doar **scoateți-le din calea operatorului zilnic**.

ProductSystem integration completă (dossier, CostEngine, module composition) rămâne **build separat** — acest audit acoperă doar **operator UI simplification**.

---

## Audit checklist

| Item | Status |
|------|--------|
| Pre-flight HEAD `d8b5a34`, tracked clean | PASS |
| Inventar Review + Layers + Confirm | PASS |
| Regula perimetru total | Documented |
| Face/Back Prep split main/debug | Documented |
| Warnings taxonomy | Documented |
| Faze implementare | 5 faze |
| No code changes | PASS |
