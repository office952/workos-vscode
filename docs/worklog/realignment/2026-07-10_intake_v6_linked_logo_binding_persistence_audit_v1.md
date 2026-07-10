# Intake V6 — Linked Logo Binding Persistence Audit V1

| Field | Value |
|-------|-------|
| Task | `INTAKE_V6_LINKED_LOGO_BINDING_PERSISTENCE_AUDIT_V1` |
| Verdict | **BINDING_NOT_PERSISTED** |
| Secondary | **PARALLEL_BINDING_TRUTH** (recommendation vs `layer_bindings`) |
| Accepted HEAD | `10a17fd` |
| Branch | `main` |
| Implementation | **NO** |
| DB rows changed | **0** |

---

## Owner direction

Letters root `TPL-VOLUMETRIC-LETTERS_v2` + logo child `TPL-VOLUMETRIC-LOGO_v1` must link inside one product flow with component-owned truth, shared-operation dedupe, one ProductDefinition/Aggregate graph, no duplicate products.

---

## Architecture readback

```
SVG layer
  → layer_role_setup (canonical operator roles)
  → selected_layer_refs (derived persist: vector_litere / vector_logo)
  → linked segment detection (derived read: roles + artwork_finishes + layer_bindings)
  → linked template binding (INTENDED: layer_bindings[] — NOT persisted today)
  → component-owned finish (artwork_finishes[] per logo segment)
  → ProductDefinition preview (linked_template_runtime_segments attached)
  → ProductAggregate (template catalog graph — NOT workspace-aware)
  → Cost / Quote / Execution (downstream frozen snapshots)
```

Confirmed principles:

- Vector Logo is a **layer-role decision** (`printed_artwork` → `vector_logo`), not a root product template.
- Logo segment needs **linked technical component** `TPL-VOLUMETRIC-LOGO_v1`.
- Binding **must** persist in workspace payload; today it **does not** in `layer_bindings`.
- ProductDefinition **reads** segments from payload + form backbone; does **not** invent binding when missing.
- ProductAggregate merges **template/module links from DB**; does not consume workspace logo binding.
- ProductDefinition does **not** calculate commercial price.
- Task rules remain execution driver; aggregate is technical not commercial offer.

---

## Runtime fixture

| Field | Value |
|-------|-------|
| Workspace ID | `22ef834d-f2d0-453b-a7a7-118928c98a39` |
| Code | IV6-189D2F12 |
| Template | TPL-VOLUMETRIC-LETTERS_v2 |
| SVG | gradi-curat.svg |
| Layers | 4× face + 2× printed_artwork (confirmed) |
| `layer_bindings` | **0 rows** |
| `selected_layer_refs` | 6 (4 vector_litere + 2 vector_logo) |
| Logo finishes | print_laminate, `confirmed: false` |
| Composition rec | letters_plus_logo, logo template **suggested** |
| Composition confirmed | **false** |

---

## Routes / endpoints verified (read-only)

| Method | URL | HTTP | Writes | Key finding |
|--------|-----|------|--------|-------------|
| GET | `/api/v1/intake-v6/workspaces/{id}` | 200 | NONE | `layer_bindings: []`; refs + finishes present |
| GET | `/api/v1/intake-v6/workspaces/{id}/linked-template-segments` | 200 | NONE | 2 segments; `binding_status: missing` |
| GET | `/api/v1/product-system/product-definition/TPL-VOLUMETRIC-LETTERS_v2?workspace_id={id}` | 200 | NONE | Same segment blockers in PD preview |
| GET | `/api/v1/intake-v6/workspaces/{id}/runtime-capture-read-model` | 200 | NONE | `svg.selected_layer_refs[]` promoted paths |
| GET | `/api/v1/intake-v6/workspaces/{id}/product-truth-promotion-planner` | 200 | NONE | vector_logo refs; no linked_templates.logo |
| GET | `/api/v1/intake-v6/workspaces/{id}/product-system-binding` | 200 | NONE | Module metadata only — **not** logo layer binding |

Captures: `docs/qa/intake-v6-linked-logo-binding-persistence-audit-v1/captures/`

---

## Source file inventory

