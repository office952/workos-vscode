# Intake V6 â€” Functional Handoff Audit (V1)

**Date:** 2026-07-10
**Task:** INTAKE_V6_FUNCTIONAL_HANDOFF_AUDIT_V1
**Verdict:** **ALIGNED_WITH_GAPS**
**Accepted HEAD:** `cba4edd`
**Branch:** `main`
**Implementation performed:** NO
**Application code changed:** NO

---

## 1. Architecture readback (intended chain)

1. **Intake V6** owns operator input, confirmation, and `payload_json` on `intake_v6_workspaces`.
2. **Form contract** maps canonical keys â†’ `workspace_path` (pilot bindings in `IntakeV6ModularFormContractService`).
3. **ProductDefinition** compiles read-only preview from template dossier + optional `workspace_id` payload + aggregate merge â€” **does not price**.
4. **ProductAggregate** expands template-linked technical graph (components, materials, operations, `task_contract.task_rules`) â€” **not a client offer**.
5. **Downstream:** `quote_input` / CommercialPriceProposal / material breakdown read compiled inputs; Quote Snapshot V2 freezes handoff; Execution reads frozen snapshots not live Intake.
6. **Component-owned truth** stays on component paths (`letter_group_finishes`, `artwork_finishes`, linked segment paths).
7. **Product Template** composes modules/components; parent must not own component calculation truth.
8. **Task generation** must follow `task_contract.task_rules`, not parallel V3 catalog alone.
9. **No commercial hourly pricing** in this audit scope.
10. **ProductDefinition activates dependencies** from finish/geometry gates; **ProductAggregate** merges parent + linked module BOM.
11. **Step 3** confirms existing truth (`internal_draft_quote_confirmed`, handoff gates) â€” does not invent geometry.
12. **UI polish loop closed** â€” footer/display changes do not alter persistence semantics (verified separately).

---

## 2. Runtime fixture

| Field | Value |
| --- | --- |
| Workspace ID | `22ef834d-f2d0-453b-a7a7-118928c98a39` |
| Workspace code | `IV6-189D2F12` |
| Template | `TPL-VOLUMETRIC-LETTERS_v2` |
| Readiness | `ready_for_quote_preview` |
| SVG | `gradi-curat.svg` |
| Layer roles | 6 confirmed (4Ã— `face`, 2Ã— `printed_artwork`) |
| Persisted `selected_layer_refs` | **None** (derived refs computable: 4Ã— `vector_litere`) |
| Handoff | **Blocked** (`operator_confirmation_missing`, `unclassified_vector_artwork_requires_decision`) |
| ProductDefinition readiness | **partial** |
| Linked logo segments | 2 blocked (binding missing, finish unconfirmed) |

Route: http://127.0.0.1:3000/intake-v6/22ef834d-f2d0-453b-a7a7-118928c98a39/operator

---

## 3. Routes/endpoints verified (GET only)

See `docs/qa/intake-v6-functional-handoff-audit-v1/audit_index.md`. All returned HTTP 200. **Writes: NONE.**

---

## 4. Files inspected

### Intake V6
- `backend/models/intake_v6_workspace.py`
- `backend/schemas/intake_v4.py`, `backend/schemas/intake_v6.py`
- `backend/services/intake_v6_workspace_service.py` (`_sync_selected_layer_refs`, step saves)
- `backend/services/intake_v4_layer_role_service.py` (`selected_layer_refs_runtime_state`)
- `backend/routers/intake_v6_workspaces.py`
- `backend/services/intake_v6_modular_form_contract_service.py`
- `backend/services/form_system_contract_backbone_service.py`
- `frontend/src/lib/intakeV6/intakeV6LayerRoleOptions.ts`, `useIntakeV6Workspace.ts`

### ProductDefinition / Aggregate
- `backend/services/product_definition_builder_service.py`
- `backend/routers/product_system_product_definition.py`
- `backend/services/product_aggregate_service.py`
- `backend/routers/product_system_aggregate.py`
- `backend/services/linked_template_runtime_segment_extraction_service.py`

