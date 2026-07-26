# INTAKE_V6_POSITION_INDEPENDENT_LAYER_COMPONENT_IDENTITY_REMEDIATION_V1

**Date:** 2026-07-12  
**Verdict:** APPROVED_WITH_DOCUMENTED_DEBT  
**Task baseline HEAD:** 0df2c79  
**Branch HEAD before commit:** 487233a (includes prior BOM dedupe commit — not modified in this task)

## Root cause

Logo instance identity was encoded as positional strings (`logo-stanga`, `logo-dreapta`), especially for raster/stroke SVG synthesis. These flowed into `layer_key`, `segment_key`, `component_ref`, Cost BOM, and EIC.

## Owner decision applied

- Operator roles: **Vector Litere**, **Vector Logo** only
- Technical identity: stable neutral `logo_instance_NNN` or existing SVG `layer_id`
- Position: geometry metadata only

## Stable identity source

`layer_id` / `layer_key` from SVG group id or neutral sequential synthesis id. Canonical backend resolver: `intake_v6_layer_identity.canonical_segment_key`.

## Runtime movement test

Swapping `position_hint` left↔right while keeping `layer_key`/`layer_id` unchanged preserves segment keys, ProductAggregate component refs, and Cost BOM cardinality.

## Forbidden scope respected

No rates, no BOM ownership dedupe changes, no Quote/Order/Execution, no migration.

## Remaining debt

Historical workspaces; legacy frontend tests with named SVG groups; resume BOM dedupe with neutral IDs.

## Next safe step

Revise and resume `INTAKE_V6_LINKED_LOGO_ARTWORK_BOM_OWNERSHIP_DEDUPE_V1` using `logo_instance_*` — do not execute automatically.

## Direction score

**90/100**
