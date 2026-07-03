# TPL-VOLUMETRIC-FACE-BACK-PREP — ProductSystem Integration

**Date:** 2026-06-24  
**Branch:** `local/integration-pr4-plus-svg-path`  
**Build:** `INTEGRATE_TPL_VOLUMETRIC_FACE_BACK_PREP_IN_PRODUCTSYSTEM_REGISTRY`

---

## Verdict

**`TPL-VOLUMETRIC-FACE-BACK-PREP`** is a **ProductSystem partial template** (module), not an Intake V4 feature flag and not final CostEngine pricing.

| Layer | Role |
|-------|------|
| **ProductSystem** | Owns template key, metadata, components, operations, material intent, draft task order |
| **Intake V4** | Consumes the template via read-only cost draft endpoint for operator review |
| **Cost draft service** | Computes temporary internal numbers; no quote/order/stock/tasks |
| **CostEngine / Quote / Production** | Future consumers — out of V1 scope |

---

## Canonical template key

```txt
TPL-VOLUMETRIC-FACE-BACK-PREP
```

Version: **`v1-cnc-only`**  
Scope: **`partial_template`**  
Status: **`draft_internal`** (seeded `active=false`)

---

## Relationship to TPL-VOLUMETRIC-LETTERS

The full volumetric letters template remains:

```txt
TPL-VOLUMETRIC-LETTERS
```

**`TPL-VOLUMETRIC-FACE-BACK-PREP`** is a reusable partial module for face plexiglas + back Forex preparation only. A future composition may embed or reference it inside the full letters template; V1 registers it as a standalone ProductSystem row without activating commercial quote scope.

Metadata field: `reusable_module_of = TPL-VOLUMETRIC-LETTERS`.

---

## Where truth lives

| Artifact | Location |
|----------|----------|
| Canonical contract (Python) | `backend/services/tpl_volumetric_face_back_prep_productsystem_contract.py` |
| ProductSystem DB seed | `backend/seeds/seed_tpl_volumetric_face_back_prep_template.py` → `product_templates` |
| Seed pipeline | `backend/scripts/seed_sync_all.py` (after BUILD4 templates) |
| Intake V4 consumer | `GET /api/v1/intake-v4/workspaces/{id}/volumetric-face-back-prep/cost-draft` |
| Cost draft builder | `backend/services/tpl_volumetric_face_back_prep_cost_draft_service.py` |

The Intake V4 endpoint is **not** the source of truth for template identity — it reads workspace geometry and registry prices, then applies the ProductSystem contract.

---

## Components (V1)

| Key | Material default | Thickness | Shanfren |
|-----|------------------|-----------|----------|
| `FACE_PLEXI` | `plexiglas_3mm` | 3 mm | Required (`cnc_channel`) |
| `BACK_FOREX` | `forex_10mm` | 10 mm | Optional (`cnc_channel_optional`) |

---

## Material mappings (historic registry aliases)

| Logical key | Registry code | Notes |
|-------------|---------------|-------|
| `plexiglas_3mm` | `MAT-ACP-FATA-LITERE` | Historic name; do not rename global registry in V1 |
| `forex_10mm` | `MAT-SPATE-PVC-LITERE` | Historic name; do not rename global registry in V1 |

---

## Operations (V1 CNC)

Fixed rule CNC rows: **1.5 EUR/ml** (`CNC_RATE_EUR_PER_ML`).

| Key | Component | Required | Notes |
|-----|-----------|----------|-------|
| `PREPARE_CNC_FILES` | GENERAL | yes | Draft internal, no EUR |
| `CUT_FACE_PLEXI` | FACE_PLEXI | yes | Maps to `cnc_face_cutting_plexiglas_3mm` |
| `SHANFREN_FACE_PLEXI` | FACE_PLEXI | yes | Maps to `cnc_face_bevel_plexiglas_3mm` |
| `CUT_BACK_FOREX` | BACK_FOREX | yes | Maps to `cnc_backing_cutting_forex_10mm` |
| `SHANFREN_BACK_FOREX` | BACK_FOREX | no | When `shanfren_forex=true` |
| `CLEAN_AND_CHECK_PARTS` | GENERAL | yes | Draft internal |
| `PACKAGE_FACE_BACK_PARTS` | GENERAL | yes | Draft internal |

Shared CNC keys align with `backend/services/shared_cnc_operation_model.py` — no duplicate operation model.

---

## Draft task order

Without Forex shanfren:

```txt
PREPARE_CNC_FILES → CUT_FACE_PLEXI → SHANFREN_FACE_PLEXI → CUT_BACK_FOREX
→ CLEAN_AND_CHECK_PARTS → PACKAGE_FACE_BACK_PARTS
```

With Forex shanfren (`shanfren_forex=true`):

```txt
… → CUT_BACK_FOREX → SHANFREN_BACK_FOREX → CLEAN_AND_CHECK_PARTS → …
```

Ordering is defined in `task_draft_order()`; V1 does **not** persist `tasks_json` or create ExecutionPlan rows.

---

## Explicit exclusions (V1)

No cant, edge vinyl, lighting, wiring, PSU, support, mounting, final assembly, stock consumption, real production tasks, final quote, Oracal/print/lamination/policromie finishes.

---

## Next phase (not this build)

- CostEngine formula handlers wired to partial template
- Quote handoff for face/back-only orders
- Production task generation from ProductSystem operations
- Composition hook inside `TPL-VOLUMETRIC-LETTERS`