### Handoff / downstream (read-only)
- `backend/services/intake_v6_commercial_quote_service.py`
- `backend/services/intake_v4_pricing_input_service.py`
- `backend/services/intake_v6_priced_quote_dry_run_service.py`

---

## 5. Step 1 handoff matrix

| Intake concept | UI source | Workspace path | Persisted | Downstream | PD consumption | Aggregate effect | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| SVG identity | Upload | `svg_source.file_name` | `gradi-curat.svg` | `canonical_values.vector_file` | geometry_svg gate | svg_geometry_analysis | CONFIRMED |
| Layer roles (letters) | Decizii straturi | `layer_role_setup.layers[].confirmed_role=face` | 4 confirmed | `vector_litere` (derived) | letter geometry | letter ops | CONFIRMED |
| Layer roles (logo) | Vector Logo UI | `confirmed_role=printed_artwork` | 2 confirmed | **not in selected_layer_refs map** | linked segments | logo segment intents | PARTIAL |
| selected_layer_refs | Derived sync | `svg.selected_layer_refs` | **None** | Product Truth promotion | â€” | â€” | **MISSING** |
| Geometry summary | Analyzer | `quote_geometry.*` | letter_count=19, perimeter present | PD canonical_values | modules pending area | ops gated | PARTIAL |
| Artwork-only decision | Pas 1 guard | `layer_role_setup` + artwork flags | mixed face+artwork | handoff blocker | segment extraction | â€” | PARTIAL |

**Step 1 verdict:** Operator layer decisions **persist** in `layer_role_setup`. **Gap:** `selected_layer_refs` not persisted despite computable; `printed_artwork` not mapped to `vector_logo` in sync service.

---

## 6. Step 2 handoff matrix (sample)

| Operator field | UI label | Workspace path | Persisted | Component owner | PD target | Module activation | Aggregate effect | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Face finish | Oracal / finisaj faÈ›Äƒ | `letter_group_finishes[].face_finish_type` | oracal_651 per group | letter component | canonical_values | debitare_fata | face_cnc_cut, vinyl | PARTIAL (confirmed:false) |
| Return finish | Cant finish | `return_finish_type` | white/gold_aluminum | letter component | canonical_values | modelare_cant | side_forming | PARTIAL |
| Return depth | AdÃ¢ncime cant | `return_depth_mm` | 60 | letter component | canonical_values | modelare_cant | linked cant materials | CONFIRMED |
| Lighting | Iluminare | `finish_setup.illuminated` + `lighting_system_type` | True, led_modules | comp_led_litere | sistem_led | conditional_active | LED ops active | CONFIRMED |
| Backing | Spate | `backing_mode` | forex_10_no_bevel | comp_spate_litere | canonical_values | debitare_spate | back_cut | CONFIRMED |
| Mounting | Montaj | `mounting_system` | direct_wall | template compose | structura_suport | inactive (bars N/A) | premount inactive | CONFIRMED |
| Sablon | Template montaj | `mounting_template_enabled` | true | finisaje | finisaje | conditional_active | mounting_template_cnc_cut | CONFIRMED |
| Logo finish | Finisaje artwork | `artwork_finishes[]` | print_laminate, unconfirmed | linked logo segment | linked_templates.* | child template | segment blocked | PARTIAL |

**Step 2 verdict:** Finish values **persist** on component paths. Letter groups **not all confirmed** in payload. Logo segments **blocked by design** until binding+finish confirmed. Footer consolidation **display-only** (no persistence change).

---

## 7. Step 3 confirmation matrix

