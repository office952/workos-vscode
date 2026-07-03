# AUDIT FINAL — Intake V4 Review Form (Volumetric Letters)

**Date:** 2026-06-24  
**Branch:** `local/integration-pr4-plus-svg-path`  
**HEAD:** `e719846` — fix(intake-v4): show full vector perimeter in summary  
**Stack:** backend :8000, frontend :3000  
**Scope:** Audit only — no backend/ProductSystem/CostEngine changes, no commits.

**Synthesizes:** `AUDIT_INTAKE_V4_REVIEW_FORM_FUNCTIONAL_IMPACT.md`, `AUDIT_INTAKE_V4_AREA_USAGE_AND_REMOVAL_PLAN.md`, UI simplification builds, cant/footprint/live-calc work on branch.

---

## Executive summary

The Intake V4 Review form for **TPL-VOLUMETRIC-LETTERS** is **operator-usable for finish capture and geometry review** after recent UI simplification (perimeter-first cards, sticky Calcul live, modular sections). It is **not final** for commercial truth or production handoff.

**Core gap (P0):** Almost all pricing/breakdown/task surfaces read **persisted workspace payload** only. Dropdown changes update local state but **Calcul live**, material breakdown, task preview, and dry-runs **do not reflect edits until „Salvează draft”**. `finishIdentityKey` includes local state → **refetch storms** with identical stale responses.

**Numeric split (Ana Maria / PBL):** Operator cant perimeter **31.64 m** (26.75 letters + 4.89 emblem) is correct in UI via `resolveIntakeV4OperatorCantPerimeterDisplay`. Backend breakdown cant qty still uses **quote_geometry ~20.97 m** (+20% → **25.17 m** priced). LED uses **~20.97 m** exterior — by design, not full vector.

**Pricing:** Oracal 641/651/8500 face vinyl uses **owner series prices** (not per-color). Dev registry often **missing** for profil cant, Forex spate, print/laminat → „tarif lipsă” despite quantities. Calcul live **omits LED consumables** from EUR buckets; Oracal hint matches `"651"` only → **8500/641** may not appear in Oracal line after save.

**Task preview:** `v3_operation_catalog` adapter — **not** ProductSystem dossier. Per-layer finish ignored when `letter_group_finishes` exist.

**Area policy:** Main UI largely perimeter-first ✓; footprint candidate pickers and area-variant summaries remain in technical accordion (removal plan documented).

**Verdict:** **~70% toward operator-final UI**; **~40% toward pricing/production-final**. Phase A (frontend save/preview UX) + Phase B (backend preview endpoint) required before calling form „final.”

---

## 1. Git state

| Item | Value |
|------|-------|
| Branch | `local/integration-pr4-plus-svg-path` |
| HEAD | `e719846` |
| Tracked M | Intake V4 frontend/backend footprint, cant, geometry, breakdown, review step |
| Untracked QA | This doc + prior audit docs under `docs/qa/` |

No commit performed in this audit.

---

## 2. Audit boundary

| In scope | Out of scope (this audit) |
|----------|---------------------------|
| Review form controls, display libs, read-only backend trace | Backend/CostEngine/ProductSystem **changes** |
| Frontend test subset | `tmp/`, `test-results/` deliverables |
| Pricing registry **read** gaps | Seeding registry in dev DB |
| UI removal recommendations | Implementation of fixes |

---

## 3. Verdict — closeness to „final”

| Dimension | Score | Notes |
|-----------|-------|-------|
| Operator UI layout | **High** | Cards ordered per owner spec; debug moved to accordion |
| Finish capture | **High** | Per-layer face/cant, emblem translucency, LED, backing |
| Live cost feedback | **Low** | Stale until save; LED cost missing in Calcul live |
| Material qty truth | **Medium** | Post-save breakdown OK; cant perimeter UI ≠ breakdown qty |
| Commercial quote truth | **Low** | Breakdown explicitly not CostEngine final; footprint not applied to quote |
| Production tasks | **Low** | V3 catalog preview; no ProductSystem contract |

