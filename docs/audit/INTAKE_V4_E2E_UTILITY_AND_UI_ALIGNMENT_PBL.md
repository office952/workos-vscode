# AUDIT_INTAKE_V4_E2E_UTILITY_AND_UI_ALIGNMENT_PBL

**Date:** 2026-06-23  
**Branch:** `local/integration-pr4-plus-svg-path` @ `6c4f67d`  
**Verdict:** **PARTIAL PASS backend truth / FAIL Confirm Summary utility** — canonical metrics exist in API and Review panels, but Confirm Summary is too generic and mislabels key areas; quote handoff UI over-promises vs backend guards.

**Workspace audited:** `IV4-4B172FD4` (`0f300dcf-0b77-4fc1-affd-6e2a20329804`)  
**URL:** http://localhost:3000/intake-v4-app/0f300dcf-0b77-4fc1-affd-6e2a20329804/operator  
**SVG:** `pbl-layere.svg` (persisted on workspace)

---

## 1. Canonical backend values (API)

| Signal | Canonical value | Source |
|--------|-----------------|--------|
| `layers_count` | 3 | `layer_role_setup.layers` |
| `parts.count` | 11 | `svg_analysis_json.parts` |
| `real_letters_count` | 10 | `quote_geometry` |
| `artwork_piece_count` | 1 | `quote_geometry` |
| `inner_holes_count` | 5 | `quote_geometry` / parts `innerContourCount` sum |
| `volumetric_piece_count` | 11 | `quote_geometry` |
| `nestable_parts` | 10 | nesting `summary` |
| `artwork_parts` | 1 | nesting `summary` |
| `active_sheet_layouts` | 1 | nesting `summary` |
| `plexiglas_face` | **0.5834 m²** | material-breakdown `plexiglas_face` |
| `return_material` | **15.4672 ml** | material-breakdown (workspace instance; golden PBL ≈15.444) |
| `face_area_m2` (quote geom) | **0.6907 m²** | `quote_geometry` — layer gross face area |
| `artwork_area_m2` | 0.1976 m² | `quote_geometry` |
| `letter_perimeter_m` / LED | **11.6299 m** | outer letter perimeter |
| `cutting_perimeter_ml` / CNC | **13.6211 m** | outer + hole perimeter |
| `hole_perimeter_ml` | 1.9912 m | inner holes |
| `return_material_perimeter_ml` | 15.4672 m | letters + holes + artwork return |
| `led_modules` | 47 | material-breakdown |
| `led_module_power_w` | 1.44 (last saved) | `finish_setup` |
| `estimated_led_watts` | 67.68 @ 1.44W | `finish_setup` |
| `required_psu_watts` | 87.98 | `finish_setup` |
| `psu_configuration` | [100] | `finish_setup` |
| Vinyl / print / laminate / backing | absent | material keys |
| Artwork execution | `needs_decision` | `artwork_finishes[0]` |
| `readiness_status` | `ready_for_quote_preview` | workspace |
| `pricing is_ready_for_quote` | **true** | pricing-input-preview |
| Quote handoff blockers (backend) | `artwork_execution_undecided:Layer_x0020_1` | `evaluate_v4_quote_handoff_blockers` |
| ProductSystem binding blockers | **[]** | product-system-binding |
| Task dry-run | `dry_run_only=true`, no stock/tasks | task-generation-dry-run |
| Nesting boundary | `preview_only=true`, `consumes_stock=false` | nesting-preview |

### Wattage matrix (backend, PBL perimeter)

| Module W | Consum LED | PSU 30% | PSU config |
|----------|------------|---------|------------|
| 1.44 | 67.68 W | 87.98 W | 100 W |
| 1.00 | 47.00 W | 61.10 W | 100 W |
| 0.75 | 35.25 W | 45.83 W | 60 W |

---

## 2. Signal × UI alignment table

