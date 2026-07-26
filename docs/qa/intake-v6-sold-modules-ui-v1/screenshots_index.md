# Intake V6 Sold Modules UI — Screenshots

**URL base:** http://127.0.0.1:3000/intake
**Operator route:** `/intake-v6/{workspaceId}/operator`
**Fixture workspace:** `22ef834d-f2d0-453b-a7a7-118928c98a39` (IV6 audit fixture, gradi-curat lineage)

| File | State |
|------|-------|
| `01_step1_full_product_default.png` | Default **Produs complet** |
| `02_step1_subset_face_cant_selected.png` | Subset mode, **FACE + RETURN-CANT** checked and persisted |
| `03_step1_empty_subset_validation.png` | Subset mode, zero checks — validation error visible |

**Expected backend result (FACE-only):** BOM runtime modules include `debitare_fata` only; cant/back/finisaje excluded (`test_intake_v6_offer_scope_persistence.py`).

**Dynamic field hiding:** not implemented in V1 (deferred to V1.1).
