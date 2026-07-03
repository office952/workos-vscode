# BUILD_INTAKE_V4_REAL_FILE_PRODUCTION_DECISION_TEST_PACK

## Branch / HEAD

| Field | Value |
|-------|-------|
| Branch | `local/integration-pr4-plus-svg-path` |
| HEAD | `b409346fae7abd9975b0bb859cfc987971887423` |
| Test date | 2026-06-22 |

## Test file

| Field | Value |
|-------|-------|
| File | `pbl-layere.svg` |
| Owner location | `C:\Users\offic\Desktop\pbl-layere.svg` |
| Size | 5631 bytes |
| Introduced | Manual upload in Intake V4 UI |
| Hardcoded in app | **No** (`rg pbl-layere` → 0 matches in committed code) |

## Workspace note (important)

Owner confirmed upload on workspace reported earlier as **IV4-0A33B462** (`0e1cc1de-…`), but **persisted data** with `pbl-layere.svg` lives on:

| Field | Value |
|-------|-------|
| Workspace ID | `a6cb9f56-2d16-4a53-b569-d5fd51cabfe2` |
| Code | **IV4-46499080** |
| URL | http://127.0.0.1:3000/intake-v4-app/a6cb9f56-2d16-4a53-b569-d5fd51cabfe2/operator |

Workspace `0e1cc1de-…` / IV4-0A33B462 remains **empty** (no svg_source, no analysis).

---

## Pasul 1 — Upload / Analyzer (persisted backend)

| Check | Result |
|-------|--------|
| Filename | `pbl-layere.svg` ✓ |
| File hash | `c674e8a308d02ebd5ab6ad05df3ecefae43cf42c0689d6e66d6b7fe4ad23c09d` ✓ |
| Analysis bundle persisted | Yes (`svg_analysis_json` present, `upload_status=analyzed`) ✓ |
| Parse errors | 0 ✓ |
| Dimensions (path_geometry) | bbox **2700.0 × 350.0011 mm** (~269.75 × 35 cm viewBox) ✓ |
| Layer count | **3** ✓ |
| Layer names | `Layer_x0020_1`, `Layer_x0020_2`, `Layer_x0020_3` ✓ |
| Colors detected | L1: `url(#id0)` gradient; L2: `#009846`; L3: `#66C3D0` ✓ |
| Child parts | **11** (contour split from 2 path layers + 1 rect part) |
| Nestable | **11 / 11** (all `canNest=true` after split) |
| Non-nestable | 0 |
| Nesting unit | **Child parts only** — 11 placements, all `partId` like `split_layer_*` or `part_layer_*`; **no layer-group nesting** ✓ |
| Stale header check | Hash + filename match `pbl-layere.svg`; sanitization hash differs (`analysis_content_hash` ≠ `source_content_hash`) due to doctype strip — expected ✓ |

### Comparison vs offline preview (QA harness, pre-split)

| Metric | Offline harness | Runtime persisted | Delta / cause |
|--------|-----------------|-------------------|---------------|
| Child parts | 3 | 11 | Contour splitting on compound paths in full pipeline |
| Nestable | 1 | 11 | Split parts become nestable individually |
| Layers | 3 | 3 | Match |
| ViewBox scale | ~270×35 cm | 2700×350 mm bbox | Match (unit conversion) |

**Nesting criterion: PASS** — placements reference child part IDs only.

---

## Pasul 3 — Layer roles / finish setup

| Layer | Auto role | Confirmed role | Color evidence |
|-------|-----------|----------------|----------------|
| Layer_x0020_1 | printed_artwork | printed_artwork | gradient artwork |
| Layer_x0020_2 | face | face | #009846 |
| Layer_x0020_3 | face | face | #66C3D0 |

| Check | Result |
|-------|--------|
| Layer roles confirmation | `confirmation_status=complete`, 3/3 confirmed ✓ |
| Finish setup global | `confirmed=true`, illuminated, PSU `[200,60]`, return 60mm ✓ |
| Per-group finishes | `letter_group_finishes` for L2/L3 have `confirmed=false`; artwork finish `confirmed=false` — partial group confirm |
| Ambiguity | **Multi-color / multi-face**: two face layers, no backing layer; warnings `roll_nesting_color_split_missing`, `missing_placement_role_metadata` |
| Blockers (backend) | None for roles/finish on persisted payload |

