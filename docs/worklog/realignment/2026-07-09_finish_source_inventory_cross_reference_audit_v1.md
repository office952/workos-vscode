# FINISH_SOURCE_INVENTORY_CROSS_REFERENCE_AUDIT_V1

**Date:** 2026-07-09  
**Mode:** SOURCE / INVENTORY CROSS-REFERENCE AUDIT ONLY — NO ACTIVATION  
**HEAD before:** `c6b06d7` — Add FINISH estimated price draft

---

## 1. Verdict

**PARTIAL**

Audit completed. Primary inventory/pricing keys for FINISH face and most artwork variants are **found in seeds and Intake V4 runtime**. Artwork print/lam can reuse the same material/service registry keys as face (evidence_only). Remaining gaps:

1. **`artwork_print_only`** — canonical Product System variant exists; Intake V4 `PRINT_ARTWORK_EXECUTION_TYPES` does **not** include `print_only` (runtime path missing).
2. **Application labor key conflict** — FINISH draft uses `FACE_VINYL_APPLICATION_LABOR` (5 EUR/mp); Intake V4 artwork print/lam application rows use **`WC_VINYL_APPLICATION`** workcenter (legacy fallback 3 EUR/mp when registry absent).
3. **`mp_artwork_area`** — owner-confirmed quantity basis; produced in Intake V4 via `quote_geometry.artwork_boxes` but **not wired** to Product System component-first runtime.
4. Seed material names are **face-oriented** (“print față litere”) though keys are reused for artwork in Intake V4.

No pricing activation. No registry writes. No Product Truth writes.

---

## 2. Scope

Audit only. Evidence classification and cross-reference map. No activation, no backend/seed/DB changes, no ProductDefinition bridge.

---

## 3. HEAD

| Field | Value |
|-------|-------|
| Branch | `main` |
| HEAD before | `c6b06d7` |
| Worktree | Pre-existing dirty: `.gitignore`, old QA smoke PNGs, unrelated untracked QA/scripts (not touched) |

---

## 4. Sources read

**Worklog / owner input**

- `docs/worklog/owner-input/finish_component_truth_owner_decision_v1.md`
- `docs/worklog/owner-input/finish_estimated_price_draft_pending_values.md`
- `docs/worklog/realignment/2026-07-09_finish_estimated_price_draft_v1.md`
- `docs/worklog/owner-input/face_price_registry_alignment_owner_decision_v1.md`
- `docs/worklog/owner-input/face_component_truth_owner_decision_v1.md`
- `docs/architecture/product-system/CANONICAL_FINISH_ENUM_MAP_v1.md`

**Product System (readonly FINISH)**

- `frontend/src/features/product-system/componentFirstFinishEstimatedPriceDraft.ts`
- `frontend/src/features/product-system/FinishEstimatedPriceDraftPanel.tsx`
- `frontend/src/features/product-system/componentFirstFinishTruthWorkshop.ts`
- `frontend/src/features/product-system/FinishTruthWorkshopPanel.tsx`
- `frontend/src/features/product-system/canonicalFinishEnumMap.ts`
- `frontend/src/features/product-system/componentFirstFaceEstimatedPriceDraft.ts` (FACE pattern reference)

**Backend seeds / runtime (read-only audit)**

- `backend/seeds/seed_volumetric_owner_confirmed_prices.py`
- `backend/seeds/seed_intake_v5_volumetric_letters_pricing.py`
- `backend/seeds/seed_volumetric_workcenter_rates.py`
- `backend/services/intake_v4_material_breakdown_service.py`
- `backend/services/return_cant_product_truth_bridge.py`
- `backend/tests/test_intake_v4_material_breakdown.py` (artwork row behavior)

**Frontend intake contracts**

- `frontend/src/lib/svgArtworkContracts.ts` (`print_only` token exists)

---

## 5. Evidence map

