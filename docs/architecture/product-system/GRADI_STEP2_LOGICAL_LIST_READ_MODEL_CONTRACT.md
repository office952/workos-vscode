# Gradi Step 2 Logical List Read Model Contract

## Purpose

Define the Step 2 / Review read-model contract for `gradi-curat.svg` after the Step 1 owner taxonomy alignment.

This contract is audit-only. It does not implement UI wiring, pricing changes, Product Truth schema changes, Quote/Order writes, inventory mutations, execution planning, DB changes, migrations, or CostEngine behavior.

## Boundary

In scope:

- `TPL-VOLUMETRIC-LETTERS_v2` plus logo artwork represented separately by owner taxonomy as `Vector Logo`.
- Runtime workspace `3c494f9f-4507-497a-912f-4f45fe709642` / `IV6-0EFC6C31` using `gradi-curat.svg`.
- Read-only comparison between backend logical read-model, material breakdown, priced dry-run, Review UI, and Confirm gate.

Out of scope:

- Analyzer changes.
- Step 1 dropdown or analysis panel changes.
- ProductDefinition write behavior.
- Product Truth persistence.
- Commercial pricing rule changes.
- Quote, Order, ExecutionPlan, TaskGraph, inventory, stock, or DB mutation.

## Authority Model

The Step 2 logical list is a read model. It must expose what the runtime currently knows and what remains a gap. It must not create commercial meaning, mutate source data, or hide missing formula bindings.

Authority order:

1. Analyzer/Form System/Product Truth inputs already persisted in the workspace payload.
2. Backend `material-breakdown` runtime rows.
3. Backend `priced-quote-dry-run` official commercial preview.
4. Backend `logical-list-read-model` reconciliation layer.
5. Frontend display only.

Frontend preview rows are not an authority if they differ from backend read-model or priced dry-run.

## Runtime Evidence

Read-only runtime checks on 2026-07-06:

- Route: `/intake-v6/3c494f9f-4507-497a-912f-4f45fe709642/operator`.
- Step 2 Review visible.
- Step 3 Confirm visible but handoff blocked.
- `priced-quote-dry-run` returned `V6_PRICED_DRY_RUN_READY`.
- Confirm page showed `Creeaza oferta pretuita` disabled and `Creeaza draft intern V6` disabled because final confirmations were incomplete.
- No write CTA was executed.

Observed commercial values:

- Internal cost reference: `772.92 EUR`.
- Official net: `5,321.55 RON`.
- Official gross with VAT: `6,439.08 RON`.

## Backend Read Model Contract

Endpoint:

- `GET /api/v1/intake-v6/workspaces/{workspace_id}/logical-list-read-model`

Current source:

- `gradi_logical_list_read_model_v1`.

Required envelope fields:

- `read_only: true`
- `source`
- `workspace_id`
- `workspace_code`
- `template_code`
- `categories`
- `core_row_count`
- `target_core_row_count`
- `core_rows_complete`
- `rows`
- `excluded_extra_commercial_lines`
- `warnings`
- `blockers`
- `runtime_totals`
- `validation`

Observed runtime envelope:

- `core_row_count: 21`
- `target_core_row_count: 21`
- `core_rows_complete: true`
- `categories: ["TOATE", "MATERIALE", "SERVICII / OPERATII", "MANOPERA"]`
- `warnings: ["BACKING_AREA_FALLBACK_USED", "ORACAL_ROLL_COLOR_SPLIT_MISSING"]`
- `blockers: []`
- `validation.no_duplicate_primary_tabs: true`
- `validation.ambalare_montaj_excluded_from_core_rows: true`
- `validation.categories_valid: true`
- `validation.formula_trace_metadata_present: true`

## Core Row Contract

The read model currently satisfies the 21 core row count for Step 2.

Required rows observed live:

| Row id | Category | Status | Formula status | Main gap |
| --- | --- | --- | --- | --- |
| `material.plexiglas_face` | `MATERIALE` | `MATCHED` | `proposed_binding` | none |
| `material.logo_plexiglas_face` | `MATERIALE` | `MATCHED` | `proposed_binding` | none |
| `material.forex_backing` | `MATERIALE` | `PARTIAL` | `proposed_binding` | `BACKING_AREA_FALLBACK_USED` |
| `material.face_oracal` | `MATERIALE` | `PARTIAL_TARIFF_CONFIRMATION_REQUIRED` | `proposed_binding` | color split warning |
| `material.print` | `MATERIALE` | `SPLIT_IN_RUNTIME` | `proposed_binding` | `PRINT_ROWS_AGGREGATED_FOR_LOGICAL_LIST` |
| `material.lamination` | `MATERIALE` | `SPLIT_IN_RUNTIME` | `proposed_binding` | `LAMINATION_ROWS_AGGREGATED_FOR_LOGICAL_LIST` |
| `material.return_profile` | `MATERIALE` | `MATCHED` | `proposed_binding` | none |
| `material.led_modules` | `MATERIALE` | `MATCHED` | `legacy_unversioned` | `FORMULA_TRACE_MISSING` |
| `material.led_psu` | `MATERIALE` | `MATCHED` | `legacy_unversioned` | none |
| `material.adhesive_cant` | `MATERIALE` | `MATCHED` | `proposed_binding` | none |
| `material.adhesive_led` | `MATERIALE` | `MATCHED` | `proposed_binding` | none |
| `material.wire_letters` | `MATERIALE` | `MATCHED` | `proposed_binding` | none |
| `material.wire_supply` | `MATERIALE` | `MATCHED` | `proposed_binding` | none |
| `material.mounting_accessories` | `MATERIALE` | `MATCHED` | `legacy_unversioned` | `COMMERCIAL_FORMULA_UNVERSIONED` |
| `service.cnc_face` | `SERVICII_OPERATII` | `MATCHED` | `proposed_binding` | none |
| `service.cnc_face_bevel` | `SERVICII_OPERATII` | `MATCHED` | `proposed_binding` | none |
| `service.cnc_back` | `SERVICII_OPERATII` | `MATCHED` | `proposed_binding` | dry-run unit bridge remains relevant |
| `service.print` | `SERVICII_OPERATII` | `SPLIT_IN_RUNTIME` | `proposed_binding` | `PRINT_SERVICE_ROWS_AGGREGATED_FOR_LOGICAL_LIST` |
| `service.lamination` | `SERVICII_OPERATII` | `SPLIT_IN_RUNTIME` | `legacy_unversioned` | `LAMINATION_SERVICE_ROWS_AGGREGATED_FOR_LOGICAL_LIST` |
| `service.application` | `SERVICII_OPERATII` | `SPLIT_IN_RUNTIME` | `legacy_unversioned` | `APPLICATION_SERVICE_ROWS_AGGREGATED_FOR_LOGICAL_LIST` |
| `labor.cant_glue` | `MANOPERA` | `MATCHED` | `proposed_binding` | none |

