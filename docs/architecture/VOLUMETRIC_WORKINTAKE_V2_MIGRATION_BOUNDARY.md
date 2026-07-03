# TPL-VOLUMETRIC-LETTERS — WorkIntake V2 Migration Boundary (Architecture Lock)

**Status:** LOCKED (documentation + guard comments)  
**Date:** 2026-06-08  
**HEAD reference:** `2935f47` (+ uncommitted hotfix/alignment work in working tree)

---

## 1. Decision summary

For **TPL-VOLUMETRIC-LETTERS**:

| Flow | Status |
|------|--------|
| **WorkIntake V2** (`/intake-v2/:id`) | **ACTIVE** — primary operator path for new work |
| **Classic intake** (`/intake/:id` modular workspace + legacy editor) | **LEGACY** — compatibility only |
| **QuoteWizard / VolumetricLettersQuoteFlow** | **LEGACY** — quote simulation handoff from saved spec |
| **`product_spec_json`** | **CANONICAL** — single persisted contract |
| **CostEngine / quote_input** | **COSTING_HANDOFF** — derived from canonical spec; change only in dedicated builds |

**Operator path of record:** V2 stages 1–7 → **Deschide QuoteWizard** → `/quotes` standalone wizard (`embedded=false`).

---

## 2. Why classic is frozen

Dual maintenance caused regressions:

- RAL/paint gating fixed in frontend readiness but CostEngine still evaluated paint lines without applicability.
- V2 geometry/PSU saved in live spec while classic QuoteWizard read stale `productSpecInitial` on handoff.
- Depth aliases (`return_depth_mm` / `depth_mm`) duplicated across classic UI, flowState, and spec.
- PSU: V2 `psu_configuration[]` vs classic `selected_psu_watts` with no single handoff rule.
- Multiple readiness layers (`intakeReadinessStages`, `buildIntakeReadinessStages`, CostEngine `quote_gate`, V2 repair panel) contradicted each other.

**Rule:** New product/business rules go to **V2 + canonical spec + explicit costing handoff builds**. Classic paths receive **critical regression fixes only**.

---

## 3. Active V2 flow

```
/intake-v2/:id
  └── WorkIntakeV2.tsx
        └── WorkIntakeV2Flow.tsx
              ├── V2ContextStage        — template confirm
              ├── V2SvgStage            — SVG upload/parse
              ├── V2LayersGeometryStage — layer + geometry metrics
              ├── V2ProductionStage     — cant, depth, vinyl rules
              ├── V2LightingStage       — LED + PSU planning
              ├── V2VerificationStage   — checklist
              └── V2QuoteStage          — handoff summary → QuoteWizard
```

**Persistence:** `onSaveProductSpec` → `intakesApi.update(product_spec_json)` (skipRefresh during stages; refresh on handoff).

**Handoff:** `handleOpenQuoteWizardHandoff` → normalize spec → save → navigate `/quotes` with **live spec** (not stale API snapshot).

**Libs:** `frontend/src/lib/workIntakeV2/*` (stageCompletion, geometrySync, lightingPlanning, psuAllocation, repairPanel).

---

## 4. Classic flow map (legacy)

| Entry | Route / component | Role | Source of truth today |
|-------|-------------------|------|------------------------|
| Modular intake shell | `/intake/:id` → `TemplateWorkspaceRouter` → `VolumetricLettersWorkspace` | Tab **Specificație** + **Simulare ofertă** | `product_spec_json` via `ProductSpecEditorSlot` |
| Legacy editor block | `IntakeDetail` → `Product001IntakeSpecEditor` | Full classic form (parallel to workspace) | `product_spec_json` on save |
| Fast ask | `VectorIntakeFastAskPanel` | Quick questions → apply to spec | `volumetricVectorFastAskMapping` → spec |
| Embedded quote | `QuoteHandoffPanel` → `VolumetricLettersQuoteFlow` `embedded=true` | Read-only sim tab | Saved spec + local `flowState` reset on spec change |
| Standalone quote | `QuoteWizard` → `VolumetricLettersQuoteFlow` `embedded=false` | 3-method wizard + simulate | `flowState` + `initialProductSpec` prefill |
| Quotes list | `/quotes` + nav state from intake | Same standalone wizard | Handoff spec from V2 or classic |

**Classic must not:** introduce new independent state models, duplicate V2 production rules, or override V2-confirmed fields without explicit save.

---

## 5. Canonical `product_spec_json` fields (V2 writes)