**Critical blockers:** P0 save-before-preview, P1 task preview per-layer, P1 emblem cant UI, P1 LED/Oracal aggregations.  
**Phase 2:** Backend cant alignment, registry seeds, preview API.  
**Polish:** Area variant UI removal, spec-only color messaging, pending-save banner.

---

## 4. State flow (rupture)

```
UI input → local state (form | letterGroups | artworkFinishes)
         → [MISSING until save] → workspace.payload persistat
         → GET material-breakdown / task-preview / pricing-input / dry-runs
         → Calcul live + Materiale folosite + accordion
```

**Local exceptions (no save):** LED module/watt/PSU recalc (`syncIntakeV4FinishLighting`); cant perimeter in Materiale folosite (`operatorCantPerimeterM`); CNC shanfren toggle → `cost-draft` refetch; task preview query params only when **zero** letter groups.

---

## 5. Functional — face finishes (1.1)

| Option | UI | Save | Breakdown | Calcul live | Notes |
|--------|----|------|-----------|-------------|-------|
| `none` | ✓ | ✓ | Plexi only | Plexi cost if priced | No `face_vinyl_*` row |
| `oracal_651` | ✓ | ✓ | `face_vinyl_651` | Partial — hint `"651"` | Owner 9 EUR/m² |
| `oracal_8500` | ✓ | ✓ | `face_vinyl_8500` | **Often missing** in Oracal EUR line | Owner 20 EUR/m² |
| `oracal_641` | ✓ | ✓ | `face_vinyl_641` | Partial | Owner 6.5 EUR/m² |
| `print_laminate` (letters) | ✓ | ✓ | If backend generates | Print row — often tarif lipsă | Registry gap |

**Verdict:** Functional **after save**; before save = UI only for costs.

---

## 6. Functional — Oracal color (1.2)

| Aspect | Behavior |
|--------|----------|
| UI | `ColorRegistrySelect` per group; nearest 651 from SVG fill (`intakeV4NearestOracalColor`) |
| Save | `face_oracal_code`, `face_oracal_name` on `letter_group_finishes` |
| Breakdown material code | Same `face_vinyl_{series}` regardless of color |
| Price | **Series** (641/651/8500), not color code |
| UX gap | No „spec-only, price on series” message |

---

## 7. Functional — cant (1.3)

| Aspect | Source |
|--------|--------|
| UI per layer | `IntakeV4ReturnCantFields` in letter groups + copy-to-all |
| Operator perimeter | `resolveIntakeV4OperatorCantPerimeterDisplay` — vector sum |
| Breakdown qty | `quote_geometry.return_material_perimeter_ml` (~20.97 m Ana Maria) |
| Priced cant | base × 1.20 waste → ~25.17 m |
| Cost | `MAT-PROFIL-LATERAL-LITERE-{depth}MM` — often **missing** in dev |
| Main card | Perimetru, finisaj, adâncime, preț/tarif lipsă |
| Technical accordion | LED exterior, breakdown cant, Oracal impact m² |

---

## 8. Functional — emblem / policromie (1.4)

| Aspect | State |
|--------|-------|
| UI | `IntakeV4ArtworkFinishSection` — hardcoded Print+laminare, Policromie |
| Translucent / Transparent | Sets `print_transparency` + forces execution/color mode |
| Cant emblemă | **No UI** — `return_finish_type` not editable for artwork |
| Missing layer flow | Analyzer derives artwork rows; no operator „add layer” |
| Cost | Print rows after save if execution valid; translucency = spec only |

---

## 9. Functional — old artwork blocks (1.5)

| Component | Location | Recommendation |
|-----------|----------|----------------|
| `IntakeV4ArtworkComplexityCard` | Technical accordion | **Keep** for owner override; not main UI |
| Accept/override recommendations | Removed from main | ✓ Correct |
| `IntakeV4ArtworkFinishSection` | Main | Simplified — OK |

