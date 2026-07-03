# BUILD — TPL-VOLUMETRIC-FACE-BACK-PREP ProductSystem Registry

**Date:** 2026-06-24  
**Branch:** `local/integration-pr4-plus-svg-path`  
**Boundary:** ProductSystem registration + contract alignment only

---

## 1. Purpose

Register **`TPL-VOLUMETRIC-FACE-BACK-PREP`** in the ProductSystem template registry so face/back prep is a first-class partial template — not isolated Intake V4 logic.

---

## 2. Where the template is stored

| Store | Path / table |
|-------|----------------|
| Canonical Python contract | `backend/services/tpl_volumetric_face_back_prep_productsystem_contract.py` |
| DB seed module | `backend/seeds/seed_tpl_volumetric_face_back_prep_template.py` |
| Persisted row | `product_templates.template_code = TPL-VOLUMETRIC-FACE-BACK-PREP` |
| Pipeline | `backend/scripts/seed_sync_all.py` → `tpl_volumetric_face_back_prep` step |

---

## 3. Template key

```txt
TPL-VOLUMETRIC-FACE-BACK-PREP
```

---

## 4. Metadata

- **label:** Pregătire fețe plexiglas + spate Forex  
- **family:** `volumetric_letters` / `litere_volumetrice`  
- **scope:** `partial_template`  
- **version:** `v1-cnc-only`  
- **status:** `draft_internal`  
- **active:** `false` (commercial scope remains `TPL-VOLUMETRIC-LETTERS` only)

---

## 5. Components

- `FACE_PLEXI` — plexiglas 3 mm, shanfren required  
- `BACK_FOREX` — Forex 10 mm, shanfren optional  

---

## 6. Material mappings

| Component | Logical | Registry code |
|-----------|---------|---------------|
| FACE_PLEXI | `plexiglas_3mm` | `MAT-ACP-FATA-LITERE` |
| BACK_FOREX | `forex_10mm` | `MAT-SPATE-PVC-LITERE` |

Prices unchanged; historic alias names documented, not renamed.

---

## 7. Operations

Seven V1 operations; four CNC ml-priced at **1.5 EUR/ml** (`fixed_rule`):

- `CUT_FACE_PLEXI`, `SHANFREN_FACE_PLEXI`, `CUT_BACK_FOREX`, `SHANFREN_BACK_FOREX`  
- Plus `PREPARE_CNC_FILES`, `CLEAN_AND_CHECK_PARTS`, `PACKAGE_FACE_BACK_PARTS` (draft internal, EUR 0)

---

## 8. Task draft order

See `task_draft_order(shanfren_forex_enabled=…)` in the contract module.  
No real tasks, no `tasks_json`, no ExecutionPlan.

---

## 9. Intake V4 endpoint (consumer)

```txt
GET /api/v1/intake-v4/workspaces/{workspace_id}/volumetric-face-back-prep/cost-draft?shanfren_forex=
```

Read-only preview; uses ProductSystem template key/version in response. Not authoritative for registry shape.

---

## 10. Relation to TPL-VOLUMETRIC-LETTERS

Partial prep module; `reusable_module_of = TPL-VOLUMETRIC-LETTERS`. Full template unchanged; BUILD4 still seeds exactly six commercial templates.

---

## 11. What this build does NOT create

- Final CostEngine pricing  
- Quote or order  
- Real production tasks  
- ExecutionPlan / `tasks_json`  
- Stock consumption  
- Intake V4 UI changes  
- Finishes (Oracal, print, lamination, policromie)

---

## 12. Files changed

- `backend/services/tpl_volumetric_face_back_prep_productsystem_contract.py` (new)  
- `backend/seeds/seed_tpl_volumetric_face_back_prep_template.py` (new)  
- `backend/scripts/seed_sync_all.py`  
- `backend/services/tpl_volumetric_face_back_prep_cost_draft_service.py` (imports contract)  
- `backend/tests/test_tpl_volumetric_face_back_prep_productsystem_registry.py` (new)  
- `backend/tests/test_tpl_volumetric_face_back_prep_cost_draft.py` (import alignment)  
- `docs/architecture/TPL_VOLUMETRIC_FACE_BACK_PREP_PRODUCTSYSTEM_INTEGRATION.md` (new)  
- `docs/architecture/TPL_VOLUMETRIC_FACE_BACK_PREP_TEMPLATE_CONTRACT.md` (ProductSystem ownership section)

---

## 13. Tests

```powershell
Set-Location C:\Users\offic\workos\backend
.\.venv\Scripts\python.exe -m pytest tests/test_tpl_volumetric_face_back_prep_cost_draft.py -q
.\.venv\Scripts\python.exe -m pytest tests/test_tpl_volumetric_face_back_prep_productsystem_registry.py -q
```

---

## 14. Commands run

```powershell
Set-Location C:\Users\offic\workos\backend
.\.venv\Scripts\python.exe -m pytest tests/test_tpl_volumetric_face_back_prep_cost_draft.py -q
.\.venv\Scripts\python.exe -m pytest tests/test_tpl_volumetric_face_back_prep_productsystem_registry.py -q
```

**Result:** 21 passed (8 cost draft + 13 registry/contract/seed).

---

## 15. Boundary / next steps

- Wire CostEngine handlers to partial template operations  
- Optional composition inside `TPL-VOLUMETRIC-LETTERS` components_json  
- Production handoff adapter when real tasks are in scope
