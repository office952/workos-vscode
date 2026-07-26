# Final Report — PRODUCT_SYSTEM_ACTIVE_PATH_ISOLATION_V1_COMPOUND

**Date:** 2026-07-14  
**Worktree:** `C:\w\psiso`  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Candidate HEAD:** `9366a74` (+ uncommitted implementation)  
**Accepted base HEAD:** `82a713e`

---

## 1. Verdict

**`COMPOUND_COMPLETE`**

---

## 2. Reusable lessons captured

Consolidated in `.compound-engineering/product-system-active-path-isolation-v1/compound-knowledge.md` — answers all 12 compound questions, workstreams A–H, proven/partial/not-proven distinctions, fixture/Figma/multitasking guardrails.

---

## 3. Canonical identity pattern

- **Read:** `resolve_template_identity()` — trim/case normalization, legacy read bridge with explicit metadata
- **Write/compile:** `require_canonical_template_code()` — reject legacy alias (422), unknown (404), no silent fallback
- **Surfaces:** all Product System compilation routers + Quote Snapshot V2

---

## 4. Dossier authority pattern

- V2 pilot: dossier = metadata/provenance/inspection only
- Behavior fields gated by `dossier_consumption_policy.py`
- Letters V2 variants/output blocks from canonical contract service
- Non-V2 legacy bridge documented in readiness/intake fallbacks — **not** repo-wide isolation

---

## 5. Modularity and ownership pattern

Product Template composes; components own component truth; ProductAggregate = technical graph; ProductDefinition composes from form contracts. ACM standalone builder; Premount aggregate-only until form contract.

---

## 6. Runtime/fixture pattern

Healthy stack ≠ populated fixtures. Seed via explicit `DATABASE_URL`, backup, pre/post counts, one owner. Snapshot rows not fabricated. Accept `PARTIAL_BLOCKED_BY_SNAPSHOT_RUNTIME_DATA` when static boundary is correct.

---

## 7. Tooling pattern

ASCII-safe PowerShell strings; parser validation before runtime; remove stale deprecated-route checks; preserve health + OpenAPI fetch/parse; never restore dead Intake V3 routes to green readiness.

---

## 8. Figma pattern

Read-only MCP; exact file/node; Figma = UI reference; runtime screenshot mandatory; classify functional vs cosmetic drift; `NO_RELEVANT_FIGMA_FRAME` when absent.

---

## 9. Multitasking pattern

One worktree, one impl/DB/runtime owner each; parallel read-only analysts; AWAIT ALL; single coordinator synthesis; no concurrent file edits; no duplicate stacks.

---

## 10. Proven vs partial vs not proven

| Tier | Items |
|------|-------|
| **Proven** | V2 identity boundary, legacy write rejection, V2 dossier metadata-only, ACM/Premount policy, runtime stability post-seed, catalog/detail proof, Figma+screenshots |
| **Static/partial** | Snapshot runtime chain, Premount ProductDefinition, FE parity, full commercial E2E, Dossier studio list |
| **Not proven** | Repo-wide dossier isolation, all non-V2 templates, complete WorkOS E2E, production/mobile/materialization |

---

## 11. Remaining roadmap

1. Scoped commit (this branch)  
2. FE Premount catalog parity (`activeTemplateScope`)  
3. Premount form contract / ProductDefinition  
4. Snapshot V2 fixture build  
5. Cost → Offer → Order → Execution real-case proof  
6. Non-V2 canonical promotion (deliberate, per-template)

---

## 12. Include list (staging recommendation — owner action)

### Backend implementation

- `backend/services/template_architecture_scope.py`
- `backend/services/template_usage_mode_policy.py`
- `backend/services/dossier_consumption_policy.py`
- `backend/services/canonical_template_contract_service.py`
- `backend/data/canonical_template_variants_volumetric_v2.py`
- `backend/data/canonical_output_blocks_volumetric_v2.py`
- `backend/services/product_aggregate_service.py`
- `backend/services/product_definition_builder_service.py`
- `backend/services/output_blocks_renderer_service.py`
- `backend/services/mini_module_registry_service.py`
- `backend/services/intake_v4_template_option_contract_service.py`
- `backend/services/intake_v5_service.py`
- `backend/services/intake_v6_template_option_contract_service.py`
- `backend/services/quote_output_composition_service.py`
- `backend/services/product_readiness_service.py`
- `backend/services/product_system_template_readiness_service.py`
- `backend/services/acm_quote_input_helpers.py`
- `backend/schemas/intake_v4.py`, `backend/schemas/intake_v6.py`
- Routers (in commit `9366a74`): aggregate, product-definition, mini-modules, cost-bom, commercial_price, EIC, quote_snapshot_v2

