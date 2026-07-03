# Volumetric Letters Phase 3 Product Truth Canonical Payload Design

**Date:** 2026-07-01  
**Status:** FRONTEND_PURE_BUILDER_IMPLEMENTED  
**Runtime payload status:** RUNTIME_PAYLOAD_NOT_IMPLEMENTED  
**Backend schema status:** BACKEND_SCHEMA_NOT_IMPLEMENTED  
**API status:** API_NOT_IMPLEMENTED

## Purpose

This document defines the Phase 3A canonical Product Truth draft shape for Intake V6 volumetric letters and records the frontend-only implementation now available under `frontend/src/lib/intakeV6/productTruth/`.

The implementation is intentionally pure and in-memory. It does not persist, call an API, change saved Intake V6 payload shape, change gating, unlock Review/Confirmare, create quotes/orders, or feed downstream runtime systems.

## Implemented Now

| Area | Status | Implementation |
|---|---|---|
| Canonical TypeScript draft types | IMPLEMENTED | `productTruthTypes.ts` |
| Pure draft builder | IMPLEMENTED | `productTruthDraftBuilder.ts` |
| Read-only readiness preview | IMPLEMENTED | `productTruthReadiness.ts` |
| Controlled fixtures | IMPLEMENTED | `productTruthFixtures.ts` |
| Focused tests | IMPLEMENTED | `productTruthDraftBuilder.test.ts`, `productTruthReadiness.test.ts` |
| Phase 3A.1 hardening | IMPLEMENTED | Source kinds, issue metadata, fixture matrix, readiness issue arrays, sample payload documentation. |
| UI preview | NOT_IMPLEMENTED | Intentionally skipped to avoid flow/payload/gating changes. |
| Runtime Product Truth payload branch | RUNTIME_PAYLOAD_NOT_IMPLEMENTED | No saved `product_truth` field is created. |
| Backend schema/API | BACKEND_SCHEMA_NOT_IMPLEMENTED / API_NOT_IMPLEMENTED | No backend files changed. |
| Downstream consumption | NOT_IMPLEMENTED | ProductDefinition, CommercialPriceProposal, snapshots, aggregate, tasks, execution remain untouched. |

## Canonical Draft Shape

The draft shape is TypeScript-first and mirrors the target documented Product Truth branch:

```text
ProductTruthDraft
  metadata
  sourceSvg
  geometry
  layers
  components
    face
    back
    returnCant
    finish
    artwork
    lighting
    electrical
    support
    mounting
    pricingBoundary
  readiness
  blockers
  warnings
  audit
```

Every `ProductTruthField<T>` contains:

- `value`
- `state`
- `sourceRefs`
- `blockers`
- `warnings`

Every `ProductTruthIssue` now also carries `affectedComponent`, `affectedField`, typed `source`, and `quoteBlocker` / `orderBlocker` / `executionBlocker` booleans so fixtures and readiness checks can assert boundary behavior without relying on runtime systems.

Allowed states:

- `suggested`
- `confirmed`
- `fallback`
- `hydrated`
- `manual`
- `blocked`
- `warning`
- `not_applicable`
- `unknown`

## Source Map

| Draft branch | Existing source | State behavior | Notes |
|---|---|---|---|
| `metadata` | Intake V6 workspace identity | hydrated/blocked | Missing workspace/template blocks traceability. |
| `sourceSvg` | SVG source/analyzer metadata | hydrated/blocked/unknown | SVG source is required for this path. |
| `geometry` | `IntakeV6QuoteGeometry` compatible input | hydrated/confirmed/blocked | Geometry is draft context, not Product Truth completion by itself. |
| `layers` | layer role setup | suggested/confirmed/blocked | Auto roles stay suggested; pending roles block. |
| `face` | owner default + layer refs | fallback/suggested/blocked | Plexiglas opal 3 mm remains fallback until canonical confirmation exists. |
| `back` | `finish_setup.backing_mode` | hydrated/confirmed/fallback | Forex 10 mm no bevel is preserved as fallback if missing. |
| `returnCant` | `finish_setup.return_*` | hydrated/confirmed/fallback | Return depth defaults to 60 mm as fallback. |
| `finish` | face/group/artwork finish setup | hydrated/confirmed/unknown | Print and lamination are split even when encoded together today. |
| `artwork` | artwork finishes + layer role hints | suggested/hydrated/confirmed | `printed_artwork` is suggestion, not automatic final print. |
| `lighting` | `finish_setup.illuminated`, lighting system, color | hydrated/confirmed/fallback | Lighting truth remains source-labelled. |
| `electrical` | LED/PSU fields + owner cable defaults | hydrated/fallback/unknown | Cable defaults are commercial defaults, not site planning truth. |
| `support` | SVG support hints and mounting bridge evidence | suggested/unknown/warning | Support is never confirmed from `mounting_system`. |
| `mounting` | `finish_setup.mounting_system`, template fields | hydrated/confirmed/blocked | `mounting_scope` remains blocked because current form lacks it. |
| `pricingBoundary` | architecture contract only | not_applicable | Pricing is not Product Truth and is not called. |

## Readiness Preview Rules

The readiness evaluator is read-only and local to the draft object.

