# VERIFY — TPL-VOLUMETRIC-FACE-BACK-PREP V1 Numeric Real Workspaces

**Date:** 2026-06-24  
**Branch:** `local/integration-pr4-plus-svg-path`  
**Base commit:** `27ed123` (+ bugfix `pricing_registry` normalization during verify)  
**Build:** `VERIFY_TPL_VOLUMETRIC_FACE_BACK_PREP_V1_NUMERIC_REAL_WORKSPACES`

## Scop

Verificare numerică a endpointului read-only V1 CNC-only pe workspace-uri reale din `backend/dev.db`, fără UI, finisaje, CostEngine, quote/order/tasks reale sau stock.

## Endpoint

```http
GET /api/v1/intake-v4/workspaces/{workspace_id}/volumetric-face-back-prep/cost-draft?shanfren_forex=
```

**Metodă verificare:** apel direct al `get_tpl_volumetric_face_back_prep_cost_draft_for_workspace()` pe aceeași DB ca dev local (echivalent logic cu endpoint-ul HTTP). Artefact JSON: `tmp/_verify_face_back_prep_v1_numeric.json`.

## Bug găsit în verify

| Issue | Impact | Fix |
|-------|--------|-----|
| `resolve_v4_registry_material_price` returnează `pricing_registry`, schema acceptă doar `prices_registry` | **500 / ValidationError** pe workspace real cu prețuri registry | `_normalize_material_price_source()` în `tpl_volumetric_face_back_prep_cost_draft_service.py` |

---

## Tabel comparativ

| Workspace | shanfren_forex | plexiglas m² | forex m² | face cut ml | face shanfren ml | back cut ml | back shanfren ml | material EUR | operation EUR | total EUR |
|-----------|----------------|--------------|----------|-------------|------------------|-------------|------------------|--------------|---------------|-----------|
| Ana Maria (IV4-8D89E354) | false | 1.2638 | 1.2638* | 25.0188 | 25.0188 | 25.0188* | — | 40.4416 | 112.5846 | **153.0262** |
| Ana Maria | true | 1.2638 | 1.2638* | 25.0188 | 25.0188 | 25.0188* | 25.0188 | 40.4416 | 150.1128 | **190.5544** |
| PBL (IV4-46499080) | false | 0.6907 | 0.6907* | 13.1322 | 13.1322 | 13.1322* | — | 22.1024 | 59.0949 | **81.1973** |
| PBL | true | 0.6907 | 0.6907* | 13.1322 | 13.1322 | 13.1322* | 13.1322 | 22.1024 | 78.7932 | **100.8956** |

\* **Fallback:** arie/perimetru spate = față (`back_area_face_fallback`, `back_cut_face_fallback`) — lipsă `backing_area_m2` / `backing_cnc_cutting_perimeter_ml` dedicat pe ambele workspace-uri.

**Delta shanfren Forex (true − false):**

| Workspace | Δ operation EUR | Expected (back cut ml × 1.5) |
|-----------|-----------------|------------------------------|
| Ana Maria | 37.5282 | 25.0188 × 1.5 = 37.5282 ✓ |
| PBL | 19.6983 | 13.1322 × 1.5 = 19.6983 ✓ |

Material cost identic între false/true (corect — șanfrenul nu schimbă m²).

---

## Ana Maria — `shanfren_forex=false`

**Workspace:** `2aeda68b-09e0-46af-ba1e-31b0a47482d7`

### Material rows

| Component | Registry | qty m² | unit € | cost € |
|-----------|----------|--------|--------|--------|
| FACE_PLEXI | MAT-ACP-FATA-LITERE | 1.2638 | 16.0 | 20.2208 |
| BACK_FOREX | MAT-SPATE-PVC-LITERE | 1.2638 | 16.0 | 20.2208 |

### Operation rows

| operation_key | ml | cost € |
|---------------|-----|--------|
| cnc_cut_face_plexi | 25.0188 | 37.5282 |
| cnc_shanfren_face_plexi | 25.0188 | 37.5282 |
| cnc_cut_back_forex | 25.0188 | 37.5282 |

**Absent:** `cnc_shanfren_back_forex`

### Formulas checked

- 25.0188 × 1.5 = 37.5282 (×3 operații) ✓
- 1.2638 × 16 = 20.2208 (×2 materiale) ✓
- material 40.4416 + operation 112.5846 = **153.0262** ✓

