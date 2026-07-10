# INTAKE_V6_LINKED_LOGO_LAYER_BINDINGS_PERSISTENCE_V1 — Research

**Phase:** RESEARCH COMPLETE  
**Accepted HEAD:** 1de22c7  
**Verdict:** READY_TO_PLAN

## Owner decisions applied in research

- DEC-LLB-01: canonical path `payload.layer_role_setup.layer_bindings[]`
- DEC-LLB-02: persist only on explicit composition confirmation
- DEC-LLB-03: per stable logo segment (`layer_key`)
- DEC-LLB-04: finishes remain in `artwork_finishes[]`
- DEC-LLB-05: ProductAggregate out of scope

## Research matrix

| Function/file | Input | Output | Reads binding | Writes binding | Canonical/derived | Gap |
|---|---|---|---|---|---|---|
| `build_product_composition_recommendation` | layers | recommendation + composition_items | no | no | derived advisory | none |
| `apply_product_composition_recommendation` | payload | recommendation fields | no | no | derived | does not touch bindings |
| `save_product_composition_confirmation_for_workspace` | confirmed + items | workspace payload | no | **was missing** | should write canonical | **fixed in this task** |
| `persist_logo_layer_bindings_from_composition_confirmation` | confirmed items + layers | layer_bindings[] | no | yes | canonical writer | new |
| `extract_linked_template_segments_from_workspace_payload` | payload + composition | segments + blockers | yes (`layer_bindings`) | no | derived runtime | consumes confirmed status |
| `ProductDefinitionBuilderService.build_preview` | workspace payload | linked segments summary | via extractor | no | derived | no change required |
| `IntakeV6ProductCompositionPanel` | payload + onConfirm | UI confirm button | no | no | UI only | already wired |

## Mandatory questions

| Question | Answer |
|---|---|
| Payload shape segment extractor expects | `layer_bindings[]` rows keyed by `layer_key`, with `target_template_code`, `binding_status` |
| Existing schema | `IntakeV4LayerBindingContract` in `backend/schemas/intake_v4.py` |
| Accepted binding statuses | `pending`, `suggested`, `confirmed`, `ignored` — readiness requires `confirmed` |
| Test-only writer before | tests/fixtures only; assembly preview had synthetic in-memory bindings |
| Composition confirmation mutating | yes — `PUT .../product-composition-confirmation` |
| Writes recommendation as truth | no — only `product_composition_confirmed` before this task |
| Atomic with workspace save | yes — same `_persist_payload` transaction |
| Reload preserves unknown fields | yes — pydantic round-trip via `model_dump` |
| Segment identity deterministic | yes — stable `layer_key` from SVG layer setup |
| ProductDefinition consumes binding | yes — via linked segment extractor when `binding_status=confirmed` |
| Product Truth promotion same binding | yes — reads workspace payload paths |
| Blocker removed after persistence | `LINKED_TEMPLATE_BINDING_MISSING` |
| Blockers that remain | finish missing, geometry, final Step 3 confirmation, ProductAggregate workspace gap |

## Journal

- Inspected audit artifacts under `docs/qa/intake-v6-linked-logo-binding-persistence-audit-v1/`
- Confirmed fixture `22ef834d-f2d0-453b-a7a7-118928c98a39` has `layer_bindings_count: 0`
- Confirmed frontend already calls `confirmProductComposition(items)` on explicit button click
- No DB schema change required