| Step 3 signal | Source | Persistence | PD effect | Blocker | Display-only? | Status |
| --- | --- | --- | --- | --- | --- | --- |
| Status configuraÈ›ie | Derived panel | None | None | reflects handoff | Yes | CORRECT |
| Checklist | ConfirmHandoffPanel | None direct | None | gates CTA | No (action UI) | CORRECT |
| Internal draft confirm | Operator toggle | `finish_setup.internal_draft_quote_confirmed` | None | handoff gate | No | **False on fixture** |
| Create draft quote | POST (not called) | Quote row | downstream | blocked | No | NOT_APPLICABLE |
| Handoff preview | GET | None | None | lists blockers | Yes | CORRECT |
| Footer warnings | Overlay | None | None | display | Yes | CORRECT |

**Step 3 verdict:** Step 3 **confirms** existing truth; does not invent product fields. Handoff **correctly blocked** until operator confirmation + artwork decision.

---

## 8. Form System binding matrix (sample)

| Form field | Binding source | Workspace destination | Owner | Conditional | PD consumer | Status |
| --- | --- | --- | --- | --- | --- | --- |
| vector_file | VOLUMETRIC_FIELD_BINDINGS | svg_source.file_name | geometry | always | geometry_svg | CORRECT |
| letter_count | pilot binding | quote_geometry.letter_count | geometry | always | quantity | CORRECT |
| face_finish_type | pilot binding | finish_setup.face_finish_type | letters | finisaje | canonical_values | CORRECT |
| lighting_system_type | pilot binding | finish_setup.lighting_system_type | LED module | sistem_led gate | conditional_active | CORRECT |
| width_mm / height_mm | pilot binding | client.width_mm/height_mm | client | required | missing on fixture | MISSING_BINDING value |
| commercial_inputs | orphan note | finish_setup.commercial_inputs | quote layer | â€” | derived_quote_input | LEGACY_ALIAS |

**Form System verdict:** Pilot **hardcoded** bindings for `TPL-VOLUMETRIC-LETTERS_v2` â€” documented HARDCODED_PILOT. Does not duplicate PD module rules; maps paths only.

---

## 9. ProductDefinition output matrix (summary)

| Section | Expected from Intake | Actual | Status |
| --- | --- | --- | --- |
| template_code | TPL-VOLUMETRIC-LETTERS_v2 | match | CONFIRMED |
| source_context | workspace_payload | workspace_id set | CONFIRMED |
| modules | gated by finish/geometry | LED+finisaje active; geometry pending | PARTIAL |
| components | dossier roles | 5 letter components | CONFIRMED |
| linked segments | logo layers | 2 blocked segments | PARTIAL |
| canonical_values | finish_setup + geometry | populated; groups unconfirmed | PARTIAL |
| validation | readiness | partial; missing width/height/letter_face_area_m2 | PARTIAL |
| pricing | none | resource_hints only | CORRECT |

**Trace example â€” return finish:** Operator `white_aluminum` on letter group â†’ `finish_setup.letter_group_finishes[].return_finish_type` â†’ PD `canonical_values.return_finish_type` + per-group â†’ `modelare_cant` linked materials â†’ aggregate `MAT-PROFIL-LATERAL-*` / `PAINTING`.

**Trace example â€” lighting:** Operator LED ON â†’ `finish_setup.lighting_system_type=led_modules` â†’ PD `sistem_led` conditional_active â†’ aggregate `led_install_letters`, `electrical_letters`.

**ProductDefinition verdict:** **Genuine compiler** for preview â€” merges workspace + aggregate. **Partial readiness** honest. **Does not price.**

---

## 10. ProductAggregate output matrix (summary)

| Aggregate item | PD source | Owner | Duplicate? | Missing? | Status |
| --- | --- | --- | ---: | ---: | --- |
| components[5] | dossier | template | No | No | CONFIRMED |
| materials[46] | parent+dossier+linked | per component | **Yes** (provenance merge) | No | MEDIUM_GAP |
| operations[42] | parent+dossier+linked | per component | **Yes** | No | MEDIUM_GAP |
| task_rules[13] | dossier task_rules_json | task_contract | No | No | CONFIRMED |
| workcenters | dossier | ops | Some null in raw API view | Partial | DOCUMENTED_DEBT |