| Key | Found? | Location | Type | Classification | FINISH use | Notes |
|-----|--------|----------|------|----------------|------------|-------|
| MAT-ORACAL-641 | YES | `seed_volumetric_owner_confirmed_prices.py`, `seed_intake_v5_volumetric_letters_pricing.py`; Intake V4 `MAT-ORACAL-641` artwork rows | inventory material | evidence_only | Face + artwork Oracal | Owner purchase 6.5 EUR/mp; seed notes reference `letter_face_area_m2`. Artwork runtime maps `ORACAL_641` → `MAT-ORACAL-641`. Not Product System registry authority. |
| MAT-ORACAL-651 | YES | Same seeds; default `face_vinyl` in `MATERIAL_REGISTRY_CODES` | inventory material | evidence_only | Face + artwork Oracal | 9.0 EUR/mp. Artwork `cut_vinyl` / `ORACAL_651` maps to same key. |
| MAT-ORACAL-8500 | YES | Same seeds | inventory material | evidence_only | Face + artwork translucent | 20.0 EUR/mp. Artwork `translucent_vinyl` / `ORACAL_8500`. |
| MAT-VINYL-PRINT-LAMINATED | YES | Seeds; `MATERIAL_REGISTRY_CODES["laminated_vinyl"]`; Intake V4 `_append_print_laminate_quote_rows` | inventory material (combined) | evidence_only | Face combined + artwork print/lam | 10.0 EUR/mp combined material only — no labor/services included. Seed name: “print + laminare **față litere**”. |
| MAT-VINYL-PRINT | YES | Seeds; `MATERIAL_REGISTRY_CODES["print_vinyl"]` | inventory material | evidence_only | Face split + artwork print | 1.5 EUR/mp material only. Print service separate. |
| LARGE_FORMAT_PRINT | YES | `seed_volumetric_workcenter_rates.py`, `seed_intake_v5_volumetric_letters_pricing.py`; Intake V4 `workcenter_rates:LARGE_FORMAT_PRINT:per_square_meter` | workcenter service rate | evidence_only | Face split + artwork print/lam | 8.5 EUR/mp. Active in pricing seeds but FINISH workshop = evidence_only only. |
| LAMINATION | YES | Same workcenter seeds; Intake V4 `WC_LAMINATE` / `LAMINATION` tpl key | workcenter service rate | evidence_only | Face split + artwork print/lam | 5.0 EUR/mp. Separable from print per owner decision. |
| FACE_VINYL_APPLICATION_LABOR | YES | `seed_volumetric_workcenter_rates.py`, `seed_intake_v5_volumetric_letters_pricing.py` | workcenter labor rate | evidence_only (conflicting_evidence for artwork) | Face Oracal/print application in FINISH draft | 5.0 EUR/mp. Label: “Manoperă aplicare folie **fețe litere**”. Intake V4 **artwork** print/lam uses `WC_VINYL_APPLICATION` instead — see labor conflict. |
| RETURN_CANT_VINYL_APPLICATION_LABOR | YES | `seed_volumetric_workcenter_rates.py`, `return_cant_product_truth_bridge.py` | workcenter labor rate | return_cant_only / not_finish_scope | **Excluded** | 1.0 EUR/ml per linear meter. Dedicated cant labor — must not map to FINISH. |

**Additional legacy intake tokens (not registry keys):** `ORAFOL_PRINT`, `ORAFOL_LAMINATION`, `ORAFOL_PRINT_LAMINATION` appear in Intake V4 test payloads only; runtime resolves to `MAT-VINYL-PRINT` / `MAT-VINYL-PRINT-LAMINATED` via `MATERIAL_REGISTRY_CODES`.

---

## 6. Draft row validation