| Flag | Behavior in Phase 3A |
|---|---|
| `readyForReview` | true only when review-level draft blockers are absent. Does not unlock the actual UI. |
| `productTruthDraftComplete` | true only if the draft has no blockers. |
| `readyForInternalDraft` | local preview only; does not enable existing CTA. |
| `readyForCommercialProposal` | always false with `PHASE_3A_PREVIEW_ONLY`. |
| `readyForQuoteSnapshot` | always false with `PHASE_3A_PREVIEW_ONLY`. |
| `readyForOrderSnapshot` | always false with `PHASE_3A_PREVIEW_ONLY`. |
| `readyForProductAggregate` | always false with `PHASE_3A_PREVIEW_ONLY`. |
| `readyForExecutionPlan` | always false with `PHASE_3A_PREVIEW_ONLY`. |

Readiness flags carry both summary code arrays and full `blockerIssues` / `warningIssues` arrays. This is still local read-only preview data and is not wired into Intake V6 buttons, saved payloads, quote creation, order creation, ProductAggregate creation, or ExecutionPlan creation.

## Phase 3A.1 Fixture Coverage Matrix

| Fixture | Purpose |
|---|---|
| `gradiCuratUnconfirmedFixture` | Analyzer suggestions pending operator confirmation; fallback face fields; missing mounting/support/finish target. |
| `gradiCuratConfirmedRolesFixture` | Confirmed layer roles but missing canonical Product Truth decisions such as artwork decision and face/material confirmation. |
| `gradiCuratCompleteReviewLikeFixture` | Complete in-memory Product Truth draft candidate with confirmed face/back/return/finish/artwork/mounting/support fields. |
| `gradiCuratSupportMountingMismatchFixture` | Steel bar mounting bridge evidence remains suggested support only, never confirmed support truth. |
| `gradiCuratArtworkIgnoredFixture` | Operator ignores artwork and print/lamination become false. |
| `gradiCuratArtworkOnlyFixture` | Artwork-only decision stays distinct from printed artwork. |
| `gradiCuratPrintNoLaminateFixture` | Print can be true while lamination remains false. |
| `gradiCuratLaminateWithoutPrintWarningFixture` | Lamination without print emits warning, not silent confirmation. |
| `gradiCuratMissingFinishTargetFixture` | Active finish without explicit target blocks commercial readiness. |
| `gradiCuratExecutionOnlyElectricalFixture` | Extra cable/site/PSU placement stay order/execution-only unless quote scoped. |

## Phase 3A.1 Builder Hardening Rules

- Analyzer layer roles remain `suggested`; confirmed and ignored roles require operator-state evidence.
- Face material and thickness remain owner defaults unless explicitly confirmed; default thickness is 3 mm, not 5 mm.
- Forex 10 mm no-sanfren is preserved as the default backing; selected sanfren is manual or confirmed input.
- Return/cant depth remains 60 mm only when explicit or fallback-labelled; active cant with missing depth emits a blocker.
- Finish target is first-class draft truth; active finish without target emits `FINISH_TARGET_MISSING`.
- `printed_artwork` SVG roles are suggestions only. `artwork_decision` separates printed, artwork-only, ignored, and missing decision states.
- `print_required` and `lamination_required` are separate booleans. Lamination without print emits `LAMINATION_WITHOUT_PRINT`.
- Support truth remains separate from mounting truth. `steel_bars` / `aluminum_bars`, `support_panel`, and `frame` evidence can suggest support but cannot confirm it.
- Cable defaults remain Product Truth commercial defaults; extra cable, site details, and PSU placement are order/execution-only unless explicitly quote scoped.
- Pricing boundary contains no commercial price, CostEngine output, quote mutation, order mutation, or downstream materialization.

## Sample Payload

Docs-only sample: `docs/architecture/product-system/samples/gradi_curat_product_truth_draft.sample.json`.

The sample includes `SAMPLE_ONLY_NOT_RUNTIME_PAYLOAD` and must not be treated as a saved Intake V6 payload, backend schema, API response, ProductDefinition input, quote snapshot, order snapshot, ProductAggregate, task graph, or execution plan.

## Support / Mounting Split

Phase 3A preserves the mandatory split:

- `mounting.mountingSystem` records current mounting truth from the existing Review form.
- `support.supportRequired` can become `suggested` from support-like SVG roles or bar-mounting bridge evidence.
- `support.supportRequired` is not `confirmed` from `mounting_system`.
- `SUPPORT_MOUNTING_BRIDGE_NOT_CANONICAL` is emitted when bridge evidence exists.
- `SUPPORT_REQUIRED_UNKNOWN` is emitted when no first-class support truth exists.

## Forbidden Now

The Phase 3A implementation forbids:

- backend changes;
- DB/schema/seed changes;
- API calls;
- persistence;
- runtime Product Truth payload writes;
- Intake V6 readiness/gating changes;
- ProductDefinition consumption;
- ProductSystem runtime migration;
- CommercialPriceProposal execution;
- Quote Snapshot or Order Snapshot creation;
- ProductAggregate;
- Task Graph;
- ExecutionPlan;
- quote/order/execution/materialization;
- Employee Mobile.

## Later Work

Recommended next safe slice:

1. Add a read-only UI/dev inspection panel only if owner wants runtime visibility, still without payload writes.
2. Design explicit first-class Intake V6 controls or payload fields for face material/thickness confirmation, mounting scope, support required/type/source, PSU placement, and site details.
3. Only after owner GO, add runtime `product_truth` payload persistence behind an explicit save boundary.
4. Later, migrate ProductDefinition and commercial proposal consumers to canonical Product Truth.