| File / function | Responsibility | Reads | Writes | Canonical / derived |
|-----------------|----------------|-------|--------|---------------------|
| `intake_v4_layer_role_service.py` — `derive_selected_layer_refs_from_setup` | Role → ref projection | `layer_role_setup.layers` | `svg.selected_layer_refs` (via sync) | Derived persist |
| `intake_v6_workspace_service.py` — `save_layer_roles_*` | Layer updates | layers[] | layers, refs, composition rec | Canonical layers; **no layer_bindings** |
| `linked_template_runtime_segment_extraction_service.py` — `extract_*` | Segment rows | layers, **layer_bindings**, artwork_finishes, backbone | — | Derived read-only |
| `intake_v6_product_composition_recommendation_service.py` — `apply_*` | Composition suggestion | logo roles | `product_composition_recommendation` | Derived persist (suggested) |
| `intake_v6_assembly_preview_service.py` — `_synthetic_bindings_from_layers` | In-memory binding synth | layers | — (preview only) | Derived ephemeral |
| `product_definition_builder_service.py` — `build_preview` | PD + linked segments | workspace payload | — | Read-only preview |
| `product_aggregate_service.py` — `build` | Template graph | DB templates/modules | — | Template canonical |
| `form_system_contract_backbone_service.py` — `_linked_template_composition` | Contract metadata | — | — | Static contract |
| `product_truth_promotion_planner_service.py` — `_classify_selected_layer_entries` | Promotion plan | `selected_layer_refs` | — | Read-only |
| `IntakeV6ProductCompositionPanel.tsx` | UI display | recommendation + PD segments | — | Display only |

---

## Logo segment identity matrix

| Source layer/ref | Derived segment ID | Grouping rule | Persisted? | Stable? | Consumer | Status |
|------------------|-------------------|---------------|------------|---------|----------|--------|
| logo-stanga | `logo-stanga` | 1 layer = 1 segment (`layer_key`) | Segment key from layer_key | Yes on reload | PD linked segments | **CORRECT** |
| logo-dreapta | `logo-dreapta` | 1 layer = 1 segment | Same | Yes | PD linked segments | **CORRECT** |
| vector_logo ref logo-stanga | N/A (ref not segment id) | Ref parallel to segment | refs persisted | Yes | Promotion planner | **CORRECT** |

Multiple logo layers → **two separate components/segments** (not merged into one logo component).

---

## Binding inventory

| Binding field/concept | Path | Set where | Persisted? | Read where | Canonical? | Status |
|-----------------------|------|-----------|------------|------------|------------|--------|
| Per-segment template bind | `layer_role_setup.layer_bindings[].target_template_code` | Schema + tests only | **NO** (fixture count 0) | Segment extractor, assembly preview | **Intended canonical** | **MISSING_BINDING** |
| Binding status | `layer_bindings[].binding_status` | Tests / synthetic preview | **NO** persist | Segment extractor | Canonical when present | **MISSING_BINDING** |
| Composition recommendation | `product_composition_recommendation.recommended_templates[]` | `apply_product_composition_recommendation` on layer save | **YES** (derived) | UI composition panel | Derived suggestion | **PARTIAL** |
| Composition confirm | `product_composition_confirmed` | Operator confirm endpoint | Optional | Handoff | Operator confirm | **PARTIAL** (false on fixture) |
| Form backbone | `linked_template_composition.linked_templates[]` | Static contract | N/A (not workspace) | Segment extractor, PD | Contract default `suggested` | **CORRECT** (contract) |
| Product truth path | `linked_templates.{code}.segments.{key}` | Segment extractor output | Derived in preview only | PD UI | Target path | **PARTIAL** |
| `product_system_bindings` | payload alias | Historical audit only | **NO writer** | — | — | **UNKNOWN/legacy** |

---

## Binding lifecycle matrix

| Lifecycle stage | Binding value | Source | Persisted? | Lost? | Risk |
|-----------------|---------------|--------|------------|-------|------|
| Initial workspace | — | — | — | — | — |
| After SVG analysis | logo layers detected | analyzer | roles in setup | — | LOW |
| After layer role confirm | printed_artwork confirmed | operator | layers + derived refs | — | LOW |
| After configurare | print_laminate values | operator | artwork_finishes | — | LOW |
| **Binding selection** | TPL-VOLUMETRIC-LOGO_v1 suggested | composition rec + contract | **Not in layer_bindings** | **YES** | **HIGH** |
| After reload | same | DB payload | refs + finishes yes; bindings **no** | Bindings never saved | **HIGH** |
| Step 3 summary | segments show missing binding | PD extractor | Read-only | — | Expected blocker |
| PD preview | binding_status missing | extractor | — | — | Blocks logo readiness |
| PA preview | child template from DB links | aggregate service | Template-level only | Workspace bind N/A | MEDIUM |

