## Risk register — PRODUCT_SYSTEM_ACTIVE_PATH_ISOLATION_V1

### R1 — Breaking historical alias reads (intentional for active compilation routes)

- **Risk**: clients sending `TPL-VOLUMETRIC-LETTERS` to compilation endpoints now get 422.
- **Mitigation**: response includes explicit canonicalization metadata; legacy read bridge remains available via `resolve_runtime_template_code` for explicit migration/read-only callers.

### R2 — Premount capability policy change could surface new offerables

- **Risk**: changing `TPL-METAL-PREMOUNT-STRUCTURE_v1` policy to root offerable affects readiness/capabilities and visibility.
- **Mitigation**: change is code-policy only (no DB), aligns with explicit owner truth in task contract; tested via targeted identity/capability checks.

### R3 — Dossier still consumed by aggregate/readiness

- **Risk**: dossier can still influence aggregate/readiness; this slice adds traceability but not full isolation.
- **Mitigation**: explicit `DOSSIER_CONSUMED` warning emitted in aggregate; tracked as remaining debt for follow-up slice to version-pin or de-authoritize dossier for canonical templates.

