# Intake V4 Operator UI — Hard Audit (Counts & Trust)

**Date:** 2026-06-24  
**Branch:** `local/integration-pr4-plus-svg-path`  
**HEAD:** `d3dde95` (local = remote)  
**Mode:** read-only — no code changes, no re-analysis, no DB/workspace mutations  

---

## 1. Scop

Verificare factuală a tuturor contoarelor și etichetelor numerice din UI-ul operator Intake V4 pentru două workspace-uri reale (Ana Maria, PBL): ce afișează ecranul, de unde vine fiecare număr, ce entitate numără, dacă este business-facing sau debug, și dacă valorile reflectă starea persisted + compute curent.

---

## 2. Metodă

| Pas | Acțiune |
|-----|---------|
| Pre-flight | `git branch`, `rev-parse`, `ls-remote`, `status`, `log` |
| Browser | Pagini deschise personal la URL-urile operator; parcurgere Steps 1–3 (Layers, Review, Confirm); note + screenshot |
| API | `GET /api/v1/intake-v4/workspaces/{id}` + `GET .../material-breakdown` (read-only, backend :8000) |
| Cod | Trace UI → helper → API field → backend service |
| Teste | Comparare cu fixture-uri `backend/tests/fixtures/intake_v4/` și teste pytest/Vitest relevante |

**Nu s-a rulat:** re-analysis, PUT analysis-bundle, quote/order/tasks, modificări DB.

---

## 3. Workspace-uri auditate

| Label | ID | SVG | Code |
|-------|-----|-----|------|
| Ana Maria | `2aeda68b-09e0-46af-ba1e-31b0a47482d7` | `fara_layere_powerclip.svg` | IV4-8D89E354 |
| PBL | `a6cb9f56-2d16-4a53-b569-d5fd51cabfe2` | `pbl-layere.svg` | IV4-46499080 |

**URLs verificate:**
- `http://localhost:3000/intake-v4/2aeda68b-09e0-46af-ba1e-31b0a47482d7/operator`
- `http://localhost:3000/intake-v4/a6cb9f56-2d16-4a53-b569-d5fd51cabfe2/operator`

---

## 4. Artefacte (payload / screenshot)

| Artefact | Path |
|----------|------|
| API bundle Ana Maria (final) | `tmp/operator-ui-hard-audit-ana-maria-20260624-132632.json` |
| API bundle PBL (final) | `tmp/operator-ui-hard-audit-pbl-20260624-132632.json` |
| API bundle Ana Maria | `tmp/operator-ui-hard-audit-ana-maria-20260624-132245.json` |
| API bundle PBL | `tmp/operator-ui-hard-audit-pbl-20260624-132245.json` |
| API bundle Ana Maria (captură anterioară) | `tmp/operator-ui-hard-audit-ana_maria-20260624-102113.json` |
| API bundle PBL (captură anterioară) | `tmp/operator-ui-hard-audit-pbl-20260624-102113.json` |
| Screenshot PBL Layers | `test-results/audit-pbl-layers-20260624.png` |

---

## 5. Tabel complet counters — Ana Maria

Stare UI verificată în browser + confirmată din API `20260624-132632`.  
**Zonă:** M = zonă principală (Layers/Review/Confirm), T = detalii tehnice / collapsible debug.