### Task draft order

`PREPARE_CNC_FILES` → `CUT_FACE_PLEXI` → `SHANFREN_FACE_PLEXI` → `CUT_BACK_FOREX` → `CLEAN_AND_CHECK_PARTS` → `PACKAGE_FACE_BACK_PARTS` (6 taskuri)

**Absent:** `SHANFREN_BACK_FOREX`

### Warnings

- `v1_cnc_only_scope` (info)
- `task_order_logical_not_physical` (info)
- `back_area_face_fallback` (warning)
- `back_cut_face_fallback` (warning)
- `shanfren_length_derived_candidate` (info)

### Manual inputs

`[]`

### Side-effect boundaries

`createsQuote=false`, `createsRealTasks=false`, `consumesStock=false`, `preview_only=true`

---

## Ana Maria — `shanfren_forex=true`

Identic cu false, plus:

### Operation row adăugat

| operation_key | ml | cost € |
|---------------|-----|--------|
| cnc_shanfren_back_forex | 25.0188 | 37.5282 |

### Task draft order (7 taskuri)

… → `CUT_BACK_FOREX` → **`SHANFREN_BACK_FOREX`** → `CLEAN_AND_CHECK_PARTS` → …

### Formulas checked

- operation total: 112.5846 + 37.5282 = **150.1128** ✓
- total internal: 40.4416 + 150.1128 = **190.5544** ✓

### Warnings extra

- `shanfren_back_length_derived_candidate`

---

## PBL — `shanfren_forex=false`

**Workspace:** `a6cb9f56-2d16-4a53-b569-d5fd51cabfe2`

### Quantities

- face area: **0.6907 m²** (align cu material review audit)
- face/back cut ml: **13.1322** (align cu `cutting_perimeter_ml` persisted PBL)

### Totals

- material: **22.1024 EUR**
- operation: **59.0949 EUR** (= 13.1322 × 1.5 × 3)
- total: **81.1973 EUR**

### Task drafts

6 taskuri — fără `SHANFREN_BACK_FOREX`

---

## PBL — `shanfren_forex=true`

### Totals

- material: **22.1024 EUR** (unchanged)
- operation: **78.7932 EUR** (= 13.1322 × 1.5 × 4)
- total: **100.8956 EUR**

### Task drafts

7 taskuri — cu `SHANFREN_BACK_FOREX` la order_index 5

---

## Verificări globale (4/4 runs)

| Check | Result |
|-------|--------|
| Șanfren față mereu activ | ✓ 4/4 |
| Șanfren Forex doar când `shanfren_forex=true` | ✓ |
| Fără rând `cnc_shanfren_back_forex` când false | ✓ |
| `SHANFREN_BACK_FOREX` task doar când true | ✓ |
| Formule ml × 1.5 pe fiecare operation row | ✓ 4/4 |
| `createsQuote` / `createsRealTasks` / `consumesStock` | ✓ false pe toate |
| ExecutionPlan / tasks_json / stock / quote DB | ✓ neatinse (read-only service) |
| Finisaje Oracal/print/etc. | ✓ absente din payload |

---

## Observații owner

1. **Perimetru Ana Maria:** draft folosește **25.0188 ml** (din `cutting_perimeter_ml` / geometry merged), nu 24.073 ml din audit UI label — surse diferite câmp geometry; de confirmat cu operator care contur e canonical pentru cost prep.
2. **Spate fallback:** pe ambele fișiere, Forex area/cut = față — cost spate este estimativ până la backing geometry dedicat.
3. **Registry bug:** fix necesar înainte de HTTP live; inclus în același branch post-verify.

---

## Comenzi

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_tpl_volumetric_face_back_prep_cost_draft.py -q
# 8 passed

# Numeric capture (local dev.db):
$env:DATABASE_URL='sqlite+aiosqlite:///C:/Users/offic/workos/backend/dev.db'
.\.venv\Scripts\python.exe C:\Users\offic\workos\tmp\_verify_face_back_prep_v1_numeric.py
```

## Verdict

**PASS cu rezerve documentate** — formulele V1 sunt coerente pe Ana Maria și PBL; șanfren Forex toggle funcționează; boundary read-only respectat; fallback spate trebuie marcat operator review.
