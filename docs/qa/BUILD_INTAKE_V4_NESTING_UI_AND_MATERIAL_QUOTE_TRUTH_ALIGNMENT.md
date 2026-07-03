# BUILD — Intake V4 Nesting UI and Material Quote Truth Alignment

**Date:** 2026-06-23  
**Branch:** `local/integration-pr4-plus-svg-path`  
**HEAD before:** `c516690`  
**Scope:** Operator UI clarity for nesting preview vs material quote review. No pricing/CostEngine/stock changes.

## 1. Problema inițială

Operatorul vedea în Material Breakdown contoare tehnice (`Sheet layouts`, `Active layouts`, `Used sheet area 6.000 m²`, `Σ placement bbox`) fără să înțeleagă:

- de ce placa 3000×2000 este activă vs 3000×1500 / 4000×1500 alternative;
- de ce Material Breakdown nu folosește 6 m² (placă întreagă);
- de ce placement bbox (1.1469 m²) diferă de selected (1.2638 m²) și de măsurătoarea Corel (ex. 2.7627 m²);
- când și de ce este cerută verificare manuală.

## 2. Ce confuza UI

| Text vechi | Problema |
|------------|----------|
| `Used sheet area 6.000 m²` | Părea consum ofertat |
| `ACTIVE for breakdown` | Engleză, fără context |
| `alternative variant` | Nu explica exclusiunea din breakdown |
| Candidați în accordion debug | Ascunși, par formule tehnice |
| `Manual review required: da` | Fără semafor și fără acțiune clară |

## 3. Definiții finale (sursă: cod backend)

### Active layout

Layout-ul de placă/rolă pentru care `config_id == active_config_id` **și** are placements (`placedItemsCount > 0`). Rezolvat în `resolve_active_sheet_layout()` → de obicei prima variantă cu piese plasate (ex. `sheet_3000x2000`).

### Alternative layout

Orice alt `configId` din `svg_analysis_json.nesting.sheets` fără flag activ. Nu se însumează în Material Breakdown (`layout_kind: alternative_variant`).

### Used sheet area (`used_sheet_area_sqm`)

Aria fizică a plăcii simulate (ex. 3000×2000 mm → 6.0 m²). **Preview diagnostic — nu consum ofertat.**

### Placement bbox (`placement_footprint_face_sqm`)

Suma dreptunghiurilor plasate pe layout-ul activ pentru piese face. Diagnostic nesting bbox, nu toolpath.

### Layout occupied (`layout_occupied_area_sqm` / `nesting_shelf_occupied_sqm`)

Aria ocupată de algoritmul shelf pe layout (usedWidth × consumedLength). Poate fi mult mai mare decât suma bbox-urilor — nu folosi direct ca preț.

### Face union bbox (`face_union_bbox_sqm`)

Bounding box union al grupurilor face din analiză.

### Selected quote area (`selected_quote_sheet_area_sqm`)

Cantitatea folosită **azi** în Material Breakdown pentru placă: politică `eligible_area_floor` (max eligibil vs placement floor). `is_applied_to_quote = false` (preview intern).

### Recommended auto candidate

`max(eligible, childPartBBoxSum × 5% buffer)` — preview policy, nu trimis în CostEngine.

### Operator override

Footprint manual Corel (cm×cm) salvat în `payload.sheet_quote_override`. Preview intern; nu schimbă selected decât dacă `use_for_quote_estimate=true` (în afara scope-ului acestui build).

## 4. Ana Maria (persisted `2aeda68b-09e0-46af-ba1e-31b0a47482d7`)

| Metric | Valoare |
|--------|---------|
| Fișier | `fara_layere_powerclip.svg` |
| Stale | da — 6× `split_layer_1_*` orphan defs |
| orphan_defs_split_placement_sqm | 2.3211 |
| eligible_face_area_sqm | 1.2638 |
| placement_footprint_face_sqm | 1.1469 |
| child_part_bbox_sum_sqm | 1.1469 |
| layout_occupied_area_sqm | 5.36 |
| selected | 1.2638 (`eligible_area_floor`) |
| requires_manual_review | true |
| is_applied_to_quote | false |

**Operator:** nesting-ul arată placă 6 m² dar breakdown folosește floor eligibil 1.2638 m². Shelf 5.36 m² și orphan defs 2.32 m² indică snapshot învechit — măsoară în Corel (ex. 192.67×143.389 cm = 2.7627 m²) și salvează footprint manual pentru review.

## 5. PBL control (`a6cb9f56-2d16-4a53-b569-d5fd51cabfe2`)

| Metric | Valoare |
|--------|---------|
| Fișier | `pbl-layere.svg` |
| Corel layers | 3 (2 face + 1 artwork) |
| orphan_defs | null/0 |
| eligible | 0.6907 |
| selected | 0.6907 (unchanged) |
| requires_manual_review | true (spread + shelf/bbox) |

PBL este mai coerent: straturi Corel reale, fără pseudo-layer/orphan defs. Tot cere review când shelf >> bbox.

## 6. Ce s-a schimbat în UI

- `IntakeV4NestingPreviewPanel`: secțiuni 1–3 (rezumat, layout activ, alternative în accordion), wording RO.
- `IntakeV4SheetQuoteReviewPanel`: semafor status, candidați vizibili, decizie operator când `requires_manual_review`.
- `IntakeV4SheetFootprintOverridePanel`: texte „Măsurat în Corel / layout manual”.
- `IntakeV4MaterialBreakdownPanel`: candidați mutați din debug accordion în panel dedicat.
- Backend disclaimer + `breakdown_note` în română (`intake_v4_nesting_preview_service.py`).

## 7. Ce NU s-a schimbat

- CostEngine, Pricing Registry, Color Registry
- Quote/order/tasks, ExecutionPlan, tasks_json
- Stock consumption
- `selected_quote_sheet_area` policy (`eligible_area_floor`)
- `is_applied_to_quote = false`

## 8. Tests

```powershell
# Backend — 57 passed
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v4_sheet_quote_candidate_policy.py tests/test_intake_v4_sheet_footprint_override.py tests/test_intake_v4_nesting_material_precision.py tests/test_intake_v4_material_breakdown.py -q

# Frontend — 18 passed (incl. new intakeV4SheetQuoteReviewDisplay.test.ts)
cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/components/workos/intake-v4/IntakeV4MaterialBreakdownPanel.test.tsx src/lib/intakeV4/intakeV4SheetQuoteReviewDisplay.test.ts src/lib/svgAnalyzer/analyzer/svgAnalyzerRegressionGate.test.ts src/lib/svgAnalyzer/analyzer/sheetQuoteCandidateFreshAudit.test.ts
```

## 9. Remaining

- Owner UI review în browser
- Re-analyze Ana Maria workspace (explicit approval)
- Post-push backup după aprobare
- Integrare quote finală / CostEngine — build separat
- Politică full-sheet stock — build separat
