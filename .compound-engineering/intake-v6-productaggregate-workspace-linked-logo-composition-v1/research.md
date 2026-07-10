# INTAKE_V6_PRODUCTAGGREGATE_WORKSPACE_LINKED_LOGO_COMPOSITION_V1 — Research

**Phase:** RESEARCH COMPLETE  
**Accepted HEAD:** 9d18806  
**Verdict:** READY_FOR_BOUNDED_IMPLEMENTATION

## Repository preflight

| Check | Result |
|---|---|
| Branch | `main` |
| HEAD | `9d18806` |
| Accepted committed state | Binding persistence task committed |
| Unrelated dirty | `.gitignore`, ProductSystem screenshots, other worklogs, `IntakeV6LayersOperatorPanel.tsx`, QA folders |
| Compound files (prior task) | `.compound-engineering/intake-v6-linked-logo-layer-bindings-persistence-v1/` |
| Unexpected application changes | None on accepted HEAD |

## Architecture readback

```text
Intake V6 workspace
  → layer_role_setup (operator layer truth)
  → selected_layer_refs (derived)
  → linked segments (extractor-derived stable segment_key)
  → layer_bindings[] (canonical binding truth, explicit confirm)
  → ProductDefinition workspace composition (compiler)
  → ProductAggregate workspace projection (THIS TASK)
  → downstream cost/snapshot/execution (out of scope)
```

Confirmed:

- ProductDefinition is the concrete product compiler for workspace-aware preview.
- ProductAggregate today is template-only; must not independently resolve bindings from recommendation.
- ProductAggregate must not read `product_composition_recommendation` as truth.
- ProductAggregate must not calculate commercial price.
- Task rules remain execution-planning driver; informational ops are not auto-tasks.
- Logo finish truth stays in `artwork_finishes[]`; parent letters product composes but does not absorb logo finish values.

## Source inventory matrix

| File/function | Responsibility | Input | Output | Workspace-aware? | Canonical/derived | Risk |
|---|---|---|---|---|---|---|
| `persist_logo_layer_bindings_from_composition_confirmation` | Write canonical bindings | confirmed items + layers | `layer_bindings[]` | yes | canonical write | LOW — done |
| `extract_linked_template_segments_from_workspace_payload` | Runtime segment rows | payload + backbone composition | segments + blockers | yes | derived read | LOW |
| `ProductDefinitionBuilderService.build_preview` | PD compiler | template + optional workspace_id | `ProductDefinitionPreview` | yes | derived | MED — letters aggregate only in components |
| `ProductAggregateService.build` | Template aggregate | template_code | `ProductAggregate` | **no** | template canonical | HIGH gap for logo |
| `get_product_aggregate` | Public aggregate API | template_code only | template aggregate | **no** | — | HIGH |
| `get_product_definition_preview` | Public PD API | template + workspace_id | PD preview | yes | — | LOW |
| `build_intake_v6_assembly_draft_preview` | Assembly draft | payload bindings | 1 logo component w/ all layer keys | yes | derived | MED — collapses segments |
| `aggregate_cost_bom_adapter` | Cost BOM from PD+PA | PD + PA + quote_input | cost BOM | indirect | derived | OUT OF SCOPE |
| `form_system_contract_backbone` | Linked composition contract | template | `linked_template_composition` | static | canonical contract | LOW |

## Current ProductDefinition output (gradi + confirmed bindings)

Evidence: `backend/tests/test_intake_v6_layer_binding_persistence.py`, `test_product_definition_gradi_composition.py`.