**Owner input:** not required for roles (already confirmed in DB). Group-level finish confirm may need owner review in UI for multi-color PBL.

---

## Pasul 4 — Material breakdown / pricing input

### Material breakdown (with dev registry pricing)

| Material key | Code | Qty | Unit |
|--------------|------|-----|------|
| plexiglas_face | MAT-ACP-FATA-LITERE | 4.482 | m² |
| face_vinyl | MAT-ORACAL-651 | 2.784 | m² |
| return_material | MAT-PROFIL-LATERAL-LITERE-60MM | 13.621 | ml |
| artwork print | MAT-VINYL-PRINT | 0.198 | m² |
| artwork laminate | MAT-VINYL-PRINT-LAMINATED | 0.198 | m² |

| Check | Result |
|-------|--------|
| Coherent with roles | Plexi + Oracal for faces; print/laminate for artwork layer; return profile ✓ |
| Forex/backing | **Absent** — no layer assigned `backing` role (expected gap for this file) |
| Warnings | `nesting_used_for_quote_not_stock`, `missing_placement_role_metadata`, `roll_nesting_color_split_missing` |
| Missing prices | **false** (with seeded registry in service test) ✓ |
| BLK-18 / pricing alignment | Pricing input `is_ready_for_quote=true`, `adapter_status=warnings`, blockers **[]** |
| Hardcoded totals | None observed |

---

## Pasul 5 — Quote / order spine

| Check | Result |
|-------|--------|
| Draft quote created | **No** |
| Linked quote | `exists=false` |
| Linked order | `exists=false` |
| UI draft quote button | **Disabled** |
| UI blocker message | *"Analiza SVG nu este salvată sau fișierul s-a schimbat — salvează din Pas 1."* |
| Root cause | Client `localFileHash` not synced with persisted `svg_source.file_hash` after reload (`hasUnsavedAnalysis`) — **false blocker despite DB persist** |
| QUOTE_NOT_PRICED | Not reached (no quote) |
| ExecutionPlan for this workspace | **No** |
| Global ExecutionPlan rows in DB | 2 (unrelated orders) |

**Commercial spine: BLOCKED** at draft-quote gate (UI hash sync bug).

---

## Pasul 6 — Production handoff / dry-run / alignment

### Handoff preview (backend from persisted payload)

| Material jobs | face_plexiglas_cutting, oracal_vinyl_cutting, return_profile_material, led_modules_install, psu_electrical |
| Active operation groups | 7 |
| Template alignment | partial — aligned 5, partial 2 |
| Partial groups | `led_electrical`, `assembly` |
| Blockers | none |

### Task dry-run

| Metric | Value |
|--------|-------|
| Task candidates | 20 |
| Provisional | `letter_assembly` only |
| `can_generate_tasks` | false |
| Blockers | `dry_run_only_no_order` (expected) |
| Alignment | partial; `blocks_real_task_generation=true` (letter_assembly provisional critical) |

### Order-bound readiness

| Metric | Value |
|--------|-------|
| `can_generate_real_tasks` | **false** ✓ |
| Blockers | `missing_client_analysis_hash`, `quote_missing`, `order_missing`, `owner_confirmation_required` |
| Alignment summary | partial; blocks real generation |

---

## ExecutionPlan / tasks_json / stock

| Check | Result |
|-------|--------|
| ExecutionPlan created for this workspace | **NO** ✓ |
| tasks_json written | **NO** ✓ |
| Real ExecutionTask | **NO** ✓ |
| Stock consumption | **NO** ✓ |

---

## Bugs found

| ID | Severity | Description |
|----|----------|-------------|
| QA-BUG-1 | **blocking commercial** | After reload, UI shows unsaved-analysis blocker on Confirm even though workspace payload is persisted with correct hash (`hasUnsavedAnalysis` / `localFileHash` not restored on hydrate) — **fix in BUILD_INTAKE_V4_ANALYSIS_HASH_HYDRATE_FIX** |
| QA-BUG-2 | **blocking quote truth** | Material breakdown inflated plexiglas (4.482 m²) and vinyl (2.784 m²) — **fixed** + read-only nesting preview added — see `BUILD_INTAKE_V4_REAL_FILE_MATERIAL_NESTING_TRUTH_AUDIT_AND_FIX` |
| QA-BUG-3 | **blocking operational truth** | Material breakdown / tasks showed Oracal/print/laminare/cant wrapped while UI had față none + cant aluminiu + artwork decizie ulterioară — **fixed in code**; **payload re-save required** on IV4-46499080 — see below |
| QA-BUG-4 | warning | Workspace ID mismatch: upload persisted on IV4-46499080, not IV4-0A33B462 (operator may have bootstrapped new workspace) |
| QA-WARN-1 | warning | PBL multi-face file: no backing layer; material breakdown omits Forex/backing |
| QA-WARN-2 | warning | Multi-color Oracal: `roll_nesting_color_split_missing` |
| QA-WARN-3 | expected | `letter_assembly` provisional in dry-run alignment |