**Recommendation:** Do not re-promote complexity card to main; optional Phase 2 hide entirely for operators.

---

## 10. Functional — LED (1.6)

| Control | Local immediate | Breakdown after save |
|---------|-----------------|----------------------|
| LED on/off | ✓ gates seeds | ✓ |
| System / color / wattage | ✓ | metadata |
| Module count | ✓ recalc | `led_modules` qty |
| Perimeter display | `ledExteriorPerimeterM` (~20.97 m) | `geometry_perimeter` |
| Calcul live EUR | **No** — consumables not summed | — |
| Materiale folosite | LED row from breakdown | ✓ |

---

## 11. Functional — CNC face/back (1.7)

| Aspect | Behavior |
|--------|----------|
| Shanfren Forex | `useIntakeV4FaceBackPrepCostDraft` — refetch on toggle |
| Summary card | Technical accordion (`IntakeV4FaceBackPrepCostDraftSummaryCard`) |
| `manual_required` | Hides total / shows „verificare perimetru” |
| Operation rows | Separate from material breakdown |

---

## 12. Functional — upload placeholder (1.8)

`IntakeV4ProjectFilesPlaceholder` — **100% placeholder**. No persistence, no material/task impact.

---

## 13. Pricing table — materials & registry

| Material | Breakdown key | Registry / price source | Dev typical | Qty after save |
|----------|---------------|-------------------------|-------------|----------------|
| Plexi față | `plexiglas_face` | `MAT-ACP-FATA-LITERE` | pricing_registry or missing | ✓ m² |
| Forex spate | `forex_backing` | `MAT-SPATE-PVC-LITERE` | **missing** | ✓ if backing |
| Oracal 651 față | `face_vinyl_651` | owner `intake_v4_owner_oracal_651` | 9 EUR/m² | ✓ |
| Oracal 8500 | `face_vinyl_8500` | owner catalog | 20 EUR/m² | ✓ |
| Oracal 641 | `face_vinyl_641` | owner catalog | 6.5 EUR/m² | ✓ |
| Print vinyl | `*_print_vinyl` | `MAT-VINYL-PRINT` | missing | ✓ |
| Laminare | `*_laminated_vinyl` | `MAT-VINYL-PRINT-LAMINATED` | missing | ✓ |
| Cant profil | `return_material` | `MAT-PROFIL-LATERAL-LITERE-{depth}MM` | **missing** | ✓ m (+ waste) |
| Oracal cant wrap | `edge_cant_oracal_651` | owner 651 area | partial | if wrapped |
| Adeziv cant | consumable | owner consumable | partial | ✓ |
| Module LED | `led_modules` | `MAT-LED-MODULE` | missing | ✓ buc |
| PSU | `led_psu` | dynamic code | variable | rare |

**Service:** `intake_v4_oracal_face_pricing_service.py` — series split, not color.  
**Service:** `intake_v4_material_breakdown_service.py` — `MATERIAL_REGISTRY_CODES`, `_apply_registry_prices`.

---

## 14. Numeric coherence — Ana Maria perimeters

| Value (m) | Meaning | Used for |
|-----------|---------|----------|
| **31.638** | Full vector (letters + emblem w/ cant) | Geometry summary full vector |
| **26.747** | Letter groups vector sum | Operator cant letters component |
| **4.891** | Emblem vector (cant active) | Operator cant emblem component |
| **31.64** | Operator cant total (UI) | Cant card, Materiale folosite cant |
| **20.97** | LED exterior / quote geometry return | LED perimeter, breakdown cant base |
| **25.17** | 20.97 × 1.20 waste | Breakdown priced cant qty |

**By design:** LED ≠ full vector (outer parts only).  
**Gap:** Breakdown cant qty should eventually align to operator vector total (backend build).

---

## 15. Owner logic rules (stated / builds)