| Label UI (exact) | Valoare UI | Zonă | Step | API field | Sursă compute |
|------------------|------------|------|------|-----------|---------------|
| IV4-8D89E354 | IV4-8D89E354 | M | header | `workspace_code` | persisted workspace |
| Operator workspace V4 | (titlu) | M | header | `title` | persisted |
| fara_layere_powerclip.svg · 29 KB | 29 KB | M | header | `source_file` / size | persisted |
| 6/6 layers confirmed | 6/6 | M | stepper | `layer_role_setup.confirmation_status` | persisted |
| Lățime | 5000.1 mm | M | Layers | `analyzerReport.document.widthMm` | client nest2 + persisted bundle |
| Înălțime | 600.1 mm | M | Layers | `document.heightMm` | idem |
| Straturi | **6** | M | Layers | `report.layers.length` | analyzer report (6 layer roles confirmate) |
| Confirmare | complete | M | Layers | `confirmation_status` | persisted |
| Grupuri volumetrice | **4** | M | Layers/Review | (derived) face-role layers in report | `buildIntakeV4GeometryMetricDisplay` — count `role=face` |
| Piese producție | **19** | M | Layers/Review | `quote_geometry.real_letters_count` | persisted path_geometry → `intake_v4_letter_part_classification_service` |
| Caractere text | n/a | M | Layers | (static) | hardcoded — curbe, nu text |
| Artwork / logo | **2** | M | Layers | (derived) artwork roles in report | `buildIntakeV4GeometryMetricDisplay` |
| Corel curve length / layer-sum | 26.747 m | M | Layers | sum layer perimeters face | client-side from analyzer report |
| Perimetru LED litere — exterior only | 20.880 m | M | Layers | `quote_geometry.led_perimeter_ml` | persisted geometry |
| Perimetru CNC față — exterior + goluri | 24.073 m | M | Layers | `quote_geometry.cutting_perimeter_ml` | persisted |
| Cant / volum litere — exterior + goluri eligibile | pending | M | Layers | `return_material_perimeter_ml` | Layers step: `analysisBundleReady=false` → pending |
| Artwork logo perimeter | 4.891 m | M | Layers | diagnostic sum | analyzer + geometry |
| Suprafață față | 1.264 m² | M | Layers | `quote_geometry.face_area_m2` | persisted |
| Suprafață emblemă | 0.850 m² | M | Layers | `quote_geometry.artwork_area_m2` | persisted |
| Layer principal | pseudo:maria | M | Layers | `primary_letters_layer_key` | persisted |
| Contururi interioare / goluri | **7** | M | Layers | `quote_geometry.inner_holes_count` | classification service |
| Contururi tăiere total | **26** | M | Layers | `quote_geometry.cutting_contours_count` | classification service |
| Layere | **6** | M | Confirm | `layerCount` | `IntakeV4ConfirmOperationalSummary` ← report.layers.length |
| Child parts | **21** | M | Confirm | derived | `nestable_parts + artwork_parts` = 19+2 |
| Litere reale | **19** | M | Confirm | `real_letters_count` | persisted quote_geometry |
| Artwork | **2** | M | Confirm | `nesting.summary.artwork_parts` | fresh material-breakdown nesting |
| Interioare | **7** | M | Confirm | `inner_holes_count` | persisted quote_geometry |
| Piese nestable | **19** | M | Confirm | `nesting.summary.nestable_parts` | fresh `intake_v4_nesting_preview_service` |
| Artwork parts (Nesting) | **2** | M | Confirm | `nesting.summary.artwork_parts` | fresh nesting |
| LED litere — module | **84** | M | Confirm | finish + geometry | `syncIntakeV4FinishLighting` |
| LED emblemă — module | **51** | M | Confirm | emblem outbox area | shared LED rule 60 mod/m² |
| LED total — module | **135** | M | Confirm | sum | computed confirm summary |
| 13 operații · 6 componente | 13 / 6 | M | Confirm | ProductSystem dossier | template metadata |
| Arie brută față / gross | 1.2638 m² | M | Confirm | `face_area_m2` | persisted |
| Arie plexiglas ofertabilă / nesting | 1.2638 m² | M | Confirm | material row plexiglas_face qty | fresh material-breakdown |
| Selected current (material review) | 1.2638 m² | M | Review | `selected_quote_sheet_area_sqm` | fresh policy floor |
| Piese plasate în layout | **21** | T | Review (nesting expanded) | active sheet `placement_count` | fresh nesting — includes artwork placements |
| Piese în layout activ | **19** | T | Review nesting summary | `summary.nestable_parts` | fresh nesting |
| Găuri excluse | **0** | T | nesting summary | `summary.holes_excluded` | fresh nesting |
| Artwork exclus | **2** | T | nesting summary | `summary.artwork_parts` | fresh nesting |
| Variante placă simulate | **4** | T | nesting summary | `summary.sheet_layouts` | fresh nesting |
| Layout-uri alternative | **11** | T | nesting summary | `summary.alternative_layouts` | fresh nesting |
| Layout-uri active (breakdown) | **5** | T | nesting summary | active_sheet + active_roll | fresh nesting |
| Face union bbox (shelf) | 2.5238 m² | M/T | material review | `face_union_bbox_sqm` | fresh sheet quote candidates |
| Placement bbox sum | 1.1469 m² | M/T | material review | `placement_footprint_face_sqm` | fresh |
| Child part bbox sum | 1.1469 m² | T | material review | `child_part_bbox_sum_sqm` | fresh |
| Placă fizică | 6.0000 m² | M/T | material review | `full_sheet_allocation_sqm` | fresh |
| Candidate tasks count (production dry-run summary) | **22** | T/API | Review technical payload | `production_task_dry_run.summary.candidate_tasks_count` | dry-run preview summary (nu counter principal Confirm/Geometry) |
| Material rows `el-22` suffix | 1.561 m² (×2 rows) | T | material breakdown | `material_key` artwork_complexity_raster_**el-22** | **NOT a counter** — SVG element id in key name |