---

## QA-BUG-2 — Suspicious material quantity / nesting truth audit

| Field | Value |
|-------|-------|
| Observed | Plexiglas față **4.482 m²** vs bbox **0.945 m²**; Vinil față **2.784 m²** |
| Root cause | `usedSheetAreaSqm` (full sheet stock) prorated to face material; roll jobs summed across alternative roll widths + artwork layer |
| Fix build | `BUILD_INTAKE_V4_REAL_FILE_MATERIAL_NESTING_TRUTH_AUDIT_AND_FIX` |
| After fix | Plexiglas **0.5834 m²**, Vinil **0.9821 m²** (placement/roll footprint) |
| Nesting preview | Collapsible panel in Review → Material Breakdown — confirms 10 face parts, active sheet only, L1 excluded |
| Retest required | Yes — reload material breakdown panel on IV4-46499080 |
| Hardcode in fix | **No** |

---

## QA-BUG-3 — Finish state truth mismatch

### 1. Setări owner reale (UI)

| Layer | Față | Cant | Artwork |
|-------|------|------|---------|
| Layer_x0020_2 | Fără finisaj — plexiglas brut | Aluminiu standard (stoc), 60 mm | — |
| Layer_x0020_3 | Fără finisaj — plexiglas brut | Aluminiu standard (stoc), 60 mm | — |
| Layer_x0020_1 | — | Aluminiu standard (stoc), 60 mm | Decizie ulterioară, policromie |

### 2. Payload persistat (IV4-46499080 @ audit)

| Field | Global | L2/L3 | L1 artwork |
|-------|--------|-------|------------|
| face_finish_type | `oracal_651` ✗ | `none` ✓ | — |
| return_finish_type | `oracal_wrapped` ✗ | `oracal_wrapped` ✗ | `standard_aluminum` ✓ |
| execution_type | — | — | `printed_vinyl_on_face` ✗ (not `needs_decision`) |

### 3. Contradicție observată

Material breakdown / preview showed: Vinil față, Cant `(oracal_wrapped)`, Print/Laminare L1, task colantare cant active — while UI per-layer showed none / aluminiu / decizie ulterioară.

### 4. Root cause

1. Material breakdown gated vinyl on **global** Oracal + roll nesting, ignoring group `none`.
2. Return label used global `oracal_wrapped`, not per-group cant.
3. Artwork print rows triggered by persisted `printed_vinyl_on_face`.
4. Partial persist: face `none` saved per group; return/artwork not aligned with UI.
5. Review panels did not refetch after finish save (`analysisIdentityKey` only).

### 5. Fix

Build `BUILD_INTAKE_V4_FINISH_STATE_TRUTH_AND_MATERIAL_TASK_SYNC_FIX` — per-layer finish truth service, breakdown gates, normalize-on-save, frontend sync + refetch.

### 6. Retest (after fix, same DB)

| Line / task | Before | After code fix |
|-------------|--------|----------------|
| Vinil față | 0.9821 m² | **absent** ✓ |
| Print/Laminare L1 | 0.198 m² | still present until payload re-save with `needs_decision` |
| return_vinyl task | active (groups `oracal_wrapped` in DB) | inactive only after re-save cant → `standard_aluminum` |

### 7. Task activation matrix (expected after re-save)

| task_key | Owner UI | After re-save |
|----------|----------|---------------|
| oracal_vinyl_cutting | inactive | inactive |
| face_finish_application | inactive | inactive |
| printed_artwork_production | inactive/blocked | inactive + `artwork_execution_pending` |
| print_lamination | inactive | inactive |
| return_vinyl_application_workbench | inactive | inactive |
| return_side_forming | active | active |
| return_face_bonding | active | active |
| led_module_install | active (illuminated) | active |
| psu_installation | active | active |

