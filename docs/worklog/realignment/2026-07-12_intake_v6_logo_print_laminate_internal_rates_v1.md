# Intake V6 Logo Print and Laminate Internal Rates V1

**Task:** INTAKE_V6_LOGO_PRINT_LAMINATE_INTERNAL_RATES_V1
**Date:** 2026-07-12
**Accepted HEAD:** 64bc5f9
**Commit:** (see git log after commit)

## Owner decisions

- `logo_face_print` = **35 RON/m²** — configured
- `logo_face_laminate` = **35 RON/m²** — configured
- `logo_finish_application` — **deferred** (`INTERNAL_OPERATION_RULE_MISSING`)

## Catalog architecture

Added `LogoInternalOperationRate` entries to `backend/data/internal_cost_rules_volumetric_v2.py`:

- `INT_LOGO_FACE_PRINT_M2`
- `INT_LOGO_FACE_LAMINATE_M2`

No `DEV_BRIDGE_LOGO_*` bridge values.

## Rate resolution

`EstimatedInternalCostService._resolve_logo_operation_internal_rate(operation_code, op=...)` resolves only from logo catalog when `is_canonical_logo_artwork_operation_row` passes (`comp_logo_finish::{instance_id}`).

## Calculations (fixture)

| Instance | Area | Print subtotal | Laminate subtotal |
|---|---:|---:|---:|
| logo_instance_001 | 0.42 m² | 14.70 RON | 14.70 RON |
| logo_instance_002 | 0.38 m² | 13.30 RON | 13.30 RON |

## Status semantics

Print/laminate missing-rate blockers removed. Application blocker remains when active. EIC `status=blocked`, `ready_for_quote_snapshot=false`.

## Tests

98 targeted tests pass (catalog, EIC, dedupe, identity, PA, Cost BOM).

Partial states (print-only, application inactive) verified via test-only `FilteredLogoBomBuilder` until upstream BOM gates on `print_required` / `lamination_required`.

## Forbidden scope

No changes to ProductDefinition, ProductAggregate, Cost BOM, seed, frontend, DB, pricing registry, CPP, Quote/Order/Execution.

## Remaining debt

- `logo_finish_application` internal rate pending `INTAKE_V6_LOGO_FINISH_APPLICATION_SCOPE_DECISION_V1`
- Upstream partial-state BOM cardinality gating not yet wired

## Next safe step

`INTAKE_V6_LOGO_FINISH_APPLICATION_SCOPE_DECISION_V1` — owner scope sign-off only; no automatic rate implementation.

## Direction score

94/100
