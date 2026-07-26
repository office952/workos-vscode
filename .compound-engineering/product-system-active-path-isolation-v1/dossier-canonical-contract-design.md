# Dossier Canonical Contract Design

## Verdict

**`PARTIAL_BLOCKED_BY_CANONICAL_CONTRACT_DATA`** for repo-wide isolation.  
**V2 active-path isolation achievable** without migration/seeds in this task.

## Smallest change (v2)

1. **`CanonicalTemplateContractService`** — facade for variants, components, form keys, output blocks.
2. **Aggregate** — `components_json` + registry map; dossier never behavior source.
3. **Intake V4/V5/V6** — canonical variants; dossier_status metadata only.
4. **Output blocks** — in-code volumetric blocks; dossier optional for provenance trace.
5. **Readiness** — template formula materials + canonical output blocks; execution from template operations.

## Classification of missing ownership

| Gap | Status |
|-----|--------|
| Variants v2 | `can_reference_canonically_now` (PROMOTE_CODE done) |
| Components v2 | `can_reference_canonically_now` (components_json + registry) |
| Output blocks v2 | `can_reference_canonically_now` (PROMOTE_CODE done) |
| Form contract v2 | `can_reference_canonically_now` (modular form bindings) |
| Task rules v2 | `needs_owner_decision` |
| Non-v2 templates | `blocked_by_data_model` / PROMOTE_CODE per template |
| Readiness dossier.approved gate | `needs_owner_decision` |

## Forbidden in this task

- DB migration, seed, pricing, Intake router redesign, Dossier CRUD rewrite, RBAC, runtime, snapshots rewrite.