### 8. Verdict

**Code + post re-save truth: PASS scoped.**

Retestul pe IV4-46499080 a fost validat pe dev DB după re-save echivalent setărilor owner. Flow-ul real așteptat este: owner/operator apasă **Salvează finisaje** în UI, apoi hard refresh/review.

**Post re-save truth (validated):**

| Check | Result |
|-------|--------|
| Global face / return | `none` / `standard_aluminum` |
| L2/L3 | face none, cant standard_aluminum 60mm |
| L1 | `needs_decision` |
| Vinil față | absent |
| Print/Laminare L1 | absent |
| Cant label | `standard_aluminum` 60mm |
| return_vinyl task | inactive |
| return_side_forming / return_face_bonding | active |
| LED/PSU | active |
| Forex | absent, no invented material |
| artwork_execution_pending | warning intenționat |
| can_generate_real_tasks | false |
| ExecutionPlan / tasks_json / stock | none |

---

## QA-BUG-1 — Analysis hash hydration false positive

| Field | Value |
|-------|-------|
| Observed | Draft quote disabled after reload on IV4-46499080 despite persisted analysis |
| Root cause | `applyHydratedWorkspace` compared **pre-hydrate** `state.localFileHash` (null) to persisted hash |
| Fix build | `BUILD_INTAKE_V4_ANALYSIS_HASH_HYDRATE_FIX` |
| Hash source of truth | `payload.svg_source.file_hash` via `getPersistedFileHash()` |
| Retest required | Yes — reload IV4-46499080 without re-upload |
| Hardcode in fix | **No** |

---

## Automated regression (not replacing manual test)

```
test_intake_v4_quote_to_order_owner_approval.py  → 32 passed
test_tpl_volumetric_operation_keys_alignment.py   → 22 passed
test_intake_v4_task_generation_dry_run.py         → 11 passed
```

---

## Verdict

| Scope | Verdict |
|-------|---------|
| **Analyzer + nesting + child parts** | **PASS** |
| **Layer roles + finish (persisted)** | **PASS** (multi-color warnings) |
| **Material breakdown + pricing input** | **PASS after QA-BUG-2 + QA-BUG-3 fixes** (vinil față removed for face-none groups; re-save finish for full truth) |
| **Quote/order commercial spine** | **BLOCKED** — re-save finish on IV4-46499080, then retest draft quote |
| **Handoff + dry-run + alignment** | **PASS** on backend read; `can_generate_real_tasks=false` ✓ |
| **Overall build** | **BLOCKED** — finish re-save + draft quote retest on IV4-46499080 |

---

## Next recommended build

1. ~~**BUILD_INTAKE_V4_ANALYSIS_HASH_HYDRATE_FIX**~~ — applied
2. ~~**BUILD_INTAKE_V4_REAL_FILE_MATERIAL_NESTING_TRUTH_AUDIT_AND_FIX**~~ — applied
3. ~~**BUILD_INTAKE_V4_FINISH_STATE_TRUTH_AND_MATERIAL_TASK_SYNC_FIX**~~ — applied (local, uncommitted)
4. Owner: re-save finish on IV4-46499080 → retest material + dry-run → draft quote
5. Then **BUILD_INTAKE_V4_EXECUTION_TASK_WRITE_ADAPTER** (still gated)

## Owner input required

Re-save Review finish on **IV4-46499080** (cant aluminiu + artwork decizie ulterioară), hard refresh, confirm material breakdown matches UI.

---

## Addendum — letter / hole / return cant finalization (2026-06-22)

Build: **`BUILD_INTAKE_V4_LETTER_PART_HOLE_AND_RETURN_CANT_FINALIZATION`** — commit `fix(intake-v4): classify real letters and return contours` on `local/integration-pr4-plus-svg-path` (HEAD before `c356291`).

**QA-BUG-4 final rule:** Inner holes are not letters/pieces, but they require return/cant material when the volumetric part has interior return.