## Category Contract

Step 2 read-model categories remain coarse and accounting-oriented:

- `MATERIALE`
- `SERVICII_OPERATII`
- `MANOPERA`

`Finisaje`, `Iluminare`, and `Montaj` are UI review sections or module-level groupings, not logical-list core categories in the current contract.

`ambalare` and `montaj` may appear in priced dry-run as extra commercial lines, but they must stay outside the 21 core rows until owner-defined as part of a dedicated commercial rule slice.

## Frontend Display Contract

Step 2 fetches `logical-list-read-model` in `IntakeV6ReviewStep` and passes it to `IntakeV6LiveCalculationSummary`.

As of `GRADI_STEP2_LOGICAL_LIST_UI_WIRING_V1`, `IntakeV6LiveCalculationSummary` uses `logicalList.rows` as the primary owner-facing line list when rows are present. Material breakdown remains available as the fallback row source only when the logical read-model is absent, and as a technical/secondary runtime source for existing totals and other technical panels.

Observed UI:

- Shows official priced total and internal cost reference.
- Shows filters `Toate`, `Materiale`, `Servicii / Operatii`, `Manopera`, `Detalii`.
- Shows Review tabs `Finisaje`, `Iluminare`, `Montaj`.
- Shows owner-facing `Vector Litere` and `Vector Logo` finish groups.
- Shows the full 21-row logical list with formula code/version, status, gaps/warnings/blockers, category grouping, quantity/unit, and child-row indicator.

Fallback behavior:

- If `logicalList.rows.length > 0`, the visible line list is the backend logical read-model.
- If `logicalList` is missing or empty, the visible line list falls back to the existing material-breakdown display rows.
- Totals continue to use the existing internal cost and priced dry-run sources; the UI does not recalculate pricing from logical rows.

## Type Contract Gap

`GRADI_STEP2_LOGICAL_LIST_UI_WIRING_V1` adds frontend logical-list types in `intakeV6PricedQuoteTypes.ts` and reuses the existing `intakeV6Api.ts` exports:

- `IntakeV6LogicalListLineTrace`
- `IntakeV6LogicalListReadModelResponse`

The UI wiring avoids `any` for the logical-list response and keeps compatibility with the existing backend payload.

## Decision

Decision: `IMPLEMENTED - UI WIRING MINIMAL` after the prior `A. AUDIT-ONLY` contract.

Reason:

- Backend runtime already produces the 21 core rows, formula metadata, warnings, blockers, excluded extra commercial lines, and validation flags.
- Runtime UI confirms Review and Confirm gates are read-only/blocked as expected.
- The missing piece was frontend display/type wiring, not backend row production.

Validation:

- `pnpm.cmd --dir frontend exec vitest run src/components/workos/intake-v6/IntakeV6LiveCalculationSummary.test.tsx --reporter=verbose` passed: 13 tests.
- Runtime UI on `IV6-0EFC6C31` showed `Lista logică read-model · 21/21 rânduri`.
- Runtime UI categories: `Materiale · 14`, `Servicii / Operații · 6`, `Manoperă · 1`.
- Formula metadata and gaps/warnings were visible for all 21 rows.
- Step 1 remained unchanged: `Vector Litere` and `Vector Logo`, no `Vector Atipic`.
- Step 3 remained gated: priced quote and internal draft buttons disabled.

## Next Implementation Slice

Recommended next prompt:

`IMPLEMENT_GRADI_STEP2_LOGICAL_LIST_UI_CONTRACT_V1`

Implementation boundary:

- Add explicit frontend types for `IntakeV6LogicalListReadModelResponse` and row traces.
- Add a read-only Step 2 logical-list panel or details view that renders backend `logicalList.rows` directly.
- Preserve existing live calculation totals and commercial preview.
- Show formula code/status/gaps in an internal/detail surface, not as owner-facing primary copy.
- Add targeted Vitest coverage for row rendering and filters.

Still out of scope:

- pricing changes;
- Product Truth schema changes;
- Quote/Order writes;
- CostEngine;
- inventory;
- execution planning.