---

## Form System binding matrix

| Form field | Condition | Workspace path | Component owner | Multi-segment | Status |
|------------|-----------|----------------|-----------------|---------------|--------|
| `svg.selected_layer_group` | vector roles confirmed | `svg.selected_layer_refs[]` | Root SVG projection | Yes (refs list) | **CORRECT** |
| Linked template picker | vector_logo present | *None* | Logo component | — | **MISSING_BINDING** |
| `finish_setup.artwork_finishes` | artwork rows | per `layer_key` | Logo segment | Yes | **CORRECT** (values) |
| Backbone `linked_templates.logo` | letters v2 root | contract only | Logo child template | Segments in contract empty | **HARDCODED_PILOT** |

No Form System field writes `layer_bindings` or confirms `target_template_code`.

---

## Component ownership matrix

| Value/rule | Current path | Expected owner | Current owner | Correct? | Risk |
|------------|--------------|----------------|---------------|----------|------|
| Logo execution print_laminate | `finish_setup.artwork_finishes[].execution_type` | Logo segment | Logo segment row | **YES** | LOW |
| Logo return 60mm / Alb | `artwork_finishes[].return_*` | Logo segment | Logo segment | **YES** | LOW |
| Letter face/cant | `letter_group_finishes[]` | Letters | Letters | **YES** | LOW |
| Linked template code | *missing* | Logo segment binding | Nowhere persisted | **NO** | **BLOCKING** |
| Logo component in assembly | synthetic/persisted bindings | Logo component | Preview-only synth | **PARTIAL** | HIGH |
| Root finish_setup defaults | `finish_setup.return_depth_mm` etc. | Letters default | Root payload | **ROOT_LEAK** (defaults) | MEDIUM |

---

## Logo finish matrix

| Logo segment | Persisted finish | Confirmation | Template binding | PD consumption | Aggregate effect | Status |
|--------------|------------------|--------------|------------------|----------------|------------------|--------|
| logo-stanga | print_laminate, 60mm, white_aluminum | `confirmed: false` | missing | finish in segment row; blocked | Template-only logo ops exist; not workspace-composed | **PARTIAL** |
| logo-dreapta | same | `confirmed: false` | missing | same | same | **PARTIAL** |

Finish **values** persist and reload. Blockers: `LINKED_SEGMENT_FINISH_MISSING` (legacy confirmed flag) + `LINKED_TEMPLATE_BINDING_MISSING`.

---

## ProductDefinition composition matrix

| Section | Letters | Logo | Shared | Duplicate? | Missing? | Status |
|---------|---------|------|--------|------------|----------|--------|
| Root template | TPL-VOLUMETRIC-LETTERS_v2 | — | — | No | — | OK |
| Linked segments | — | 2 segments → LOGO_v1 owner | — | No | binding missing | **BLOCKED** |
| Active modules | letter modules | logo not activated via binding | — | — | logo module path | **PARTIAL** |
| Materials/processes | from form bindings | not fully composed | potential shared prep | Unknown | logo materials | **PARTIAL** |
| Readiness | partial | blocked segments | — | — | binding + finish confirm | **BLOCKED** |
| Price | none | none | — | — | — | **CORRECT** |

Trace broken link:

```
Vector Logo layer (confirmed)
  → selected ref (vector_logo) ✅
  → linked segment (logo-stanga) ✅
  → finish_setup.artwork_finishes ✅
  → layer_bindings.target_template_code ❌ MISSING
  → ProductDefinition segment binding_status missing ❌
  → ProductAggregate workspace composition ❌ (template-only)
```

---

## ProductAggregate composition matrix

| Aggregate item | Letters source | Logo source | Shared? | Duplicate? | Task rule? | Status |
|----------------|----------------|-------------|---------|------------|------------|--------|
| Parent template | TPL-VOLUMETRIC-LETTERS_v2 DB | — | — | — | Yes | OK |
| Child linked module | module links | TPL-VOLUM-ALUMINIU etc. | Some shared | Dedupe in service | Yes | Template-level |
| Logo child TPL-VOLUMETRIC-LOGO_v1 | DB if linked | module link | — | — | — | **Not workspace-bound** |
| Workspace-specific 2 segments | — | — | — | — | — | **NOT CONSUMED** |

**Explicit classification:** ProductAggregate is **template-only** for workspace binding; cannot reflect per-segment operator binding without new read path or snapshot.

---

## Shared operation deduplication matrix

