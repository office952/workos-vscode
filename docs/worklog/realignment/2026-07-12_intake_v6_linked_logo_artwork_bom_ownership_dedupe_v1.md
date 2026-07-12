# INTAKE_V6_LINKED_LOGO_ARTWORK_BOM_OWNERSHIP_DEDUPE_V1

**Date:** 2026-07-12  
**Verdict:** APPROVED_WITH_DOCUMENTED_DEBT  
**Accepted HEAD before:** `0df2c79`  
**Branch:** main  
**Compound folder:** `.compound-engineering/intake-v6-linked-logo-artwork-bom-ownership-dedupe-v1/`

---

## Task

Eliminate parallel cost truth for linked logo artwork BOM rows by enforcing a single canonical owner per concept per segment. Parent rate catalog task remains on hold.

## Root cause

Three producers emitted the same artwork concepts per segment: face child (erroneous print/lam declarations), finish child (media + application), and dossier `mapping_only` (`linked_segment::{segment}`). Dedupe keyed on `component_ref` without semantic ownership; Cost BOM treated mapping rows as costable.

## Owner decisions applied

All seven DEC-DEDUPE-* decisions closed. Artwork owner: `comp_logo_finish::{segment}`. Face owner: `comp_logo_face::{segment}` for substrate/CNC only. mapping_only = metadata/provenance, never automatic physical fallback.

## Canonical material ownership

| Concept | Owner |
|---|---|
| print_media | comp_logo_finish::{segment} |
| laminate_media | comp_logo_finish::{segment} |
| logo_face_material | comp_logo_face::{segment} |

## Canonical operation ownership

| Concept | Owner |
|---|---|
| logo_face_print | comp_logo_finish::{segment} |
| logo_face_laminate | comp_logo_finish::{segment} |
| logo_finish_application | comp_logo_finish::{segment} |
| logo_face_cnc_cut | comp_logo_face::{segment} |

## Seed realignment

`seed_tpl_volumetric_logo_v1.py`: removed artwork from face child; added print/lam operations to finish child. No rate changes, no operation code renames, no formula changes.

## ProductAggregate filter

`logo_artwork_cost_ownership.py` + filter in `product_aggregate_workspace_composition_service.py`.

## BOM guard

Defensive filter in `aggregate_cost_bom_adapter.py` using same contract (`non_canonical_logo_owner` skip reason).

## mapping_only semantics

`linked_segment::{segment}` rows suppressed from composed aggregate and Cost BOM when linked child owners exist.

## Cardinality before / after

Per segment (confirmed_bindings fixture):

- Before: print 3, laminate 3, print op 2, lam op 2, application op 2
- After: **1 each** for all five artwork concepts

Two segments: 4 materials + 6 operations total.

## Segment independence

logo-stanga and logo-dreapta each retain separate namespaced refs; no cross-segment dedupe.

> **Correction (2026-07-12):** Earlier examples used positional fixture names such as `logo-stanga` and `logo-dreapta`. These names are non-canonical and must be interpreted only as historical fixture labels. Canonical identity is stable and position-independent (`logo_instance_001`, etc.).

## Partial states

- Missing finish → zero artwork rows
- Missing binding → zero logo rows
- Print-only / print+lam scenarios covered in tests

## Downstream behavior

ProductAggregate, Cost BOM, and EIC consume canonical rows only. `INTERNAL_OPERATION_RULE_MISSING` unchanged. No EIC dedupe added.

## Tests

`test_logo_artwork_bom_ownership_dedupe.py` (13), plus updates to logo EIC ops tests and regression batches (102 targeted tests, all pass).

## Runtime probe

Probe confirms 1/1/1/1/1 per segment on `comp_logo_finish::*`, source `TPL-VOLUMETRIC-LOGO_v1`.

## Validation

Backend-only diff; no frontend, pricing, Quote/Order/Execution, schema, or live reseed.

## Review

APPROVED_WITH_DOCUMENTED_DEBT — rates and historical DB backfill deferred.

## Files changed

- `backend/seeds/seed_tpl_volumetric_logo_v1.py`
- `backend/services/logo_artwork_cost_ownership.py` (new)
- `backend/services/product_aggregate_workspace_composition_service.py`
- `backend/services/aggregate_cost_bom_adapter.py`
- `backend/tests/test_logo_artwork_bom_ownership_dedupe.py` (new)
- `backend/tests/test_estimated_internal_cost_logo_operations.py`
- Compound artifacts + this worklog

## Seed safety

Contract-only seed edit; no destructive reseed, no backfill, no production DB touch.

## Forbidden scope

Rates, CPP, pricing, Quote, Order, Execution, frontend, migrations — not touched.

## Honest opinion

The fix is correctly layered: contract source (seed) + composition truth + defensive BOM guard. Quantities were never wrong; cardinality was. This unblocks the duplication re-audit without prematurely wiring 35 RON/m².

## Remaining debt

35 RON/m² artwork operation rates remain unconfigured pending post-dedupe audit.

## Next safe step

Re-run `INTAKE_V6_ARTWORK_INTERNAL_RATE_DUPLICATION_AUDIT_V1` — do not implement rates automatically.

## Direction score

**92/100** — canonical ownership enforced; rate catalog and historical migration still pending.