**Valoarea 22:** apare în payloadul tehnic `production_task_dry_run.summary.candidate_tasks_count=22`, dar **nu** ca număr principal în cardurile Confirm/Geometry.  
**Valoarea 19:** apare ca **Piese producție**, **Litere reale**, **Piese nestable** — **nu** ca interioare.

---

## 6. Tabel complet counters — PBL

| Label UI (exact) | Valoare UI | Zonă | Step | API field | Sursă compute |
|------------------|------------|------|------|-----------|---------------|
| IV4-46499080 | IV4-46499080 | M | header | `workspace_code` | persisted |
| pbl-layere.svg | (file) | M | header | source file name | persisted |
| Straturi | **3** | M | Layers | `report.layers.length` | browser screenshot + API |
| Grupuri volumetrice | **2** | M | Layers | derived face layers | geometry metric display |
| Piese producție | **10** | M | Layers | `real_letters_count` | persisted |
| Artwork / logo | **1** | M | Layers | derived artwork layers | geometry metric display |
| Corel curve length | 13.621 m | M | Layers | layer-sum | client report |
| Perimetru LED | 11.630 m | M | Layers | `led_perimeter_ml` | persisted |
| Perimetru CNC față | 13.132 m | M | Layers | `cutting_perimeter_ml` | persisted |
| Contururi interioare / goluri | **2** | M | Layers (expected) | `inner_holes_count` | API=2, confirm step not fully rendered in a11y tree |
| Layere | **3** | M | Confirm (API) | layer count | 3 confirmed roles |
| Child parts | **11** | M | Confirm (API) | 10+1 | nestable + artwork |
| Litere reale | **10** | M | Confirm (API) | `real_letters_count` | persisted |
| Artwork | **1** | M | Confirm (API) | `artwork_parts` | nesting summary |
| Interioare | **2** | M | Confirm (API) | `inner_holes_count` | persisted |
| Piese nestable | **10** | M | Confirm (API) | `nestable_parts` | fresh nesting |
| Piese plasate în layout | **11** | T | nesting | `placement_count` | fresh — 10 letters + 1 artwork |
| Selected quote sheet area | 0.6907 m² | M | Review | `selected_quote_sheet_area_sqm` | fresh policy |
| Face union bbox | 1.1577 m² | M/T | material review | `face_union_bbox_sqm` | fresh |
| 13 operații · 6 componente | 13 / 6 | M | Confirm | ProductSystem | template metadata |
| Candidate tasks count (production dry-run summary) | **14** | T/API | Review technical payload | `production_task_dry_run.summary.candidate_tasks_count` | dry-run preview summary |

**Valoarea 22:** nu apare nici în UI principal, nici în payloadul PBL (`candidate_tasks_count=14`).  
**Valoarea 19:** **Nu apare** în UI PBL.

**Notă PBL Confirm step:** handoff blocat (artwork execution undecided, lighting config invalid). Checkbox confirm disabled — UI afișează blockers, nu toate rândurile numerice în accessibility snapshot; valorile Confirm provin din API + Layers step verificat vizual.

---

## 7. Trace UI → API → backend (counters importanți)

### 7.1 Straturi / Layere

```
UI "Straturi" (Layers)
  → IntakeV4SvgAnalyzerStep (report.layers.length)
  → client SvgAnalysisCoreReport from persisted analysis_bundle + local rehydrate
  → nest2 analyzer output in workspace.payload.analysis_bundle

UI "Layere" (Confirm)
  → IntakeV4ConfirmOperationalSummary
  → buildIntakeV4ConfirmSummary({ layerCount })
  → same report.layers.length
```

**Business-facing:** da (număr straturi SVG confirmate).  
**Trust:** persisted bundle; consistent între Layers și Confirm.

### 7.2 Piese producție / Litere reale