| Operation | Letters | Logo | Shared once? | Current rows | Desired | Risk |
|-----------|---------|------|--------------|--------------|---------|------|
| SVG prep | yes | yes | should | assembly policy says assembly scope | dedupe_common_operations in rec | **MEDIUM** — not enforced in PD |
| Print/laminate | letters face | logo artwork | per component | breakdown may add logo rows | per logo component | **MEDIUM** duplicate risk |
| CNC face cut | yes | logo face | separate | separate components in assembly preview | separate | OK |
| Assembly/pack | policy assembly | policy assembly | once | recommendation policy only | ProductDefinition merge | **DOCUMENTED_DEBT** |

Duplicate prevention belongs primarily in **ProductDefinition composition merge** + **task rule generation**; not implemented for workspace binding gap.

---

## Parallel binding truth matrix

| Binding concept | Source A | Source B | Canonical | Conflict? | Risk |
|-----------------|----------|----------|-----------|-----------|------|
| Logo template | `product_composition_recommendation` → LOGO_v1 suggested | `layer_bindings` empty | **layer_bindings** (intended) | **YES** | **HIGH** |
| Logo template | Form backbone suggested | layer_bindings | layer_bindings + operator confirm | YES | HIGH |
| Segment identity | layer_key | selected_layer_refs.layer_id | layer_key for segments | No | LOW |
| Finish completeness | artwork values present | artwork.confirmed false | values for operator UX; confirm flag legacy | **YES** | MEDIUM (post-confirmation audit) |
| Product system binding API | module metadata | logo layer binding | different concepts | Naming trap | MEDIUM |

---

## Blocker semantics matrix

| Blocker | Source | Valid? | Class | Status |
|---------|--------|--------|-------|--------|
| LINKED_TEMPLATE_BINDING_MISSING | segment extractor | **YES** — no persisted binding | VALID_OPERATOR_BLOCKER | Operator must choose/confirm product solution |
| LINKED_SEGMENT_FINISH_MISSING | segment extractor | **PARTIAL** — values exist, confirmed=false | VALID_SYSTEM_BLOCKER / legacy flag | Distinguish value vs flag |
| unclassified_vector_artwork_requires_decision | handoff | fixture-specific | VALID_OPERATOR_BLOCKER | Separate from binding |
| operator_confirmation_missing | handoff Step 3 | YES | FINAL_CONFIRMATION | Not binding |
| PRODUCT_COMPOSITION_NOT_CONFIRMED | composition | YES | VALID_OPERATOR_BLOCKER | Parallel to binding |

---

## Downstream consumer matrix

| Consumer | Input | Receives logo component? | Recompiles binding? | Frozen? | Risk |
|----------|-------|--------------------------|---------------------|---------|------|
| EstimatedInternalCost | PD/BOM preview | Partial via breakdown | Live workspace | No | MEDIUM |
| CommercialPriceProposal | snapshot inputs | Should from frozen graph | Should not | Quote-stage | HIGH if live re-resolve |
| Quote Snapshot V2 | handoff snapshot | Expected composed | Must freeze | Yes | HIGH |
| ExecutionPlan V2 | order snapshot | Expected composed | Must not re-resolve intake | Yes | HIGH |
| Task rules | aggregate/dossier | Template-level | — | Template | MEDIUM |

Downstream must consume **frozen composed graph**, not re-resolve empty `layer_bindings`.

---

## Tests

| Command | Passed | Failed | Exit | Notes |
|---------|--------|--------|------|-------|
| pytest `-k "logo or linked or gradi or vector_logo or letters_plus"` (6 files) | 20 | 2 | 1 | Pre-existing failures unrelated to binding audit |

**Missing coverage (mandatory review):**

- Binding persists across reload — **NO test for production write path** (path absent)
- Two logo segments bind deterministically when persisted — tested only with fixture injection in gradi PD test
- PD consumes **persisted** binding from operator save — **NOT COVERED**
- PA duplicate print/laminate guard — partial in material breakdown test
- Final confirmation does not create binding — **NOT COVERED** (expected true)

---

## Findings priority

