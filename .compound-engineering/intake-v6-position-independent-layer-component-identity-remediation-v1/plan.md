# INTAKE_V6_POSITION_INDEPENDENT_LAYER_COMPONENT_IDENTITY_REMEDIATION_V1 — Plan

**Phase:** PLAN COMPLETE  
**Verdict:** READY_FOR_BOUNDED_IMPLEMENTATION  
**Accepted HEAD (task baseline):** 0df2c79

## Layers

| Layer | Action |
|---|---|
| A — Analyzer source | Neutral `logo_instance_NNN` instead of positional IDs |
| B — Shared identity helpers | `layerInstanceIdentity.ts`, `intake_v6_layer_identity.py` |
| C — Backend read-path | Canonical segment keys + legacy alias normalization |
| D — Fixtures/tests | Replace positional fixture IDs |
| E — Docs | Correction notes + active contract wording |

**Out of scope:** BOM ownership dedupe, rates, Quote/Order/Execution, DB migration.

**PLAN COMPLETE**