### Tests

- `backend/tests/test_product_system_identity_boundary.py`
- `backend/tests/test_template_architecture_scope.py`
- `backend/tests/test_dossier_consumption_policy.py`
- `backend/tests/test_dossier_true_isolation.py`
- `backend/tests/test_product_aggregate_dossier_gating.py`
- `backend/tests/test_intake_v6_option_contract_dossier_gating.py`

### Tooling

- `scripts/start-dev.ps1`

### QA / evidence (selected)

- `docs/qa/product-system-active-path-isolation-v1/RUNTIME_PROOF_REPORT.md`
- `docs/qa/product-system-active-path-isolation-v1/01`–`06` screenshots
- Figma reference PNGs (optional)

### Docs / compound closeout

- `docs/worklog/realignment/2026-07-13_product_system_active_path_isolation_v1.md`
- `.compound-engineering/product-system-active-path-isolation-v1/compound-knowledge.md`
- `.compound-engineering/product-system-active-path-isolation-v1/decision-log.md`
- `.compound-engineering/product-system-active-path-isolation-v1/risk-register.md`
- `.compound-engineering/product-system-active-path-isolation-v1/final-report.md` (this file)
- Selected research/verification artifacts (owner discretion — not entire research dump)

---

## 13. Exclude list

- `backend/dev.db`, all DB backups (`*.pre-*.db`)
- `.cursor/**`
- Local Figma plugin/config
- `backend/logs/**`
- `.compound-engineering/windows-ghost-listener-8000-clear-v1/**`
- Temporary probes: `_post_seed_runtime_probe.py`, `_post_seed_probe_out.json`, `_snapshot_tables_probe.py`, `_runtime_db_probe.py`
- Secrets / `.env` files
- Unrelated compound folders

---

## 14. Files changed (compound task only)

| File | Action |
|------|--------|
| `.compound-engineering/product-system-active-path-isolation-v1/compound-knowledge.md` | Rewritten (closeout) |
| `.compound-engineering/product-system-active-path-isolation-v1/decision-log.md` | Appended |
| `.compound-engineering/product-system-active-path-isolation-v1/risk-register.md` | Updated |
| `.compound-engineering/product-system-active-path-isolation-v1/final-report.md` | Replaced (compound closeout) |
| `docs/worklog/realignment/2026-07-13_product_system_active_path_isolation_v1.md` | Appended |

---

## 15. Application code changed

**NO**

---

## 16. DB mutated

**NO**

---

## 17. Ready for owner commit GO

**YES** — with §12/§13 staging discipline.

---

## 18. Recommended next shortcut

```
/ce-commit
```

(Do not invoke automatically.)

---

## Roadmap awareness checkpoint

| Metric | Value |
|--------|-------|
| Roadmap awareness | **9/10** |
| Current position | Closeout before scoped commit; before broader E2E composition |
| Dead pieces | Intake V3 gate removed; no dead routes restored |
| Forbidden scope respected | **YES** |
| Direction alignment | **93/100%** |

---

## Delivery footer

| Field | Value |
|-------|--------|
| Task | `PRODUCT_SYSTEM_ACTIVE_PATH_ISOLATION_V1_COMPOUND` |
| Worktree | `C:\w\psiso` |
| Branch | `feature/product-system-active-path-isolation-v1` |
| Candidate HEAD | `9366a74` |
| Accepted HEAD | `82a713e` |
| Code-review verdict | `APPROVE_WITH_NON_BLOCKING_FOLLOWUPS` |
| Application code changed | **NO** |
| DB mutated | **NO** |
| Runtime started | **NO** |
| Compound complete | **YES** |
| Ready for owner commit GO | **YES** |
| Recommended next shortcut | `/ce-commit` |
| Verdict | **`COMPOUND_COMPLETE`** |