1. **Perimeter-first operator UI** — dimensions + vector/cant/LED perimeters; not area variants on main surface.
2. **Cant / volum** labeling — not „return”; default white Oracal 651 policy for cant.
3. **Oracal face price on series** — 641/651/8500 owner EUR/m²; color = production spec.
4. **Print + laminare** — one physical coverage (dedupe in Materiale folosite); paired rows in breakdown for cost.
5. **LED emblem** — `ceil(outbox_area_m2 × 60)` modules when area_lit.
6. **Footprint override** — raises Plexi/Forex only; not Oracal/print; `is_applied_to_quote: false`.
7. **Breakdown ≠ final quote** — informative internal; CostEngine separate.
8. **Tasks from ProductSystem** — strategic; not form/catalog V3 long-term.
9. **Save finish_setup** — required for analysis-bundle truth and material rows.
10. **Fail-closed pricing** — `price_source=missing` not silent defaults.

---

## 16. Calcul live

| Question | Answer |
|----------|--------|
| Source | `GET material-breakdown` + `face-back-prep cost-draft` |
| Local cost? | **No** (except CNC draft on shanfren) |
| Before save? | Stale costs |
| Cant EUR | From breakdown — tarif lipsă if registry missing |
| LED EUR | **Not aggregated** |
| Oracal EUR | `sumMaterialByHint(..., ["oracal","651"])` — 8500/641 gap |
| Status line | „Status lipsă tarife” when `contains_missing_prices` |

---

## 17. Materiale folosite

- Source: breakdown + `operatorCantPerimeterM` for cant (m not priced waste).
- Print+laminare: `sumPrintLaminateCoverage` — max per artwork, label „acoperire”.
- Mobile: collapsible toggle.
- Oracal aggregated by series label.

---

## 18. Footprint source selector

**Component:** `IntakeV4SheetFootprintOverridePanel` (technical accordion).

| Source | Plexi/Forex | Oracal |
|--------|-------------|--------|
| `eligible_area_floor` | ✓ | no |
| `face_union_bbox` | ✓ | no |
| `layout_occupied_area` | ✓ | no |
| `operator_manual_footprint` | ✓ | no |

Updates after save + refetch. **Area removal plan:** hide candidate m² from operator path (Phase 2).

---

## 19. Print + laminare dedupe

**Fixed** in `intakeV4LiveMaterialsUsedDisplay.ts` — tests 8/8 PASS. Backend still emits paired rows (correct for separate cost lines).

---

## 20. Area UI removal status

See `AUDIT_INTAKE_V4_AREA_USAGE_AND_REMOVAL_PLAN.md`. Main cards: **no m²** ✓. Residual: footprint panel, sheet quote selected area, geometry advanced, cant Oracal impact m², LED outbox m² in technical.

---

## 21. Modularity — `IntakeV4ReviewStep.tsx`

| Aspect | Assessment |
|--------|------------|
| Size | ~1040 lines — **orchestrator heavy** |
| State | form, letterGroups, artworkFinishes, 10+ preview states |
| Fetch effects | 8+ useEffects keyed on `finishIdentityKey` |
| Strength | Clear section composition |
| Risk | Identity key triggers redundant API calls |
| Recommendation | Split: `useIntakeV4ReviewPreviews`, `useIntakeV4ReviewFinishState` |

---

## 22. Modularity — display / lib layer

| Module | Role | Quality |
|--------|------|---------|
| `intakeV4GeometryMetricDisplay.ts` | Perimeter metrics + operator cant resolver | **Good** — tested |
| `intakeV4EdgeCantDisplay.ts` | Cant view model | **Good** — separated from UI |
| `intakeV4LiveMaterialsUsedDisplay.ts` | Materiale folosite aggregation | **Good** — tested |
| `intakeV4FinishPayloadSync.ts` | Identity key + layer→global sync | **Partial** — key too broad |
| `intakeV4FinishHydration.ts` | Pending save detection | **Incomplete** — ignores letterGroups |
| `intakeV4NearestOracalColor.ts` | Default color | **Good** — isolated |
| `useIntakeV4FaceBackPrepCostDraft.ts` | CNC draft hook | **Good** — small |