```
UI "Piese producție"
  → IntakeV4GeometryPanel / buildIntakeV4GeometryMetricDisplay
  → productionPartCount = real_letters_count ?? material_piece_count ?? letter_count
  → workspace.payload.quote_geometry (persisted)
  → intake_v4_quote_geometry_service + intake_v4_letter_part_classification_service
  → counts real_letter_items (face parts excluding orphan holes)

UI "Litere reale" (Confirm)
  → geometry.real_letters_count ?? letter_count
  → same persisted quote_geometry field
```

**Ana Maria:** 19 = piese volumetrice nestable clasificate ca litere reale.  
**PBL:** 10.  
**Business-facing:** da — dar label „Piese producție” ≠ „litere tipografice”; include piese curbă (ex. soare = emblemă).

### 7.3 Contururi interioare / goluri / Interioare

```
UI "Contururi interioare / goluri" (Layers)
  → geometry.inner_holes_count
  → intake_v4_letter_part_classification_service:
       embedded_inner_holes (innerContourCount on letter items)
     + orphan_inner_holes (orphan hole part ids)

UI "Interioare" (Confirm)
  → same inner_holes_count
```

**Ana Maria:** 7 (NU 19).  
**PBL:** 2.  
**Business-facing:** da pentru CNC/perimetru cant; necesită explicație (găuri interioare decupaj, nu „piese”).

### 7.4 Child parts (Confirm)

```
UI "Child parts"
  → resolveChildPartsCount()
  → nesting.summary.nestable_parts + nesting.summary.artwork_parts
  → GET material-breakdown (fresh compute) → nesting_preview
  → intake_v4_nesting_preview_service._build_part_rows
```

**Ana Maria:** 21 = 19 + 2.  
**PBL:** 11 = 10 + 1.  
**Business-facing:** parțial — eticheta EN „Child parts” pe UI RO; sumă nestable+artwork, **nu** inner holes.

### 7.5 Piese nestable vs Piese plasate

```
UI "Piese nestable" / "Piese în layout activ"
  → preview.summary.nestable_parts
  → count(parts where nestable=true)

UI "Piese plasate în layout" (active sheet)
  → sheet.placement_count
  → all placements on active sheet config (face letters + artwork parts)
```

**Ana Maria:** nestable **19**, placements **21** (difference = 2 artwork placements).  
**Trust:** ambele fresh din același material-breakdown call; diferența este by design.

### 7.6 Material quote areas

```
UI "Aria pieselor eligibile" / "Selected current"
  → IntakeV4SheetQuoteReviewPanel
  → material_breakdown.sheet_quote_material_candidates
  → intake_v4_internal_draft_quote_policy_service / sheet quote candidate builder
  → selected_quote_sheet_area_sqm = 1.2638 (Ana Maria), source eligible_area_floor
  → is_applied_to_quote = false (preview only)
```

**Business-facing:** da pentru review intern; **nu** preț CostEngine final până la quote apply.

### 7.7 Warnings / manual review

```
UI manual review bullets
  → formatActiveManualReviewReasons (shared helper)
  → manual_review_reason string from sheet_quote_material_candidates
  → intake_shared_material_review.filter_stale_orphan_manual_review_tokens
```

**Ana Maria post-reanalysis:** orphan_defs stale token **absent**; rămân: candidateSpread, pseudo_layer, layout/child bbox spread.  
**Trust:** reflects fresh compute; stale orphan warning suppressed when `orphan_defs_split_placement_sqm=null`.

---

## 8. Secțiune dedicată „22 / 19”

### Ana Maria

| # | Întrebare | Răspuns factual |
|---|-----------|-----------------|
| 1 | Există 22 în datele verificate? | **Da**, în payloadul tehnic de dry-run: `candidate_tasks_count=22` (Ana Maria). |
| 2 | Există 22 în cardurile principale Confirm/Geometry? | **Nu**. Nu este afișat ca „Litere reale/Interioare/Child parts”. |
| 3–5 | Dacă ar exista ca număr principal | N/A — în UI principal nu există counter business cu valoarea 22. |
| 6 | Ce entități ar putea fi confundate cu „22”? | **21** Child parts / placement_count; **23** volumetric_piece_count (API only, nu UI principal); **26** cutting_contours; substring **el-22** în material keys (logo dreapta complexity rows) — **nu este contor**. Pre-reanalysis istoric: **27** placements (documentat în BUILD reanalysis, nu în UI curent). |
| 7 | Există 19 în UI? | **Da.** |
| 8 | Unde? | **Piese producție** (Layers/Review); **Litere reale** (Confirm); **Piese nestable** (Confirm + nesting summary). |
| 9 | Label exact | „Piese producție”, „Litere reale”, „Piese nestable” — **nu** „19 litere” ca text literal. |
| 10 | Field API | `real_letters_count`, `nestable_parts`, `letter_count` (all 19). |
| 11 | Unde se calculează | `intake_v4_letter_part_classification_service` (letters); `intake_v4_nesting_preview_service` (nestable). |
| 12 | Ce numără | 19 piese face volumetrice clasificate ca litere/piese producție nestable. |
| 7–12 pentru „19 interioare” | **Nu.** Label **Interioare** = **7**, field `inner_holes_count`. |

