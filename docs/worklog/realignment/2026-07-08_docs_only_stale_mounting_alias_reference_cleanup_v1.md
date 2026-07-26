# 2026-07-08 - docs only stale mounting alias reference cleanup v1

Summary:
- verified that `TPL-VOLUMETRIC-MOUNTING-STRUCTURE_v1` is gone from active runtime/code surfaces
- cleaned tracked docs so remaining mentions explicitly read as stale alias, superseded reference, or historical-only context
- left export/archive/untracked parked lanes untouched

Changed docs:
- `docs/qa/mounting-finish-alias-canonicalization-2026-07-08/MOUNTING_AND_FINISH_ALIAS_CANONICALIZATION_AUDIT_V1.md`
- `docs/worklog/realignment/2026-07-08_mounting_and_finish_alias_canonicalization_audit_v1.md`
- `docs/qa/realignment/2026-07-06/AUDIT_ONE_DIRTY_GROUP_PRODUCT_SYSTEM_SHARED_BASE_AFTER_F75FDB5_V1.md`
- `docs/qa/stale-mounting-alias-cleanup-2026-07-08/DOCS_ONLY_STALE_MOUNTING_ALIAS_REFERENCE_CLEANUP_V1.md`

Not changed on purpose:
- `docs/architecture/product-system/PRODUCT_SYSTEM_COMPONENT_OWNED_CALCULATION_BOUNDARY.md` because the file is currently part of a preexisting untracked lane and would be unsafe to absorb into this commit
- export/archive snapshots and generated packs

Canonical reminder:
- `TPL-METAL-PREMOUNT-STRUCTURE_v1` is the canonical runtime/backend mounting template code
- `TPL-VOLUMETRIC-MOUNTING-STRUCTURE_v1` is a stale alias and must not be used as canonical documentation truth