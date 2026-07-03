# FIX — TPL-VOLUMETRIC-FACE-BACK-PREP CNC Pass Counts & Vector Perimeter Truth

**Date:** 2026-06-24  
**Branch:** `local/integration-pr4-plus-svg-path`  
**Build:** `FIX_TPL_VOLUMETRIC_FACE_BACK_PREP_CNC_PASS_COUNTS_AND_VECTOR_PERIMETER_TRUTH`

---

## 1. Problem

V1 cost draft priced CNC operations as **P × 1.5 EUR** per row (1 pass each). Owner rule requires **pass_count × P × 1.5 EUR**, especially for Forex 10 mm (3 passes without shanfren, 5 total with shanfren). Back perimeter also incorrectly fell back to face perimeter for CNC costing.

---

## 2. Owner rule

```txt
Perimetrul vectorilor este sursa de adevăr.
Cost CNC = perimetru vectorial real × număr treceri × 1.5 EUR/ml
```

---

## 3. Correct formulas

| Component | Condition | Formula |
|-----------|-----------|---------|
| FACE_PLEXI cut | always | P_face × 1 × 1.5 |
| FACE_PLEXI shanfren | always | P_face × 1 × 1.5 |
| FACE total | | P_face × 2 × 1.5 |
| BACK_FOREX cut | no shanfren | P_back × 3 × 1.5 |
| BACK_FOREX cut + shanfren | with shanfren | P_back × 3 × 1.5 + P_back × 2 × 1.5 = P_back × 5 × 1.5 |

---

## 4. What changed

| File | Change |
|------|--------|
| `backend/services/tpl_volumetric_face_back_prep_cost_draft_service.py` | pass_count on operations; vector-only perimeter resolution; no face→back CNC fallback |
| `backend/services/tpl_volumetric_face_back_prep_productsystem_contract.py` | pass count + vector perimeter key constants |
| `backend/schemas/intake_v4.py` | `pass_count`, `perimeter_source`, `perimeter_confidence`, `is_vector_perimeter_source` on operation rows |
| `backend/tests/test_tpl_volumetric_face_back_prep_cost_draft.py` | pass count + vector protection tests |
| `docs/architecture/TPL_VOLUMETRIC_FACE_BACK_PREP_TEMPLATE_CONTRACT.md` | sections 8, 8.1, 9 updated |

---

## 5. Vector perimeter protection

- Face keys: `cnc_cutting_perimeter_ml`, `face_cutting_perimeter_ml`, `cutting_perimeter_ml`
- Back keys: `backing_cnc_cutting_perimeter_ml`, `back_cutting_perimeter_ml`
- Missing → `manual_required` + warning `vector_perimeter_missing_or_low_confidence`
- No bbox / nesting / face-fallback for CNC cost

---

## 6. Tests

```powershell
Set-Location C:\Users\offic\workos\backend
.\.venv\Scripts\python.exe -m pytest tests/test_tpl_volumetric_face_back_prep_cost_draft.py -q
```

**Result:** 11 passed (cost draft) + 13 passed (registry, unchanged).

---

## 7. Boundaries (unchanged)

No final CostEngine, quote/order, real tasks, ExecutionPlan, `tasks_json`, stock consumption, or Intake V4 UI changes.