| Metric | IV4-46499080 (after) |
|--------|----------------------|
| `real_letters_count` | **10** |
| `artwork_piece_count` | **1** (L1 cant active) |
| `volumetric_piece_count` | **11** |
| `inner_hole_count` | **2** |
| `cutting_contours_count` | **14** |
| `outer_letter_perimeter_ml` | **11.6299** |
| `inner_hole_perimeter_ml` | **1.0951** |
| `letter_cnc_cutting_perimeter_ml` | **12.725** |
| `letter_return_perimeter_ml` | **12.725** |
| `artwork_return_perimeter_ml` | **1.8461** |
| `total_return_material_perimeter_ml` | **14.5711** |
| `led_perimeter_ml` | **11.6299** |

**Layer_x0020_1:** `execution_type=needs_decision`, `return_finish_type=standard_aluminum`, `return_depth_mm=60` — print/laminare absent; cant row **14.57 ml** aggregated.

UI hard refresh (Review step): Geometry **10 / 2 / 14 / 11.63 LED / 14.57 cant**; material breakdown cant label `Cant / return litere + interioare + artwork (standard_aluminum · 60 mm)`; task dry-run **Real letters 10 · Holes 2 · Closed contours 14 · Return 14.571 ml**.

QA doc: `docs/qa/BUILD_INTAKE_V4_LETTER_PART_HOLE_CLASSIFICATION_FIX.md`

## Commit recommendation

**Committed** — classification + return cant scope; nesting sheet role-split test failure documented as non-blocking (parallel nesting WIP).

---

## Addendum — CNC router passes & bevel costing audit (2026-06-22)

Build: **`BUILD_INTAKE_V4_CNC_ROUTER_PASSES_AND_BEVEL_COSTING_AUDIT`** (uncommitted).

| Metric | IV4-46499080 |
|--------|----------------|
| `led_perimeter_ml` | 11.6299 |
| `cnc_cutting_perimeter_ml` | **12.725** (outer + holes) |
| `return_material_perimeter_ml` | 14.5711 |
| Face CNC cost (2 passes × 1.5 EUR) | **38.175 EUR** |
| Backing Forex CNC | **absent** (no backing layer); CostEngine `back_cut` still **57.26 EUR** — gap |

QA doc: `docs/qa/BUILD_INTAKE_V4_CNC_ROUTER_PASSES_AND_BEVEL_COSTING_AUDIT.md`

---

## Addendum — Backing gate & CNC UI decision (2026-06-22)

Build: **`BUILD_INTAKE_V4_BACKING_GATE_AND_CNC_UI_DECISION`**.

| Metric | IV4-46499080 before | After backing gate |
|--------|---------------------|-------------------|
| Backing layers | 0 | 0 |
| `backing_present` | unset | **false** |
| `face_cnc_cut` | 38.175 EUR | 38.175 EUR (unchanged) |
| `back_cut` | **57.26 EUR phantom** | **0** — `gate:backing_absent` |
| Forex material breakdown | absent | absent |
| Task dry-run `cnc_back_cut` | N/A (no forex material job) | unchanged — inactive |

Synthetic confirmed-backing checks (pytest):

- No bevel: 12.725 × 3 × 1.5 = **57.2625 EUR**
- 7 mm bevel: 12.725 × 5 × 1.5 = **95.4375 EUR**

QA doc: `docs/qa/BUILD_INTAKE_V4_BACKING_GATE_AND_CNC_UI_DECISION.md`

UI gap: read-only Review backing/CNC status panel deferred to next build.

---

## Addendum — Nesting preview & material precision closure (2026-06-22)

Build: **`BUILD_INTAKE_V4_NESTING_PREVIEW_AND_MATERIAL_PRECISION_CLOSURE`**.

| Before | After |
|--------|-------|
| Plexi 4.482 m² (full sheet proration) | Footprint from active sheet placements (face roles only) |
| Vinil 2.784 m² (roll alternatives summed) | Single best roll per layer/color; artwork excluded |
| Material test expected 2.34 m² (sheet stock) | **0.56 m²** placement footprint policy |
| No nesting preview in breakdown | `nesting_preview` embedded + `GET …/nesting-preview` |
| Forex from geometry without backing confirm | Excluded when no confirmed backing layer |

IV4-46499080: Vinil/Print absent; Cant ~14.57 ml; LED/PSU active; Forex/backing absent; nesting preview read-only.

QA doc: `docs/qa/BUILD_INTAKE_V4_NESTING_PREVIEW_AND_MATERIAL_PRECISION_CLOSURE.md`