| Draft row | Current status | Evidence found | Still blocked? | Recommendation |
|-----------|----------------|----------------|----------------|----------------|
| Face Oracal 641 | evidence_only | MAT-ORACAL-641 + FACE_VINYL_APPLICATION_LABOR in seeds | YES (activation) | Keep evidence_only. Keys confirmed. |
| Face Oracal 651 | evidence_only | MAT-ORACAL-651 + labor | YES | Keep evidence_only. |
| Face Oracal 8500 | evidence_only | MAT-ORACAL-8500 + labor | YES | Keep evidence_only. |
| Face print+lam combined | evidence_only | MAT-VINYL-PRINT-LAMINATED 10 EUR/mp + labor | YES | Keep evidence_only. Combined = material only. |
| Face print+lam split | evidence_only | MAT-VINYL-PRINT + LARGE_FORMAT_PRINT + LAMINATION + labor | YES | Keep evidence_only. Split model matches seeds. |
| Artwork Oracal 641 | evidence_only | Same MAT-ORACAL-641; Intake V4 artwork Oracal rows | YES | Keys confirmed for artwork. `mp_artwork_area` runtime handoff to Product System still pending. |
| Artwork print+lam | source_inventory_audit_required | Same keys as face split/combined in Intake V4 `_append_artwork_print_rows` | YES | **Upgrade classification to evidence_only** for material/service keys; retain blocker for labor conflict + Product System geometry handoff. |
| Artwork print only | source_inventory_audit_required | MAT-VINYL-PRINT + LARGE_FORMAT_PRINT exist; **`print_only` not in Intake V4 `PRINT_ARTWORK_EXECUTION_TYPES`** | YES | Remain audit_required / blocked. Owner must decide: add runtime path or retire variant. |
| Artwork Oracal 8500 | evidence_only | MAT-ORACAL-8500; Intake V4 translucent artwork | YES | Keep evidence_only. |
| Artwork none/raw plexi | not_applicable | No FINISH keys (correct) | YES | Keep not_applicable. FACE Plexiglas separate. |

---

## 7. Artwork source assessment

### Artwork print+lam

- **Keys exist:** Intake V4 `_append_artwork_print_rows` uses `_append_print_laminate_quote_rows` with `registry_code` → `MAT-VINYL-PRINT`, `MAT-VINYL-PRINT-LAMINATED`, services `LARGE_FORMAT_PRINT`, `LAMINATION`, application via `WC_VINYL_APPLICATION`.
- **Quantity basis:** `quote_geometry.artwork_boxes|bounding_box_footprint` or `estimated_area_m2` / SVG layer fallback — maps to owner `mp_artwork_area` conceptually.
- **Safe as evidence_only:** YES for material/service keys (same as face). NOT safe to promote to owner-confirmed FINISH pricing or registry authority.
- **Remaining audit flags:** labor key conflict; seed labels face-specific; Product System has no live `mp_artwork_area` producer.

### Artwork print only

- **Canonical enum:** `artwork_print_only` with `execution_type=print_only` in `canonicalFinishEnumMap.ts` and `svgArtworkContracts.ts`.
- **Intake V4 runtime:** `PRINT_ARTWORK_EXECUTION_TYPES` = `{print_laminate, print_translucent, printed_vinyl, printed_laminated_vinyl, printed_vinyl_on_face}` — **`print_only` absent**.
- **Conclusion:** Material/service keys exist in inventory but **no artwork print-only breakdown path** in Intake V4. Stays `source_inventory_audit_required` until owner/runtime decision.

### mp_artwork_area / artwork_instances

- **Owner rule:** `mp_artwork_area` when geometry exists (owner_confirmed).
- **Intake V4:** Area from `artwork_boxes` bounding footprint (`BASIS_ARTWORK_BOX_FOOTPRINT`).
- **Product System:** `componentFirstFinishTruthWorkshop.ts` lists `artwork_instances` input key; blocker: “Artwork geometry handoff pending — mp_artwork_area rule confirmed but runtime source missing”.
- **Conclusion:** Quantity basis rule is sound; **Product System handoff not wired** — blocks readyForPricing regardless of key audit.

### What remains source_inventory_audit_required

| Item | Reason |
|------|--------|
| `artwork_print_only_draft` | No Intake V4 `print_only` execution handler |
| Artwork application labor | `FACE_VINYL_APPLICATION_LABOR` vs `WC_VINYL_APPLICATION` conflict |
| Product System mp_artwork_area | Runtime geometry source not connected to component-first |

