# 2026-07-08 - return cant component preview readiness remediation v1

HEAD before:

- `97d67c1`

HEAD after:

- pending at write time

Fisiere citite:

- ownership map docs
- backbone contract
- modular form contract
- mini module registry
- Product Truth draft builder
- field projection helper
- Review / Confirm read-only helpers

Fisiere atinse:

- `docs/architecture/product-system/RETURN_CANT_COMPONENT_PREVIEW_READINESS_REMEDIATION.md`
- `docs/qa/return-cant-component-preview-readiness-remediation-2026-07-08/RETURN_CANT_COMPONENT_PREVIEW_READINESS_REMEDIATION_V1.md`
- `docs/worklog/realignment/2026-07-08_return_cant_component_preview_readiness_remediation_v1.md`

Decizia readiness:

- `RETURN_CANT_BLOCKED_WITH_EXPLICIT_FIELDS`

Blockers inchisi:

- niciun blocker runtime inchis
- am inchis doar ambiguitatea de decizie dintre `partial_ready` si `ready_for_readonly_preview`

Blockers ramasi:

- material_profile lipsa
- perimeter_source lipsa ca path explicit
- dependency pe `face.confirmed_perimeter` lipsa ca field explicit
- split incomplet pentru color target
- layer_group_ids lipsa
- confirmation_state lipsa ca field de componenta

Forbidden scope confirmation:

- fara cod
- fara UI
- fara endpoint
- fara component root
- fara component quote
- fara Logo offerability
- fara Pricing / Quote / Order / Execution
- fara ProductAggregate / TaskGraph / ExecutionPlan
- fara DB/seed/migration

Next recommended prompt:

- `TASK — RETURN_CANT_MISSING_TRUTH_FIELDS_CONTRACT_V1`

Observatie importanta:

- daca urmatorul prompt ramane direct `INTAKE_V6_RETURN_CANT_COMPONENT_PREVIEW_READONLY_SLICE_V1`, exista risc mare sa se implementeze un preview care doar recicleaza fallback-uri si root geometry, fara component-owned truth suficient.