| Domain | Key fields | Written by |
|--------|------------|------------|
| Vector | `vector_file_name`, `vector_detected_layers`, `vector_primary_letters_layer_*`, `vector_layer_mapping_confirmed` | V2 SVG + layers stages |
| Geometry | `width_mm`, `height_mm`, `letter_face_area_m2`, `letter_perimeter_m`, `letter_count`, `geometry_confirmed_for_file_name` | V2 geometry sync / manual |
| Production | `return_color`, `return_edge_color`, `volume_finish`, `return_depth_mm`, `depth_mm`, `face_vinyl_*`, `visual_chamfer_included` | V2 production + `applyFrontlitConstructionDefaults` |
| Lighting | `lighting_system_type`, `led_module_power_w`, `led_strip_density`, `light_color`, `letter_perimeter_m` | V2 lighting |
| PSU planning | `total_led_watts`, `required_psu_watts`, `psu_configuration`, `psu_allocation_status`, `selected_psu_watts` (optional classic mirror) | V2 lighting / frontlit sync |
| Pathway | `intake_input_pathway` | V2 context |

**Aliases:** `return_depth_mm` ↔ `depth_mm` must stay synced on save (canonical: `return_depth_mm`).

---

## 6. Classic compatibility rules

1. **Read** `product_spec_json` for display and QuoteWizard prefill.
2. **Write** only when operator explicitly saves in classic UI (no shadow state).
3. **Do not** add new gating rules solely in classic UI — mirror in canonical libs or backend policies.
4. **QuoteWizard `flowState`** is ephemeral; readiness for simulate may merge `flowState` with spec for legacy wizard only (see `mergeProductSpecWithFlowState`).
5. **Embedded** quote tab remains read-only summary; edits happen in Specificație or V2.

---

## 7. CostEngine handoff boundary

```
product_spec_json
    → mapProductSpecToVolumetricQuotePrefill / buildSimulateQuoteInputPayload
    → quote_input (API: POST /api/v1/product-system/simulate-cost)
    → CostEngine build_execution_layers_from_components
    → readiness.quote_gate / commercial blockers
```

| Layer | Module | Change policy |
|-------|--------|---------------|
| Payload builder | `volumetricQuoteInput.ts`, `volumetricQuoteFlowState.ts` | CANONICAL — handoff fixes allowed |
| Line applicability | `quote_input_line_gate.py`, template `components_json` | COSTING_HANDOFF — dedicated hotfixes |
| Formula math | `formula_handlers.py`, `cost_engine_service.py` | COSTING_HANDOFF — no drive-by changes |
| Soft warnings | `volumetric_quote_input_policy.py` | CANONICAL |
| Commercial gate | `volumetric_quote_ready_policy.py` | CANONICAL |

**Paint tubes:** `paint_tube_count` required only when `volume_finish === "paint_after_face_miter_bond"` (CostEngine gate + payload strip for stock cant).

**PSU:** CostEngine today uses `selected_psu_watts` (single). V2 may set `psu_configuration[]`; handoff maps max unit for classic simulate until multi-PSU costing exists.

---

## 8. Module status table

| Module / file | Status | Allowed changes | Forbidden changes |
|---------------|--------|-----------------|-------------------|
| `WorkIntakeV2.tsx`, `WorkIntakeV2Flow.tsx` | **ACTIVE** | Stages, handoff, persistence | Removing routes |
| `workIntakeV2/stages/*` | **ACTIVE** | UX within stage scope | Duplicating classic wizard |
| `lib/workIntakeV2/*` | **ACTIVE** | Stage logic, PSU/geometry | CostEngine formula edits |
| `intakeProductSpec.ts`, `intakeVolumetricSpec.ts` | **CANONICAL** | Schema fields with backend validator | Breaking aliases without migration |
| `volumetricFrontlitIntake.ts` | **CANONICAL** | Spec sync, PSU sizing metadata | CostEngine pricing |
| `volumetricQuoteInput.ts` | **CANONICAL / HANDOFF** | Prefill, payload, paint gating | New classic-only fields |
| `volumetricQuoteFlowState.ts` | **HANDOFF** | flowState merge for legacy wizard | New business rules without spec mirror |
| `intakeReadinessStages.ts` | **CANONICAL** | Display routing | Backend `ready_for_quote` policy |
| `volumetricIntakeFormPrep.ts` | **CANONICAL** | Prep summaries | CostEngine changes |
| `VolumetricLettersQuoteFlow.tsx` | **LEGACY** | Critical blockers, handoff bugs | New product rules, redesign |
| `Product001IntakeSpecEditor.tsx` | **LEGACY** | Data integrity | New production rules |
| `VectorIntakeFastAskPanel.tsx` | **LEGACY** | SVG parse regressions | New operator workflows |
| `VolumetricLettersWorkspace.tsx` | **LEGACY** | Tab shell breakage | Feature parity with V2 |
| `QuoteWizard.tsx` | **LEGACY** | Routing to volumetric flow | Generic wizard redesign |
| `quote_input_line_gate.py` | **HANDOFF** | Applicability gates | Global formula bypass |
| `cost_engine_service.py`, `formula_handlers.py` | **HANDOFF** | Dedicated costing builds | Drive-by intake fixes |
| `seed_build4_templates.py` | **HANDOFF** | Template line gates | Removing paint line |
| Multi-PSU CostEngine pricing | **DEFERRED** | Future build | Partial in hotfixes |
| LED strip costing handoff | **DEFERRED** | Future build | — |
| V2 as default `/intake/:id` | **DEFERRED** | Promotion milestone | — |