---

## 8. Boundary check

| Check | Result |
|-------|--------|
| No RETURN-CANT ownership | DA |
| No FACE base material ownership (MAT-ACP-FATA-LITERE) | DA |
| No RAL minimum ownership | DA |
| No pricing activation | DA |
| No Product Truth live write | DA |
| No Pricing Registry write | DA |
| No ProductDefinition bridge | DA |
| No backend/DB/seed changes in this slice | DA |

---

## 9. Recommended owner questions

1. **Artwork application labor:** Should FINISH artwork use `FACE_VINYL_APPLICATION_LABOR` (5 EUR/mp, face-labeled) or a distinct artwork labor key / `WC_VINYL_APPLICATION` mapping? Intake V4 currently uses the latter for artwork print/lam rows.

2. **Artwork print only:** Keep `artwork_print_only` as owner-confirmed variant? If yes, Intake V4 must add `print_only` to `PRINT_ARTWORK_EXECUTION_TYPES` (or equivalent) before FINISH draft can clear audit.

3. **Shared material keys:** Accept that `MAT-VINYL-PRINT` / `MAT-VINYL-PRINT-LAMINATED` seed names say “față litere” but keys are reused for artwork in Intake V4 — rename later vs document-only?

4. **mp_artwork_area handoff:** Confirm Product System should consume Intake V4 `quote_geometry.artwork_boxes` footprint as the first `mp_artwork_area` source (spec-only; no implementation in this slice).

Do not invent answers. Do not activate pricing.

---

## 10. Next step recommendation

**FINISH_OWNER_PRICE_VALUES_DECISION_V1** — after owner answers labor key + print_only runtime questions.

Alternative if owner wants spec before prices: **FINISH_PRODUCT_TRUTH_HANDOFF_SPEC_V1** (mp_artwork_area / artwork_instances handoff).

Do **not** run **FINISH_DRAFT_PRICE_SOURCE_CLEANUP_V1** until owner confirms labor and print_only.

---

## 11. Cat sunt in directia stabilita

**94/100%** — Source cross-reference map complete; artwork print_only runtime gap and labor key conflict remain before owner price values or activation path.

---

## Audit answers (sections A–F)

### A. Oracal face/artwork

- Keys present in seeds and Intake V4. Classification: **evidence_only** for FINISH Product System (owner decision overrides seed “owner-confirmed purchase” for workshop authority).
- Apply to **both** face and artwork in Intake V4 runtime. Same `MAT-ORACAL-*` keys for artwork Oracal rows.

### B. Print+lam combined

- `MAT-VINYL-PRINT-LAMINATED` present; **material only** at 10 EUR/mp; services/labor separate.
- Face: seed quantity from `letter_face_area_m2`. Artwork: same key via `_append_print_laminate_quote_rows`.
- Safe as **evidence_only** for artwork print+lam material; not registry authority in Product System.

### C. Print split

- `MAT-VINYL-PRINT`, `LARGE_FORMAT_PRINT`, `LAMINATION` all present.
- Split model: material 1.5 + print 8.5 + lam 5.0 EUR/mp (evidence_only).
- Artwork print only: keys exist but **no runtime handler** for `execution_type=print_only`.

### D. Labor

- `FACE_VINYL_APPLICATION_LABOR`: appropriate **evidence** for face finish application per owner decision.
- Artwork-specific: Intake uses `WC_VINYL_APPLICATION` — **conflicting_evidence** with FINISH draft labor ref.
- `RETURN_CANT_VINYL_APPLICATION_LABOR`: **return_cant_only**, excluded.

### E. Quantity basis

- Face: **mp_face_area** — owner_confirmed.
- Artwork: **mp_artwork_area** — owner_confirmed; Intake V4 produces area via artwork box footprint; Product System handoff **pending**.

### F. Boundaries

All preserved. No activation in this slice.