| ID | Classification | Summary |
|----|----------------|---------|
| F-01 | **BLOCKING_FUNCTIONAL** | `layer_bindings` never written on canonical Intake V6 save paths |
| F-02 | **BLOCKING_FUNCTIONAL** | Segment extractor reports `binding_status: missing` on live fixture despite composition rec suggesting LOGO_v1 |
| F-03 | **HIGH_RISK_DEVIATION** | Parallel truth: `product_composition_recommendation` vs empty `layer_bindings` |
| F-04 | **HIGH_RISK_DEVIATION** | Assembly preview synthetic bindings not persisted; PD/segments ignore synth |
| F-05 | **MEDIUM_GAP** | No Form System / UI path to confirm per-segment linked template binding |
| F-06 | **MEDIUM_GAP** | ProductAggregate template-only; workspace segment binding not consumed |
| F-07 | **DOCUMENTED_DEBT** | Shared operation dedupe policy in recommendation not enforced in PD merge |
| F-08 | **CORRECT** | vector_logo refs derive and persist (6 refs on fixture) |
| F-09 | **CORRECT** | Logo finish values persist per segment (print_laminate) |
| F-10 | **CORRECT** | ProductDefinition attaches linked segments read-only; no price calculation |

---

## Owner decisions required

### DEC-LLB-01 — Canonical binding path

- **Problem:** No persisted per-segment linked template binding.
- **Evidence:** Fixture `layer_bindings_count: 0`; runtime `LINKED_TEMPLATE_BINDING_MISSING`.
- **Options:** (A) Persist `layer_bindings` on composition confirm; (B) New `linked_template_bindings[]` path; (C) Promote composition rec to canonical binding.
- **Recommended:** (A) — schema already exists.
- **Files:** `intake_v6_workspace_service.py`, composition confirm handler, segment extractor.
- **Migration/backfill:** Backfill optional; historical rows remain unresolved without owner policy.
- **Owner GO:** YES

### DEC-LLB-02 — Binding confirmation timing

- **Problem:** Suggested vs confirmed binding semantics split across rec, contract, segments.
- **Recommended:** Operator confirms composition → write `layer_bindings[].binding_status=confirmed`.
- **Owner GO:** YES

### DEC-LLB-03 — Per-segment vs merged logo component

- **Problem:** Two logo layers = two segments today.
- **Evidence:** logo-stanga, logo-dreapta separate segment_keys.
- **Recommended:** Keep per-segment unless owner wants single merged logo component.
- **Owner GO:** YES

### DEC-LLB-04 — Finish confirmed flag vs value completeness

- **Problem:** `LINKED_SEGMENT_FINISH_MISSING` despite print_laminate persisted.
- **Recommended:** Align segment readiness with value-based completeness (consistent with Step 3 audit).
- **Owner GO:** YES

### DEC-LLB-05 — ProductAggregate workspace consumption

- **Problem:** PA cannot reflect workspace-bound logo segments.
- **Recommended:** Separate slice: workspace-aware assembly snapshot or PD-driven aggregate overlay.
- **Owner GO:** YES

---

## Honest opinion

Logo segments **are detected correctly** with stable keys. Template binding **is not persisted** — it disappears because **`layer_bindings` has no production writer**. Logo finishes are **component-row owned** and reload-safe; blockers mix **real missing binding** with **legacy confirmed flags**. ProductDefinition **does not** genuinely compose letters+logo into a ready linked product on the live fixture. ProductAggregate is **one template graph**, not one workspace-coherent letters+logo instance. Operations **may duplicate** without binding-driven merge. **Most dangerous gap:** operator/composition suggests LOGO_v1 but runtime reads **missing binding**, blocking PD/readiness/handoff. **Do not implement** auto-binding, backfill, or PA merge until DEC-LLB-01/02 approved.

---

## Recommended next functional slice

**INTAKE_V6_LINKED_LOGO_LAYER_BINDINGS_PERSISTENCE_V1** — Persist and confirm `layer_role_setup.layer_bindings[]` when operator confirms product composition; wire save path only; segment extractor + tests; no ProductAggregate merge yet.

---

## Files created

- `docs/worklog/realignment/2026-07-10_intake_v6_linked_logo_binding_persistence_audit_v1.md`
- `docs/qa/intake-v6-linked-logo-binding-persistence-audit-v1/AUDIT_INDEX.md`
- `docs/qa/intake-v6-linked-logo-binding-persistence-audit-v1/read_only_audit_capture.py`
- `docs/qa/intake-v6-linked-logo-binding-persistence-audit-v1/captures/*`

## Forbidden scope

No application code, DB, seeds, pricing, templates, UI, or fixture mutation.

## Commit

Message: `Audit Intake V6 linked logo binding`

## Direction score

**88/100** — Audit proves the gap precisely; architecture direction clear; implementation deliberately deferred.