| Signal | Backend | UI visible? | Where | Problem? |
|--------|---------|-------------|-------|----------|
| layers_count=3 | ✓ | ✓ | Layers summary, Confirm | **Ambiguous** — reads as 3 pieces |
| parts.count=11 | ✓ | ✗ | — | **Missing** in Layers/Confirm |
| real_letters=10 | ✓ | ✓ | Review GeometryPanel | Not on Confirm |
| artwork=1 | ✓ | partial | GeometryPanel volumetric | Not on Confirm |
| inner_holes=5 | ✓ | ✓ | Review GeometryPanel | Not on Confirm |
| plexiglas 0.5834 m² | ✓ | ✓ | Material breakdown | Not on Confirm |
| face_area 0.6907 m² | ✓ | ✓ | GeometryPanel, Pricing input, **Confirm** | **Mislabeled as quote face on Confirm** |
| return 15.47 ml | ✓ | ✓ | GeometryPanel, breakdown | Not on Confirm |
| CNC 13.62 m | ✓ | ✓ | Review GeometryPanel | Not on Confirm |
| LED 47 + wattage | ✓ | ✓ | Review lighting block, breakdown | Confirm shows only "LED" |
| needs_decision L1 | ✓ | ✓ | Breakdown warning, pricing warning | **Not on Confirm Summary** |
| draft quote eligible | blocked | partial | Confirm handoff | **UI gate ≠ backend gate** |
| dry-run only | ✓ | ✓ | Task dry-run panels (Review) | Not on Confirm |

---

## 3. Why Confirm shows `A 0.691 m²`

**Root cause (not a math bug):** Confirm Summary uses `readQuoteGeometryFromPayload().face_area_m2`, which comes from `quote_geometry.face_area_m2` — the **sum of nest2 layer filled/bounding areas** for face-role layers (`Layer_x0020_2` + `Layer_x0020_3`). That is gross layer footprint (~0.691 m²).

**Material breakdown plexiglas 0.5834 m²** comes from **active nesting sheet layout** prorated to nestable letter parts (net quote estimate).

**Alignment gap:** Confirm label "Geometrie quote · A … m²" implies a single offer face area, but shows the **layer-area proxy**, not the **nesting quote quantity**. Operator can believe quote uses 0.691 m² while material breakdown correctly uses 0.5834 m².

---

## 4. Task findings (summary)

### A — Layers
- Layer roles table is clear (L1 artwork, L2/L3 face).
- **Gap:** No `parts.count=11`, no child-part vs layer explanation, no inner holes count on this step.
- Reupload/unsaved analysis banner exists via SmartBanner.

### B — Review / Finish
- Per-layer finish sections + global lighting block are strong.
- Artwork `needs_decision` visible in artwork finish section.
- **Gap:** Global summary line "Față / cant: none / standard_aluminum" loses per-layer context (L1 artwork vs L2/L3 letters).

### C — Lighting
- Selector 0.75 / 1.00 / 1.44 W visible on Review; preview recalculates; persists after save (API confirmed `led_module_count=47`, wattage fields).
- **Gap:** Confirm Summary does not show wattage, module count, PSU.

### D — Material breakdown
- Plexiglas, return, LED modules (with W/buc), led_total_watts, PSU visible.
- Explicit disclaimer: nesting for quote estimate, not stock.
- Warnings include `artwork_execution_pending`, `nesting_used_for_quote_not_stock`.
- **Gap:** Warnings not surfaced on Confirm; no side-by-side "layer area vs nesting area".

### E — Nesting
- Collapsible panel; boundary flags correct (`preview_only`, no stock).
- **Gap:** Operator must expand; active vs alternative layouts not obvious at a glance on Confirm.

### F — Confirm Summary (critical)
Current (`IntakeV4ConfirmStep.tsx`):

```text
Layers: 3
Față / cant: none / standard_aluminum
Geometrie quote: P 11.63 m · A 0.691 m² · 10 piese
Cant depth / LED: 60 mm · LED
```

**Missing vs operational truth:** child parts 11, artwork 1, holes 5, plexiglas nesting area, CNC/return perimeters, LED module count/wattage/PSU, artwork blocker, dry-run boundaries, explicit "draft blocked until L1 decided".

