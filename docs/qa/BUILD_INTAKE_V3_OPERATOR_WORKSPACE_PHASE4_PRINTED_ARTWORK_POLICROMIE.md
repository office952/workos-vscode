# BUILD: Intake V3 Operator Workspace — Phase 4 Printed Artwork / Policromie

**Date:** 2026-06-19  
**Build:** `BUILD_INTAKE_V3_OPERATOR_WORKSPACE_PHASE4_PRINTED_ARTWORK_POLICROMIE`  
**Status:** PASS

---

## 1. Verdict

**PASS** — Printed artwork / policromie is a first-class layer finish on `layer_finish_assignments[]`, with readiness blockers, quote preview extension, read-only materials preview, and operator UI — no CostEngine, inventory, or production side effects.

---

## 2. Branch / HEAD

| Field | Before | After |
|-------|--------|-------|
| Branch | `local/integration-pr4-plus-svg-path` | same |
| HEAD | `f167e86eaef2fd15c3cd40dc1ba83b4e3fc625f6` | _(updated at commit)_ |

---

## 3. Git status

**Before:** tracked clean after Phase 3; `?? tmp/`  
**After:** Phase 4 backend + frontend + tests + QA doc committed; `tmp/` untracked

---

## 4. Files changed

| Area | Files |
|------|-------|
| Schema / contracts | `backend/schemas/intake_v3.py`, `backend/data_models/intake_v3_contracts.py` |
| Layer finish service | `backend/services/intake_v3_layer_finish_assignment_service.py` |
| Layer roles | `backend/services/intake_v3_layer_role_confirmation_service.py` |
| Backend tests | `backend/tests/test_intake_v3_printed_artwork_layer_finish.py` (new) |
| Frontend contracts / helpers | `layerFinishContracts.ts`, `operatorLayerArtworkFinishForm.ts`, `layerRoleConfirmationContracts.ts`, `blockerMessages.ts` |
| Operator UI | `IntakeV3OperatorLayerArtworkFinishCard.tsx` (new), `IntakeV3OperatorPrintedArtworkMaterialsPreview.tsx` (new), `IntakeV3OperatorLayerFinishSetup.tsx`, `IntakeV3OperatorFinishesTab.tsx`, `IntakeV3OperatorLayerSetup.tsx`, `IntakeV3OperatorMaterialsTab.tsx`, `IntakeV3OperatorReadinessTab.tsx` |
| Frontend tests | `IntakeV3OperatorWorkspaceApp.test.tsx`, `operatorLayerArtworkFinishForm.test.ts` (new) |
| QA | this document |

---

## 5. Backend contract

Extended Phase 3 model — no parallel system.

- **`IntakeV3PrintedArtworkFinishSpec`** nested on `IntakeV3LayerFinishAssignment.printed_artwork_finish`
- Fields: `enabled`, `print_method`, `media_family`, `media_code`, `laminate_enabled`, `laminate_type`, `contour_cut`, `white_ink`, `white_backing`, `area_sqm`, `waste_percent`, `notes`, `is_confirmed`, confirmation metadata
- **Print methods:** `printed_vinyl`, `uv_print`, `latex_print`, `solvent_print`, `other`
- **Laminate types:** `gloss`, `matte`, `dry_erase`, `none`, `other`
- **Artwork roles:** `printed_artwork`, `logo`, `artwork`, `policromie` — productive; require artwork finish setup
- **`IntakeV3LayerFinishPreviewItem`** extended with artwork fields for quote preview

---

## 6. Frontend UI

- **Finishes tab:** artwork layers render `IntakeV3OperatorLayerArtworkFinishCard` (Atoms-style) — print method, media, laminate, contour cut, white ink/backing, area estimate (read-only), notes, confirm
- **Not Oracal path:** artwork layers do not show face vinyl / ColorRegistry controls
- **Status badges:** Needs artwork setup, Needs laminate type, Needs contour decision, Confirmed, Pending
- **Layer setup tab:** hint routes artwork layers to Finishes tab
- **Materials tab:** `IntakeV3OperatorPrintedArtworkMaterialsPreview` — read-only production estimate rows from `layer_finish_preview`

---

## 7. Readiness / quote gate

Blockers (when artwork layer is productive and unconfirmed):

| Code | Meaning |
|------|---------|
| `MISSING_PRINTED_ARTWORK_SETUP` | Artwork finish not enabled |
| `MISSING_PRINTED_ARTWORK_PRINT_METHOD` | Print method required |
| `MISSING_PRINTED_ARTWORK_LAMINATE_TYPE` | Laminate enabled but type missing |
| `MISSING_PRINTED_ARTWORK_CONTOUR_DECISION` | Contour cut must be explicit true/false |
| `UNCONFIRMED_PRINTED_ARTWORK` | Setup not confirmed |

- **Exempt:** `technical_cutouts`, `reference`, `ignore`
- **Quote gate:** Create Guarded Draft Quote blocked with layer-specific message (via readiness `finisaje` section)
- **Backwards compat:** workspaces without `printed_artwork_finish` continue on Phase 3 global/layer Oracal path

---

## 8. Materials read-only behavior

- Confirmed artwork appears in materials preview with media, laminate, contour basis, white ink/backing, area, waste
- No inventory reservation, StockMovement, PurchaseOrder, CostEngine, or final price
- Missing area: `"Area estimate unavailable — requires geometry/artwork area confirmation."`

---

## 9. Backwards compatibility

- Old workspaces without `printed_artwork_finish` pass existing Phase 3 tests
- Global / group / letter finish fallback preserved
- Technical route unchanged
- Artwork layers skip Oracal global sync bridge

---

## 10. Tests run

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v3_layer_finish_assignments.py tests/test_intake_v3_printed_artwork_layer_finish.py -q

cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/pages/IntakeV3OperatorWorkspaceApp.test.tsx src/lib/intakeV3/operatorLayerArtworkFinishForm.test.ts
```

**Results:** backend 17/17 PASS; frontend 23/23 PASS

---

## 11. Boundary confirmations

| Boundary | Status |
|----------|--------|
| No CostEngine changes | ✓ |
| No pricing coupling | ✓ |
| No inventory mutation | ✓ |
| No StockMovement | ✓ |
| No ExecutionTask / ExecutionPlan | ✓ |
| No PO / SupplierOrder | ✓ |
| Quote guarded via readiness | ✓ |
| Materials read-only preview only | ✓ |
| Technical route preserved | ✓ |
| No push | ✓ |

---

## 12. Deferred to Phase 5

- LED / PSU layer setup
- Lighting electrical validation
- E2E hardening matrix (Phase 6)
- CostEngine / inventory / production handoff

---

## 13. Safe to continue Phase 5?

**Yes** — Phase 4 layer-based printed artwork contract is stable, tested, and isolated from pricing/production. Phase 5 can extend the same `layer_finish_assignments[]` pattern for lighting without rework.
