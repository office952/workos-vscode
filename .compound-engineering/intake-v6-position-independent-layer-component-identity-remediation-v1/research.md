# INTAKE_V6_POSITION_INDEPENDENT_LAYER_COMPONENT_IDENTITY_REMEDIATION_V1 — Research

**Phase:** RESEARCH COMPLETE

## Root cause

`layer_key` == `segment_key` propagates through bindings, ProductDefinition segments, ProductAggregate namespacing, Cost BOM, and EIC. Raster/stroke logo synthesis in `semanticAndPseudoLayerExpansion.ts` assigned `logo-stanga` / `logo-dreapta` from viewBox center-X — position became identity.

## Existing stable source

- SVG named group `id` when present
- Persisted `layer_id` in `layer_role_setup.layers[]`
- New neutral sequential IDs: `logo_instance_001`, `logo_instance_002`

## Not canonical

Position labels, display names, array order, geometry centroids.

**RESEARCH COMPLETE**