**ProductAggregate verdict:** Shared **template-level** graph (no workspace_id on endpoint). Task rules present. **Duplicate rows** from parent+dossier+linked merge in PD preview â€” known merge artifact.

---

## 11. Component ownership matrix

| Value | Workspace path | Component owner | Template role | PD role | Aggregate | Verdict |
| --- | --- | --- | --- | --- | --- | --- |
| Face material/finish | letter_group_finishes | comp_face_litere | compose | canonical_values | face ops/materials | CORRECT |
| Return depth/finish | letter_group_finishes | comp_lateral / linked cant | compose | modelare_cant | cant materials | CORRECT |
| LED config | finish_setup | comp_led_litere | gate | sistem_led | LED ops | CORRECT |
| Backing | finish_setup.backing_mode | comp_spate_litere | compose | canonical_values | back_cut | CORRECT |
| Mounting/sablon | finish_setup.mounting_* | comp_finisaj_litere | compose | finisaje | template CNC | CORRECT |
| Vector Litere | layer_role_setup face | letter segments | root | geometry | letter graph | CORRECT |
| Vector Logo | printed_artwork layers | linked logo segment | linked child | linked_templates | segment intents | PARTIAL |
| SVG geometry | quote_geometry | shared | root | geometry_inputs | gate ops | CORRECT |

---

## 12. Naming alignment matrix

| Concept | Intake UI | Workspace key | Form contract | PD | Aggregate | Aligned? |
| --- | --- | --- | --- | --- | --- | --- |
| Vector Litere | Vector Litere | `face` | vector_file/geometry | vector_litere (derived) | letter components | **Partial** (storage `face`) |
| Vector Logo | Vector Logo | `printed_artwork` | artwork paths | linked segment | logo child | **Partial** (not vector_logo in refs) |
| Finisaje faÈ›Äƒ | Oracal 651 | `face_finish_type` | face_finish_type | oracal_651 | MAT-ORACAL-651 | Yes |
| Cant/return | Cant | `return_finish_type`, `return_depth_mm` | bindings | canonical_values | lateral materials | Yes |
| Iluminare/LED | Iluminare | `illuminated`, `lighting_system_type` | lighting_system_type | sistem_led | LED ops | Yes |
| Calcul estimativ | UI label | N/A (display) | derived_quote_input | not PD price | N/A | Yes |

---

## 13. Fallback / default findings (sample)

| File/function | Value | Fallback | Classification | Alters output? |
| --- | --- | --- | --- | ---: |
| `selected_layer_refs_runtime_state` | role map | only `face`,`logo` | **DANGEROUS_SILENT_DEFAULT** | Yes â€” omits printed_artwork |
| `_sync_selected_layer_refs` | empty refs | pop field | MISSING_FIELD_GUARD | Yes â€” clears persisted refs |
| `_resolve_module_state` structura_suport | mounting_system | inactive if not bars | SAFE_COMPATIBILITY | Yes (intended gate) |
| `_is_illuminated` | illuminated flag | lighting_system_type | SAFE_COMPATIBILITY | Yes (intended) |
| PD builder | missing workspace | template-only preview | DISPLAY_ONLY | Partial graph |

---

## 14. Parallel truth matrix (priority)

| Concept | Source A | Source B | Canonical | Conflict? | Consumer | Risk |
| --- | --- | --- | --- | --- | --- | --- |
| Layer roles | layer_role_setup | selected_layer_refs | layer_role_setup | **Yes** â€” refs stale | Product Truth | HIGH |
| Logo identity | printed_artwork | vector_logo enum | owner taxonomy + linked segments | **Yes** | PD segments | HIGH |
| Readiness | workspace.readiness_status | quote_handoff blockers | both valid gates | No | UI vs handoff | LOW |
| Product graph | ProductAggregate template | PD+workspace merge | PD preview for workspace | Partial | CostEngine | MEDIUM |
| Pricing | quote_input | CommercialPriceProposal | quote_input adapter | No if same input | dry-run | LOW |
| Tasks | task_contract.task_rules | V3 task preview catalog | task_rules canonical | Documented | task preview | MEDIUM |