### PBL

| Valoare | Apare? |
|---------|--------|
| 22 (UI principal) | **Nu** |
| 22 (payload tehnic dry-run) | **Nu (PBL are 14)** |
| 19 | **Nu** |
| 10 | Da — Piese producție / Litere reale / Piese nestable |
| 2 | Da — Interioare / Contururi interioare |

---

## 9. Inventar labeluri (selectiv)

| Text afișat | Componentă | Field / sursă | RO/EN | Zonă |
|-------------|------------|---------------|-------|------|
| Straturi | IntakeV4SvgAnalyzerStep | `report.layers.length` | RO | M |
| Layere | IntakeV4ConfirmOperationalSummary | `layerCount` | RO label / EN „Layere” | M |
| Grupuri volumetrice | IntakeV4GeometryPanel | derived face count | RO | M |
| Piese producție | IntakeV4GeometryPanel | `real_letters_count` | RO | M |
| Caractere text | IntakeV4GeometryPanel | n/a static | RO | M |
| Artwork / logo | IntakeV4GeometryPanel | artwork layer count | RO | M |
| Contururi interioare / goluri | IntakeV4GeometryPanel | `inner_holes_count` | RO | M |
| Contururi tăiere total | IntakeV4GeometryPanel | `cutting_contours_count` | RO | M |
| Child parts | IntakeV4ConfirmOperationalSummary | nestable+artwork | **EN label** | M |
| Litere reale | IntakeV4ConfirmOperationalSummary | `real_letters_count` | RO | M |
| Interioare | IntakeV4ConfirmOperationalSummary | `inner_holes_count` | RO | M |
| Piese nestable | IntakeV4ConfirmOperationalSummary | `nestable_parts` | RO | M |
| Artwork parts | IntakeV4ConfirmOperationalSummary | `artwork_parts` | EN | M |
| A. Preview nesting — diagnostic | IntakeV4NestingPreviewPanel | collapsible | RO | T |
| Piese în layout activ | IntakeV4NestingPreviewPanel | `nestable_parts` | RO | T |
| Piese plasate în layout | IntakeV4NestingPreviewPanel | `placement_count` | RO | T |
| Material quote review — estimare internă | IntakeV4SheetQuoteReviewPanel | sheet_quote_material_candidates | RO | M |
| Footprint manual Corel | IntakeV4SheetFootprintOverridePanel | operator override | RO | M |
| Detalii tehnice / debug | IntakeV4ReviewStep | collapsible panels | RO | T |
| Nu este preț final ofertă… CostEngine | IntakeV4MaterialBreakdownPanel | disclaimer | RO | M |

---

## 10. Consistență UI / API / test fixtures

### Ana Maria

| Metric | UI (browser) | API live | Fixture / test |
|--------|--------------|----------|----------------|
| real_letters / Piese producție | 19 | 19 | `ana_maria_post_reanalysis_metrics` — nu conține letters; fresh analysis fixture folosit pentru reanalysis dry-run |
| inner_holes / Interioare | 7 | 7 | — |
| nestable_parts | 19 | 19 | — |
| placement_count | 21 | 21 | post_reanalysis: `placements_count: 21` |
| selected_quote_sheet_area | 1.2638 | 1.2638 | post_reanalysis fixture: 1.2638 ✓ |
| layout_occupied / face union | 2.5238 | 2.5238 | post_reanalysis + reanalysis preview test ✓ |
| orphan_defs_split | absent UI | null | post_reanalysis ✓ |
| split_layer_count | 0 (API) | 0 | reanalysis regression ✓ |