---

## 9. What future builds MAY touch

- WorkIntake V2 stages, repair panel, stage completion rules.
- Canonical spec validators (`backend/validators/intake_product_spec.py`).
- `mapProductSpecToVolumetricQuotePrefill` / `buildSimulateQuoteInputPayload` alignment with V2 output.
- CostEngine **applicability** and template line gates (dedicated PRs).
- Backend `volumetric_quote_*_policy.py` alignment with V2 fields.
- Critical regression fixes in LEGACY modules (documented in QA).

---

## 10. What future builds MUST NOT touch (without explicit approval)

- Redesigning classic `VolumetricLettersQuoteFlow` wizard UX.
- Adding new production rules only in `Product001IntakeSpecEditor` or fast-ask.
- CostEngine formula math / pricing registry in intake UX PRs.
- Quote / order / execution spine.
- Inventory reservation.
- Removing classic routes before migration milestone.
- Implementing multi-PSU or LED strip **pricing** inside readiness-only PRs.

---

## 11. Known gaps

| Gap | Owner path |
|-----|------------|
| CostEngine multi-PSU pricing | DEFERRED costing build |
| LED strip pricing handoff | DEFERRED |
| Classic cant vinyl vs V2 vinyl fields | LEGACY frozen; V2 canonical |
| DB template `components_json` may lag seed (painting op gate) | Re-seed or migration script |
| `intake/:id` still shows link to V2 as “experimental” | Promotion decision pending |
| Classic embedded quote tab vs standalone wizard confusion | Operator docs + V2 handoff only |
| Readiness systems still layered (UI vs CostEngine vs legacy status) | Consolidate in CANONICAL builds |

---

## 12. Test strategy

| Layer | Tests |
|-------|-------|
| V2 | `WorkIntakeV2Flow.test.tsx`, `workIntakeV2/*.test.ts` |
| Canonical handoff | `volumetricQuoteInput.test.ts`, `volumetricQuoteFlowState.test.ts` |
| Readiness | `intakeReadinessStages.test.ts`, `volumetricIntakeFormPrep.test.ts` |
| Backend policies | `test_volumetric_quote_input_policy.py`, `test_volumetric_quote_ready_policy.py` |
| CostEngine applicability | `test_quote_input_line_gate.py`, `test_volumetric_paint_tube_material.py` |
| E2E operator path | `/intake-v2/:id` → QuoteWizard → simulate (manual QA: IR-MQ47AGDG) |

**Rule:** V2 feature PRs must add/update tests in ACTIVE + CANONICAL layers. LEGACY changes require regression test or QA note.

---

## 13. Migration plan (phased)

### Phase 0 — LOCK (this document)
- Freeze classic business logic.
- Document boundaries and operator path.

### Phase 1 — Handoff hardening (in progress, uncommitted)
- V2 live spec handoff to QuoteWizard.
- `flowState` / `product_spec_json` alignment for legacy wizard.
- CostEngine paint line applicability.

### Phase 2 — Canonical quote_input only
- Single builder: spec → quote_input (no stale parallel fields).
- Deprecate classic-only quote_input keys in UI.

### Phase 3 — CostEngine PSU evolution
- `psu_configuration` native costing (multi-PSU).
- Reduce `selected_psu_watts` shim.

### Phase 4 — Route promotion
- Default volumetric intake → `/intake-v2/:id`.
- Classic `/intake/:id` → read-only archive or redirect.

---

## 14. Operator quick reference

**Do use:** `http://localhost:3000/intake-v2/IR-XXXX` → complete stages → **Deschide QuoteWizard**.

**Avoid for new rules:** Classic Product001 editor only, embedded Simulare tab as primary workspace, editing business rules only in QuoteWizard flowState without saving spec.