---

## 15. Downstream consumer matrix

| Consumer | Input source | Same graph? | Recompiles? | Mutates upstream? | Status |
| --- | --- | ---: | ---: | ---: | --- |
| material-breakdown | workspace payload + cost adapters | Partial | Yes (estimate) | No | CORRECT read |
| pricing-input-preview | workspace â†’ quote_input | Yes | Yes | No | CORRECT |
| priced-quote-dry-run | quote_input â†’ CommercialPriceProposal | Yes | Yes | No | CORRECT (not canonical proof) |
| Quote Snapshot V2 | post-handoff write | Frozen | No live Intake | No | NOT exercised |
| ExecutionPlan V2 | frozen snapshot | N/A | No | No | NOT exercised |
| Legacy `/price` | separate | No | Yes | No | DOCUMENTED_DEBT |

---

## 16. Tests

```powershell
cd backend
$env:APP_ENV='development'; $env:DATABASE_URL='sqlite+aiosqlite:///./dev.db'
.\.venv\Scripts\python.exe -m pytest `
  tests/test_product_definition_builder.py `
  tests/test_product_definition_gradi_composition.py `
  tests/test_product_aggregate_volumetric_v2.py `
  tests/test_intake_v6_modular_form.py `
  tests/test_product_truth_promotion_planner_service.py `
  tests/test_return_cant_product_truth_bridge.py -q
```

| Metric | Value |
| --- | --- |
| Passed | 55/55 |
| Failed | 0 |
| Duration | 4.80s |
| Exit | 0 |
| Hangs | None |

E2E step1 smoke **not run** (explicitly out of scope â€” stale badge debt).

---

## 17. Findings priority

| ID | Classification | Summary |
| --- | --- | --- |
| FHA-01 | HIGH_RISK_DEVIATION | `selected_layer_refs` not persisted; computable 4 refs vs None in payload |
| FHA-02 | HIGH_RISK_DEVIATION | `printed_artwork` not mapped to `vector_logo` in `_SELECTED_LAYER_ROLE_MAP` |
| FHA-03 | MEDIUM_GAP | Linked logo segments: binding missing + finish unconfirmed (blocked correctly) |
| FHA-04 | MEDIUM_GAP | PD partial readiness â€” missing width/height/letter_face_area_m2 on fixture |
| FHA-05 | MEDIUM_GAP | PD preview duplicates materials/operations across provenance layers |
| FHA-06 | DOCUMENTED_DEBT | ProductAggregate endpoint template-only (no workspace_id) |
| FHA-07 | DOCUMENTED_DEBT | PricingInputPanel "PreÈ› oficial" when official totals (UI debt) |
| FHA-08 | DOCUMENTED_DEBT | E2E step1 smoke stale badge â€” not pipeline blocker |
| FHA-09 | CORRECT | Step 3 display-derived status; handoff gates block correctly |
| FHA-10 | CORRECT | Footer consolidation did not change persistence |
| FHA-11 | UNKNOWN | Negative-hole geometry treatment â€” not proven on this fixture path |

**Blocking functional issues:** **NONE** for operator truth loss (layer_role_setup intact). **Promotion/handoff blockers** are explicit, not silent.

---

## 18. Owner decisions required

### DEC-FHA-01 â€” selected_layer_refs persistence drift
- **Problem:** Derived refs computable but absent from persisted payload.
- **Evidence:** Runtime recompute â†’ 4 refs; GET workspace â†’ `svg.selected_layer_refs` None.
- **Risk:** Product Truth promotion may report SELECTED_LAYER_REFS_MISSING.
- **Options:** (A) backfill on read; (B) enforce sync on every layer-role save + migration; (C) promotion reads layer_role_setup directly.
- **Recommended:** B + promotion fallback to derive (read-only).
- **Blocked until GO:** YES

