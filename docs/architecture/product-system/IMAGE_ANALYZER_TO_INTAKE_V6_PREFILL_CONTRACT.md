# Image Analyzer to Intake V6 Prefill Contract

Status: contract/spec only
Date: 2026-07-06
Scope: WorkOS Intake V6 prefill boundary for a future external Image Analyzer integration

## Purpose

Image Analyzer is an analyzer-first source that can prefill Intake V6 with suggested geometry, colors, objects, warnings, and template proposals.

Image Analyzer is not Product Truth. It is not ProductDefinition. It is not Pricing. It is not Quote. It is not Order. It is not Execution.

The official WorkOS flow remains:

```text
Work Intake
-> Product System template selection / hint
-> Intake V6 workspace
-> analyzer suggestions
-> Form System composition
-> operator review and confirmation
-> Product Truth
-> ProductDefinition
-> CommercialPriceProposal / Offer
-> Quote Snapshot
-> Order Snapshot
-> Execution later
```

Image Analyzer must enter this flow as prefill/proposal only. It must not create a parallel quote form and must not bypass Intake V6.

## Source Discriminator

Required field for future Image Analyzer payloads:

```json
{
  "analysis_source_type": "image"
}
```

Allowed future source types, stated for contract clarity only:

- `"svg"` - current/future SVG source normalization.
- `"image"` - Image Analyzer prefill source.

No runtime enum is implemented by this document.

## External Image Analyzer Payload

Expected payload shape:

```json
{
  "analysis_source_type": "image",
  "source_file": {},
  "image_analysis": {},
  "foreground_bbox": {},
  "scale_mode": {},
  "commercial_colors": [],
  "objects": [],
  "area": {},
  "perimeter": {},
  "layer_breakdown": [],
  "diagnostics": [],
  "operator_review_required": true,
  "confirmed_geometry": {},
  "quote_ready_payload": {},
  "template_proposals": [],
  "intake_v6_prefill": {}
}
```

Important semantics:

- `confirmed_geometry` is only the external Image Analyzer term.
- Inside WorkOS, image-derived geometry remains suggested/pending until Intake V6 operator confirmation.
- `quote_ready_payload` is only external analyzer terminology.
- Inside WorkOS, `quote_ready_payload` maps to Intake V6 prefill/proposal, not final quote readiness.

## Source and State Rules

All mapped values must carry source/state semantics.

Allowed states:

- `suggested`
- `prefill`
- `operator_pending`
- `confirmed`
- `blocked`
- `warning`
- `rejected`

Rules:

- Image-derived values enter WorkOS as `suggested` or `prefill`.
- `operator_review_required` defaults to `true`.
- No image-derived value becomes `confirmed` without explicit Intake V6 operator action.
- Fallback, hydrated, or image-prefill values must not appear as final truth.
- Diagnostics remain warnings/attention, not blockers, unless a future Intake V6 rule explicitly promotes them.

## Mapping Table

| Image Analyzer field | Intake V6 target | Initial WorkOS state | Rule |
|---|---|---|---|
| `confirmed_geometry.width_mm` | work geometry width | `suggested` / `operator_pending` | operator must confirm |
| `confirmed_geometry.height_mm` | work geometry height | `suggested` / `operator_pending` | operator must confirm |
| `confirmed_geometry.area_m2` | estimated surface | `suggested` | not pricing truth |
| `confirmed_geometry.perimeter_m` | estimated perimeter | `suggested` | not pricing truth |
| `commercial_colors` | finish/color candidates | `suggested` | no automatic material truth |
| `objects` / `objects_count` | body count / complexity candidates | `suggested` | review required |
| `layer_breakdown` | pseudo-segments / candidate modules | `suggested` | not SVG layer roles |
| `diagnostics` | attention/warnings | `warning` | read-only until rules exist |
| `operator_review_required` | confirmation gate | `blocked` until review | default true |
| `template_proposals` | ProductDefinition proposal input | `suggested` | ProductDefinition decides later |
| `quote_ready_payload` | Intake V6 prefill/proposal | `prefill` | not final quote readiness |

## Template Proposal Rules

- Image Analyzer may propose `TPL-VOLUMETRIC-LETTERS_v2` as a root candidate.
- Image Analyzer may propose `TPL-VOLUMETRIC-LOGO_v1` only as linked child/candidate.
- Image Analyzer must not activate Logo as root offerable.
- Image Analyzer must not activate component root.
- Image Analyzer must not activate component quote.
- ProductDefinition decides after confirmed Intake V6 state.
- Owner GO is required for any future Logo root offerability.

## Forbidden Outputs

Image Analyzer payload must not create, write, or directly activate:

- Cost
- CommercialPriceProposal
- Offer
- Quote
- Quote Snapshot
- Order
- Order Snapshot
- Execution
- ProductAggregate
- TaskGraph
- ExecutionPlan
- stock movement
- inventory movement
- employee/operator production tasks
- final Product Truth
- final ProductDefinition

## Current WorkOS Anchors

The current WorkOS flow this contract must preserve:

- `/intake` is the Work Intake entrypoint.
- `NewIntakeDialog` owns method selection.
- Current method id is `svg_analyzer_intake_v6`.
- Current analyzer mode is `analyzer_first`.
- Workspace creation goes through `ensureIntakeV6WorkspaceForIntakeRequest(...)`.
- Intake V6 operator route remains `/intake-v6/:workspaceId/operator`.
- Intake V6 shell remains `Straturi -> Review -> Confirmare`.
- Current SVG analyzer step remains SVG-specific.

## Future Implementation Slices

A. Contract/spec only - current slice.

B. Disabled/preview UI card in `NewIntakeDialog`.

- Add `Image Analyzer - Intake V6` as disabled or preview-only.
- Explain that image analysis prefill requires operator review.
- Do not create quote/order/execution.

C. Workspace source discriminator.

- Add `analysis_source_type` support in workspace model/client types.
- Preserve SVG flow unchanged.

D. Image payload adapter.

- Map external Image Analyzer JSON into Intake V6 prefill.
- Preserve source/state metadata.
- Require operator confirmation.

E. Operator review UI for image geometry/prefill.

- Review image geometry, object count, colors, area, perimeter, and diagnostics.
- Keep all values pending until operator confirms.

F. Tests proving no bypass.

- Image payload cannot bypass Intake V6.
- Image payload cannot create Cost/Offer/Quote/Order/Execution.
- Image payload cannot mark values confirmed without operator action.
- Image payload cannot activate Logo root offerability.
- Letters root remains `TPL-VOLUMETRIC-LETTERS_v2`.
- Logo remains linked child/candidate.
- Existing SVG flow remains unchanged.

G. Owner-reviewed integration with external Image Analyzer repo.

- Only after contract, UI preview, workspace source awareness, adapter, and tests are accepted.

## Required Future Tests

Future implementation must include tests proving:

- Image payload cannot bypass Intake V6.
- Image payload cannot create Cost/Offer/Quote/Order/Execution.
- Image payload cannot mark values confirmed without operator action.
- Image payload cannot activate Logo root offerability.
- Letters root remains `TPL-VOLUMETRIC-LETTERS_v2`.
- Logo remains linked child/candidate.
- Existing SVG flow remains unchanged.

## Roadmap Guard

This document is a contract boundary only. It does not implement runtime behavior, UI cards, adapters, backend services, migrations, seeds, pricing, quote/order/execution, ProductAggregate, TaskGraph, or ExecutionPlan.