---

## 23. Modularity — backend (read-only)

| Service | Boundary |
|---------|----------|
| `intake_v4_material_breakdown_service.py` | Material qty + registry prices — **not** CostEngine |
| `intake_v4_oracal_face_pricing_service.py` | Owner Oracal series |
| `intake_v4_production_preview_service.py` | V3 catalog adapter |
| `intake_v4_sheet_footprint_override_service.py` | Plexi/Forex raise |
| `intake_v4_nesting_material_precision.py` | Area/nesting internals |

Clear service split; preview engine not ProductSystem.

---

## 24. UI/UX — remove from main operator surface

**P0 (owner list):** Footprint radio+m² list; sheet quote „arie selectată”; geometry face/artwork m²; artwork complexity area.  
**P1:** Cant Oracal impact panel; pricing input face m²; nesting area columns.  
**Keep:** Dimensions, perimeters, material m² quantities in breakdown/Materiale folosite, Calcul live EUR.

---

## 25. Task preview / ProductSystem boundary

| Aspect | Current |
|--------|---------|
| Engine | `build_v4_task_preview_response` → V3 `build_task_seed_candidates` |
| ProductSystem | Binding count shown; **not** dossier-driven tasks |
| Per-layer finish | Ignored when `letter_group_finishes.length > 0` |
| Banner | `INTAKE_V4_PREVIEW_ONLY_BANNER` in technical accordion |
| Change effect | **After save** only |

**Target:** Template dossier operations from `TPL-VOLUMETRIC-LETTERS` — separate ProductSystem build.

---

## 26. Confirmed issues (P0–P2)

| ID | Sev | Issue |
|----|-----|-------|
| P0-1 | Critical UX | Calcul live stale before save |
| P0-2 | Critical UX | Refetch on `finishIdentityKey` — wasted work, same payload |
| P1-1 | High | Task preview no per-layer draft |
| P1-2 | High | Emblem cant UI missing |
| P1-3 | High | Calcul live excludes LED consumable cost |
| P1-4 | High | Oracal EUR hint 651-only |
| P1-5 | High | Cant breakdown qty ≠ operator vector perimeter |
| P2-1 | Medium | Oracal color spec-only not communicated |
| P2-2 | Medium | `isIntakeV4SelectorStatePendingSave` incomplete |
| P2-3 | Medium | Print/laminat registry missing in dev |
| P2-4 | Medium | Area variant UI still in technical accordion |

---

## 27. Tests run (2026-06-24)

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run \
  src/components/workos/intake-v4/IntakeV4LiveCalculationSummary.test.tsx \
  src/components/workos/intake-v4/IntakeV4EdgeCantReviewCard.test.tsx \
  src/lib/intakeV4/intakeV4GeometryMetricDisplay.test.ts \
  src/components/workos/intake-v4/IntakeV4OperatorGeometrySummaryCard.test.tsx \
  src/components/workos/intake-v4/IntakeV4FaceBackPrepCostDraftPanel.test.tsx \
  src/components/workos/intake-v4/IntakeV4LetterGroupFinishesSection.test.tsx \
  src/components/workos/intake-v4/IntakeV4ArtworkFinishSection.test.tsx \
  src/lib/intakeV4/intakeV4NearestOracalColor.test.ts \
  src/components/workos/intake-v4/IntakeV4MaterialBreakdownPanel.test.tsx \
  src/lib/intakeV4/intakeV4LedLighting.test.ts \
  src/lib/intakeV4/intakeV4LiveMaterialsUsedDisplay.test.ts \
  src/components/workos/intake-v4/IntakeV4SheetFootprintOverridePanel.test.tsx \
  src/lib/intakeV4/intakeV4SheetFootprintSource.test.ts