### DEC-FHA-02 â€” printed_artwork â†’ vector_logo mapping
- **Problem:** UI confirms Vector Logo as `printed_artwork`; sync map only knows `logo`.
- **Evidence:** `intake_v4_layer_role_service._SELECTED_LAYER_ROLE_MAP`; frontend `intakeV6LayerRoleOptions.ts`.
- **Risk:** Logo layers never enter selected_layer_refs; parallel linked-segment path only.
- **Options:** (A) extend map; (B) normalize to `logo` on save; (C) linked segments only (status quo).
- **Recommended:** A + document single canonical downstream role.
- **Blocked until GO:** YES

### DEC-FHA-03 â€” Linked template binding persistence
- **Problem:** Segments detected but `binding_status: missing`.
- **Evidence:** linked_segments + PD linked_template_runtime_segments.
- **Risk:** Logo composition incomplete for quote/order.
- **Options:** (A) persist binding on composition confirm; (B) keep read-only segment discovery until Product Truth slice.
- **Recommended:** B for now â€” align with existing blocked handoff.
- **Blocked until GO:** YES

---

## 19. Honest opinion

The handoff chain is **architecturally coherent** and mostly **aligned**: Intake persists rich payload, ProductDefinition compiles honestly as partial when data missing, ProductAggregate supplies shared BOM/task rules, handoff gates block instead of silently defaulting.

**Strongest layer:** Intake workspace persistence + explicit handoff/readiness gates.

**Weakest layer:** Derived `selected_layer_refs` sync and logo role mapping â€” creates parallel truth vs `layer_role_setup` and linked segments.

**Operator truth lost?** **No** â€” primary decisions remain in `layer_role_setup` and `finish_setup`.

**ProductDefinition compiler?** **Yes** â€” read-only, provenance-aware, partial when appropriate.

**ProductAggregate shared graph?** **Yes** at template level; workspace-specific activation comes via PD merge.

**Most dangerous gap:** FHA-01/FHA-02 â€” downstream consumers expecting persisted `selected_layer_refs` may disagree with live layer_role_setup.

**Do not implement yet:** Auto-mapping fixes, Product Truth promotion changes, linked binding writes, or aggregate dedup â€” need owner GO per DEC-FHA-*.

---

## 20. Recommended next functional slice

**INTAKE_V6_SELECTED_LAYER_REFS_AND_LOGO_ROLE_HANDOFF_V1** â€” narrow backend sync + mapping alignment + promotion read path; no UI polish; tests only for refs persistence and printed_artworkâ†’vector_logo.

---

## 21. Files created

- `docs/worklog/realignment/2026-07-10_intake_v6_functional_handoff_audit_v1.md`
- `docs/qa/intake-v6-functional-handoff-audit-v1/audit_index.md`
- `docs/qa/intake-v6-functional-handoff-audit-v1/captures/*.json` (11 read-only captures)
- `docs/qa/intake-v6-functional-handoff-audit-v1/scripts/extract_audit_summary.py`
- `docs/qa/intake-v6-functional-handoff-audit-v1/scripts/fetch_readonly_captures.ps1`

---

## 22. Forbidden scope

Confirmed: no application code, DB, seed, migration, pricing, UI, E2E, or test modifications.

---

## 23. Commit

`Audit Intake V6 functional handoff` (docs only)

---

## 24. Direction score

**Roadmap awareness:** 9/10
**Cat sunt in directia stabilita:** 88/100%

Dead pieces: New truth source? NO Â· Mapping removed? NO Â· Legacy deleted? NO Â· Parallel truth identified? **YES** Â· Silent defaults? **YES (mapped)** Â· Auto implementation? NO