| PD item | Owner | Source path | Segment-aware? | Ready? | Provenance |
|---|---|---|---|---|---|
| Root product | LETTERS_v2 | template_code + workspace | partial | partial | form + aggregate |
| `components[]` | letters dossier | `ProductAggregateService.build(LETTERS_v2)` | **no logo rows** | letters yes | dossier |
| `linked_template_runtime_segments.segments[]` | workspace binding | `layer_bindings[]` + layers + finishes | **yes** (`logo-stanga`, `logo-dreapta`) | binding confirmed; finish may block segment readiness | extractor |
| `owning_template_code` per segment | linked template contract | backbone `TPL-VOLUMETRIC-LOGO_v1` | yes | yes | form backbone |
| Logo finishes | component-owned | `finish_setup.artwork_finishes[]` | yes per `layer_key` | if `confirmed` | workspace |
| `material_roles[]` | letters aggregate | parent + linked modules | **letters only** | partial | aggregate |
| `operation_roles[]` | letters aggregate | parent + linked modules | **letters only** | partial | aggregate |
| Task rules in PD | **not exposed** | — | — | — | only via separate PA |
| Blockers | segment readiness | extractor `_product_truth_readiness` | yes | `LINKED_TEMPLATE_BINDING_MISSING` gone when binding confirmed | derived |

### Mandatory PD questions

| Question | Answer |
|---|---|
| Stable component/segment identity? | **Segments yes** via `segment_key`; **components no** for logo |
| Owning template code exposed? | **Yes** on linked segments |
| Component-owned finish data exposed? | **Yes** on segment `finish` sub-object |
| Active modules exposed? | **Yes** for letters modules only |
| Materials/processes per component? | **Letters only** in PD roles |
| Enough provenance for dedupe? | **Partial** — segment paths exist; aggregate merge not implemented |
| Shared operations identified? | **No** at PD level |
| Task rules present? | **Template-level only** via separate aggregate build |

**Conclusion:** PD already contains enough **segment binding + finish + template ownership** information for aggregate composition, but **does not** expand logo template graph into components/materials/operations. Adapter must expand logo template aggregate per confirmed segment.

## Current ProductAggregate limitation

| Aggregate concern | Current behavior | Required behavior | Gap |
|---|---|---|---|
| Workspace awareness | `build(template_code)` only | optional workspace composition | **YES** |
| Endpoint input | template_code path param | + optional workspace_id | **YES** |
| ProductDefinition input | none | consume PD preview internally | **YES** |
| Composition input | none | confirmed linked segments from PD | **YES** |
| Linked logo expansion | only if building LOGO root standalone | expand per bound segment under LETTERS root | **YES** |
| Multiple segments | N/A at workspace | two traceable instances | **YES** |
| Segment identity | lost (template-only) | preserve `segment_key` | **YES** |
| Logo finishes | unavailable | read via PD segments; not copied into binding | **YES** |
| Task rules | dossier-derived for single template | compose letters + per-segment logo rules | **YES** |
| Dedupe | code+source+provenance key | must not dedupe separate segment consumption | **partial** |

Endpoint today: `GET /api/v1/product-system/aggregate/{template_code}` — no workspace_id.

## Adapter options evaluation

| Option | Truth duplication | Code size | Contract change | Dedupe clarity | Risk | Recommendation |
|---|---|---|---|---|---|---|
| **A — PA consumes PD output** | **Low** | Medium | Minimal (optional query param) | High if merge rules explicit | Medium | **SELECT** |
| B — PA reads workspace bindings directly | High (re-resolves segments) | Medium | Minimal | Low | High | Reject |
| C — New shared composition contract schema | Low | Large | New public contract | High | Medium | Defer unless A insufficient |
| D — PD owns aggregate assembly | Low | Large | PD response bloat | Medium | Circular coupling | Reject |

**Selected:** Option A — `ProductDefinitionBuilderService.build_preview` remains compiler; new workspace composition adapter expands logo template aggregates using PD `linked_template_runtime_segments`.

## Owner decisions flagged (see plan)

- DEC-PA-01: segment instance model (two instances recommended)
- DEC-PA-02: partial aggregate when finish missing
- DEC-PA-03: task rule merge owner
- DEC-PA-04: endpoint shape (optional workspace_id on existing aggregate GET)
- DEC-PA-05: aggregate preview vs final Step 3 confirmation

## Journal

- Inspected `product_definition_builder_service.py`, `product_aggregate_service.py`, routers, linked segment extractor, assembly preview (collapsed logo component pattern — must not copy for aggregate).
- Confirmed binding persistence tests prove PD consumes confirmed bindings.
- No ProductAggregate workspace code exists on HEAD `9d18806`.