```

**Result:** 13 files, **57/57 PASS**.

**No dedicated `IntakeV4ReviewStep` test** — coverage via section tests.

---

## 28. Manual smoke checklist

1. Seed/open Ana Maria PBL workspace on Review step.
2. Verify geometry card: L/H mm, vector perimeter, **no** face area m².
3. Change face finish 651→8500 on a letter group — Calcul live **unchanged** until save.
4. Save draft — Oracal m²/cost updates in breakdown; check Oracal EUR line for 8500.
5. Cant card shows **~31.64 m** (or fixture values); accordion shows **~20.97 m** breakdown.
6. Toggle LED off — module count local; save — LED row disappears from preview.
7. Emblem translucent checkbox — save — print rows appear if complexity allows.
8. Footprint source change — save — Plexi m² changes in Materiale folosite.
9. Shanfren toggle — CNC draft refetches without full save.
10. Task preview list — changes only after save; note V3 banner.
11. Confirm step — align perimeter-first (optional regression).

**E2E:** `npm run test:e2e:workintake-finish` with `PW_SKIP_WEB_SERVER=1` when stack live.

---

## 29. Phasing A–E

### Phase A — Frontend UX (no backend)

1. Banner: „Previzualizare costuri după Salvează draft” when local ≠ persisted.
2. Stop breakdown refetch on local `finishIdentityKey`; refetch on `updated_at` post-save only.
3. Extend pending-save detection to `letterGroups` / `artworkFinishes`.
4. Calcul live: sum `consumable_rows` (LED); broaden Oracal hint to 641/8500.
5. Emblem cant fields (reuse `IntakeV4ReturnCantFields`).
6. Area UI P0 removals from removal plan.

### Phase B — Backend preview (confirm scope)

1. `GET material-breakdown?draft=1` or POST preview body.
2. Task preview with `letter_group_finishes` override.
3. Align `return_material` qty to operator vector perimeter policy.
4. Dev registry seeds for profil, Forex, print.

### Phase C — ProductSystem tasks

1. Task preview from template dossier.
2. Finish → material intent unified contract.

### Phase D — Commercial quote

1. Footprint `is_applied_to_quote` decision.
2. Quote handoff readiness gates.

### Phase E — Polish

1. Spec-only color messaging.
2. ReviewStep hook split.
3. Confirm step alignment.
4. Remove artwork complexity from operator path if owner approves.

---

## 30. Key file index

| Role | Path |
|------|------|
| Review orchestrator | `frontend/.../steps/IntakeV4ReviewStep.tsx` |
| Calcul live | `frontend/.../IntakeV4LiveCalculationSummary.tsx` |
| Materiale folosite | `frontend/.../intakeV4LiveMaterialsUsedDisplay.ts` |
| Cant display | `frontend/.../intakeV4EdgeCantDisplay.ts` |
| Geometry metrics | `frontend/.../intakeV4GeometryMetricDisplay.ts` |
| Breakdown API | `backend/.../intake_v4_material_breakdown_service.py` |
| Oracal pricing | `backend/.../intake_v4_oracal_face_pricing_service.py` |
| Task preview | `backend/.../intake_v4_production_preview_service.py` |
| Pending save | `frontend/.../intakeV4FinishHydration.ts` |

---

## 31. Secondary docs

| Doc | Purpose |
|-----|---------|
| `AUDIT_INTAKE_V4_REVIEW_FORM_FUNCTIONAL_IMPACT.md` | Control-by-control functional trace |
| `AUDIT_INTAKE_V4_AREA_USAGE_AND_REMOVAL_PLAN.md` | Area classification A–E + removal phases |
| `BUILD_INTAKE_V4_UI_SIMPLIFICATION_FINAL_OPERATOR_REVIEW.md` | Owner UI order spec |
| `BUILD_INTAKE_V4_CANT_PERIMETER_COST_SIMPLE_UI.md` | Cant UI cleanup |

---

## Boundary (this audit)

- No code changes except this documentation.
- No backend/ProductSystem/CostEngine modifications.
- Tests run read-only verification only.