### G — Quote handoff
- Checkboxes are **real backend guards** on `create-draft-quote` (`confirm_no_order`, etc.).
- **Policy gap:** UI enables handoff when `ProductSystem binding.blockers` empty + readiness + checkboxes — but backend **`evaluate_v4_quote_handoff_blockers`** also requires no `artwork_execution_undecided` and valid `client_analysis_hash`.
- `is_ready_for_quote=true` in pricing preview **does not** include artwork execution blocker → operator sees green adapter status while draft creation would 422.
- Button **creates real draft quote** (not just navigate) then opens QuoteWizard.

---

## 5. Utility scores (1–5)

| Dimension | Score | Rationale |
|-----------|-------|-----------|
| Claritate geometrie | **3** | Review GeometryPanel good; Layers/Confirm omit parts/holes |
| Claritate materiale | **3** | Breakdown strong on Review; Confirm silent |
| Claritate iluminare | **4** | Review lighting block post-6c4f67d; Confirm only "LED" |
| Claritate nesting | **3** | Data correct; UX buried in collapsible Review panel |
| Claritate warnings/blockers | **2** | Warnings scattered; Confirm hides artwork blocker |
| Claritate quote handoff | **2** | Checkboxes honest; gate mismatch vs backend |
| Încredere generală ofertare | **2.5** | Backend truth exists; Confirm undermines trust |

**Can a real operator decide a quote from this UI?**  
**Partially on Review**, **not safely on Confirm alone** — must scroll Review panels and still may attempt draft quote while L1 undecided.

---

## 6. Prioritized fix plan (no implementation)

### Must fix before quote policy

| # | Title | Why | Likely files | Risk | Tests |
|---|-------|-----|--------------|------|-------|
| M1 | Confirm Summary operational truth | Operator decision point is wrong | `IntakeV4ConfirmStep.tsx`, shared summary component | Low | Component test + e2e confirm |
| M2 | Area label split: layer gross vs nesting quote | 0.691 vs 0.5834 confusion | `IntakeV4ConfirmStep`, `IntakeV4GeometryPanel`, `IntakeV4PricingInputPanel` | Med | Assert both values labeled |
| M3 | Show child parts / holes / artwork on Confirm | 3 layers ≠ 3 pieces | Confirm summary | Low | PBL fixture |
| M4 | Quote handoff gate = backend blockers | Prevent false enable | `IntakeV4ConfirmStep`, API expose handoff preview blockers | Med | Test artwork needs_decision blocks button |
| M5 | Artwork needs_decision on Confirm | Critical blocker invisible | Confirm + readiness | Low | Handoff blocker test |
| M6 | LED summary on Confirm | wattage/modules/PSU | Confirm summary | Low | Lighting regression |

### Should fix before production

| # | Title | Why | Likely files |
|---|-------|-----|--------------|
| S1 | Layers step: parts.count + holes hint | Early geometry education | `IntakeV4SvgAnalyzerStep` |
| S2 | Align pricing `is_ready_for_quote` with handoff blockers | Green when still blocked | `intake_v4_pricing_input_service`, UI badges |
| S3 | Task dry-run → operator groups | Production readability | dry-run panels |
| S4 | Nesting active layout badge on Confirm | Quick layout truth | Confirm + nesting summary |

### Later polish

- Human labels for `none` / `standard_aluminum` on Confirm (use same helpers as Review).
- Visual hierarchy: warnings sticky on Confirm.
- Per-layer finish rollup line instead of global only.

---

## 7. Recommended next build

```text
BUILD_INTAKE_V4_CONFIRM_SUMMARY_AND_HANDOFF_ALIGNMENT
```

Scope: M1–M6 above; no quote policy/CostEngine changes; reuse canonical `quote_geometry` + material breakdown + handoff blockers API.

---

## 8. Boundaries confirmed (audit session)

- No code implementation
- No commit / push
- No quote/order/tasks created
- No stock consumption