**Stale vs fresh:**
- Geometry counts (letters, holes, perimeters): **persisted** în `workspace.payload.quote_geometry` / analysis bundle.
- Nesting summary, material breakdown, sheet quote candidates: **fresh computed** la fiecare `GET material-breakdown`.
- Confirm step combină ambele — de aceea Child parts (21) poate diferi semantic de Litere reale (19).

### PBL

| Metric | UI Layers | API live | Fixture golden | Fixture degraded |
|--------|-----------|----------|----------------|------------------|
| real_letters | 10 | 10 | (derived from golden) | — |
| inner_holes | 2 (API) | 2 | — | — |
| nestable_parts | 10 | 10 | nestableCount **11** in golden JSON | nestableCount **1** |
| placement_count | 11 | 11 | — | — |

**Diferențe explicite:**
- `pbl_layere_golden_analysis.json` are `nestableCount: 11` — **nu** match UI live 10 (fixture ≠ workspace DB state).
- `test_intake_v4_pbl_pricing_completeness.py` folosește `inner_holes_count: 5` ca **mock** — **nu** reflectă workspace live (2).
- Testele reanalysis PBL compară golden vs degraded ca **dry-run preview**, nu UI live.

**Regulă aplicată:** diferențele nu sunt marcate „greșit” fără sursă — golden/degraded sunt scenarii alternate, nu snapshot-uri ale workspace-ului `a6cb9f56…` audiat.

---

## 11. Concluzii factuale (trust)

1. **UI afișează numere consistente cu API** pentru workspace-urile audiate la momentul verificării (backend live :8000, frontend :3000).
2. **Aceeași cifră (ex. 19) apare sub labeluri diferite** (Piese producție, Litere reale, Piese nestable) — același sau familie strânsă de fields; operatorul trebuie să citească labelul.
3. **Contoare diferite pentru entități diferite:** 19 litere ≠ 7 interioare ≠ 21 child parts ≠ 21 placements ≠ 26 contururi tăiere.
4. **Valoarea 22 există doar în payload tehnic dry-run** (`candidate_tasks_count=22` Ana Maria), nu ca counter business în cardurile principale UI; confuzie posibilă cu: placement 21, volumetric 23, contururi 26, sau **el-22** în denumiri material rows.
5. **Valoarea 19 nu este „19 interioare”** — interioare = **7** (Ana Maria), label explicit „Interioare” / „Contururi interioare / goluri”.
6. **Material quote area (1.2638 m²)** este preview policy floor, `isAppliedToQuote=false` — trustworthy pentru review intern, **nu** pentru preț comercial final CostEngine.
7. **Nesting shelf / face union (2.5238 m²)** este marcat diagnostic — UI avertizează să nu fie folosit ca preț.
8. **Cant / volum pe Layers step** rămâne „pending” până la context Review cu bundle complet — comportament cod, nu stale data.
9. **PBL** are blockers reale (artwork undecided, lighting) — unele sumare Confirm sunt incomplete în UI din cauza handoff blocat.

**Verdict trust parțial:** contoarele de clasificare geometrie (litere, interioare, straturi) sunt **utilizabile** dacă operatorul înțelege labelurile; contoarele nesting/material (**placements, shelf bbox, selected area**) sunt **preview/diagnostic** și sunt etichetate ca atare în cod; **nu** un singur număr universal „de încredere pentru preț”.

---

## 12. Întrebări deschise

1. Owner a văzut „22 litere” / „19 interioare” într-o **sesiune anterioară pre-reanalysis** sau pe **alt ecran** (V3, QuoteWizard, raport export)?
2. Trebuie aliniat label **Child parts** (EN) la terminologie RO și/sau tooltip care explică formula nestable+artwork?
3. `volumetric_piece_count` (23 Ana Maria) și `artwork_piece_count` (4) există în payload dar **nu** au card dedicat în UI principal — intenționat?
4. Fixture `ana_maria_fresh_analysis.json` conține metadata `sourceFileName: pbl-layere.svg` în grep — nume fișier inconsistent în fixture; afectează trust teste offline vs Ana Maria live?
5. PBL golden fixture `nestableCount: 11` vs live 10 — care este sursa canonicală pentru regression PBL UI?

---

## Confirmări task

- [x] Read-only — singur fișier creat: acest document  
- [x] Fără re-analysis  
- [x] Fără commit / push  
- [x] Branch `local/integration-pr4-plus-svg-path` @ `d3dde95`  
- [x] Tracked tree clean (untracked: tmp, test-results, alte docs)
