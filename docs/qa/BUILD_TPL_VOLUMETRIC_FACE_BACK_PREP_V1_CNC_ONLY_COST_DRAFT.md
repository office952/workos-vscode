# BUILD — TPL-VOLUMETRIC-FACE-BACK-PREP V1 CNC-Only Cost Draft

**Date:** 2026-06-24  
**Branch:** `local/integration-pr4-plus-svg-path`  
**Contract:** `docs/architecture/TPL_VOLUMETRIC_FACE_BACK_PREP_TEMPLATE_CONTRACT.md`

## 1. Scop

Primul build implementabil pentru template-ul parțial **`TPL-VOLUMETRIC-FACE-BACK-PREP`**: cost intern draft read-only pentru față plexiglas + spate Forex și operații CNC (debitare + șanfren/canal), fără finisaje.

## 2. Ce include V1

- Componente `FACE_PLEXI` și `BACK_FOREX`
- Materiale: plexiglas 3 mm, Forex 10 mm (registry)
- Operații CNC separate: debitare + șanfren la **1.5 EUR/ml** fiecare
- Taskuri draft ordonate (preview only)
- Endpoint read-only GET cost draft
- Teste unitare service

## 3. Ce exclude V1

Oracal, print, laminare, policromie, colantare, pregătire print, cant, LED, cabluri, surse, suport, montaj, asamblare, stock, taskuri reale, ExecutionPlan, tasks_json, quote client, CostEngine final.

Finisaje → **Faza 2**.

## 4. Formule cost

| Rând | Formulă |
|------|---------|
| Material plexi | `face_area_sqm × unit_price_registry` |
| Material Forex | `back_area_sqm × unit_price_registry` |
| Debitare față | `face_cut_length_ml × 1.5 EUR` |
| Șanfren față | `shanfren_face_length_ml × 1.5 EUR` (default = cut length, derived candidate) |
| Debitare spate | `back_cut_length_ml × 1.5 EUR` |
| Șanfren spate | `back_shanfren_length_ml × 1.5 EUR` dacă activ |

Total intern = sumă materiale + operații când nu există prețuri lipsă sau input manual obligatoriu.

## 5. Material keys

| Logical key | Registry code | Notă |
|-------------|---------------|------|
| `plexiglas_3mm` | `MAT-ACP-FATA-LITERE` | Cod istoric ACP; material real PMMA 3 mm |
| `forex_10mm` | `MAT-SPATE-PVC-LITERE` | Cod istoric PVC; display Forex 10 mm |

## 6. Operații CNC

| operation_key | task_key | Tarif |
|---------------|----------|-------|
| `cnc_cut_face_plexi` | `CUT_FACE_PLEXI` | 1.5 EUR/ml |
| `cnc_shanfren_face_plexi` | `SHANFREN_FACE_PLEXI` | 1.5 EUR/ml |
| `cnc_cut_back_forex` | `CUT_BACK_FOREX` | 1.5 EUR/ml |
| `cnc_shanfren_back_forex` | `SHANFREN_BACK_FOREX` | 1.5 EUR/ml (opțional) |

## 7. Taskuri draft

Ordine fără șanfren spate:

`PREPARE_CNC_FILES` → `CUT_FACE_PLEXI` → `SHANFREN_FACE_PLEXI` → `CUT_BACK_FOREX` → `CLEAN_AND_CHECK_PARTS` → `PACKAGE_FACE_BACK_PARTS`

Cu șanfren spate: + `SHANFREN_BACK_FOREX` după `CUT_BACK_FOREX`.

## 8. Read-only

- `preview_only: true`
- `creates_real_tasks: false`
- `consumes_stock: false`
- `creates_quote: false`

## 9. Ce nu creează

Quote, order, task DB rows, ExecutionPlan, tasks_json, inventory deductions, CostEngine commercial totals.

## 10. Fișiere

| File | Rol |
|------|-----|
| `backend/services/tpl_volumetric_face_back_prep_cost_draft_service.py` | Builder + workspace loader |
| `backend/schemas/intake_v4.py` | Response models |
| `backend/routers/intake_v4_workspaces.py` | GET endpoint |
| `backend/tests/test_tpl_volumetric_face_back_prep_cost_draft.py` | Tests |

## 11. Endpoint

```http
GET /api/v1/intake-v4/workspaces/{workspace_id}/volumetric-face-back-prep/cost-draft
Query: shanfren_forex (optional bool)
```

## 12. Comenzi + teste

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_tpl_volumetric_face_back_prep_cost_draft.py -q
```

## 13. Boundary

Nu modifică CostEngine, Pricing Registry rates, stock, UI React (V1 backend-only).
