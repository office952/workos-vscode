## Risk register — PRODUCT_SYSTEM_ACTIVE_PATH_ISOLATION_V1

### R1 — Breaking historical alias reads (intentional for active compilation routes)

- **Risk**: clients sending `TPL-VOLUMETRIC-LETTERS` to compilation endpoints now get 422.
- **Mitigation**: response includes explicit canonicalization metadata; legacy read bridge remains available via `resolve_runtime_template_code` for explicit migration/read-only callers.

### R2 — Premount capability policy change could surface new offerables

- **Risk**: changing `TPL-METAL-PREMOUNT-STRUCTURE_v1` policy to root offerable affects readiness/capabilities and visibility.
- **Mitigation**: change is code-policy only (no DB), aligns with explicit owner truth in task contract; tested via targeted identity/capability checks.

### R3 — Dossier still consumed on non-V2 / legacy paths (accepted)

- **Risk**: non-canonical templates and readiness fallbacks may still read dossier behavior fields.
- **Status**: **ACCEPTED** as documented legacy bridge — not repo-wide isolation claim.
- **Mitigation**: `dossier_consumption_policy.py` gates V2 pilot surfaces; aggregate emits `DOSSIER_METADATA_ONLY` for canonical templates; compound closeout documents boundary explicitly.

### R4 — Dev-stack backend “ready” gate is stricter than `/health` (mitigated)

- **Risk**: `npm run dev:stack` could report backend failure even when `/health` and `/openapi.json` return HTTP 200, because readiness required deprecated Intake V3 OpenAPI paths absent from active router registration.
- **Mitigation:** `PRODUCT_SYSTEM_DEV_READINESS_GATE_STALE_INTAKE_V3_FIX_V1` removed the three stale path requirements. Readiness now requires health success + OpenAPI fetch/parse only (`STALE_LEGACY_PATH_CHECK_REMOVED`). Re-run single-stack runtime proof to confirm frontend starts.

### R5 — `start-dev.ps1` parser failure blocked runtime (mitigated)

- **Risk**: Unicode em-dash in diagnostics catch string caused PowerShell `ParserError`; stack could not start.
- **Mitigation**: owner-approved ASCII-only fix on line 170 (`PARSER_FIX_ONLY`). Re-validate with `-NoProfile` parser before next `/ce-debug` attempt.

### R6 — Empty local dev.db blocks V2 pilot runtime proof (mitigated)

- **Risk**: `npm run dev:stack` succeeds but runtime proof cannot demonstrate catalog, capability truth, dossier authority without seeded rows.
- **Status**: **MITIGATED** by Phase 2 `seed_sync_all` (2026-07-14, `FIXTURE_ACTIVATION_PASS`); POST SEED proof `PASS_V2_PILOT_WITH_LEGACY_BRIDGE`.
- **Residual**: Snapshot V2 chain still unseeded (see R7).

### R7 — Snapshot V2 fixture seed absent (active)

- **Risk**: Even after `seed_sync_all`, runtime proof for snapshot/execution identity may remain `PARTIAL_BLOCKED_BY_SNAPSHOT_RUNTIME_DATA` because no repo-owned seed populates `quote_snapshots_v2` + `orders.snapshot_v2_json` + ExecutionPlan V2 preview chain.
- **Evidence**: Fixture audit — production seeds stop at catalog/pricing registries; V2 chain exists only in pytest helpers (`test_execution_plan_v2_preview._seed_v2_order_with_snapshot`).
- **Mitigation**: Accept partial snapshot verdict for pilot, or owner GO for a future dedicated V2 snapshot fixture build (not invented in audit task).

### R8 — DATABASE_URL mis-target during seed (active)

- **Risk**: `AGENTS.md` E2E example uses `C:/Users/offic/workos/backend/dev.db`; running seed without overriding `DATABASE_URL` could write main workspace DB.
- **Mitigation**: Fixture audit mandates explicit `sqlite+aiosqlite:///C:/w/psiso/backend/dev.db` before owner GO; compound closeout repeats rule in `compound-knowledge.md`.

### R9 — Premount catalog list visibility (open, non-blocking)

- **Risk**: `TPL-METAL-PREMOUNT-STRUCTURE_v1` is offerable in API/template-availability but absent from operational catalog cards while ACM/Letters appear.
- **Root cause**: `frontend/src/lib/activeTemplateScope.ts` omits Premount from `OWNER_VALID_ACTIVE_TEMPLATE_CODES` despite backend `ROOT_OFFERABLE_TEMPLATE_CODES`.
- **Evidence**: Code review F-01/F-02; POST SEED UI — direct URL/detail PASS; list filter gap.
- **Mitigation**: Dedicated FE parity build; **does not block commit** per final review rules.

### R10 — Blueprint Dossier studio list wiring (open, non-blocking)

- **Risk**: Entity API returns 4 approved dossiers but `/product-system/blueprint-dossier` shows Active (0) when `productTemplatesApi.list()` is empty.
- **Mitigation**: Admin inspect via entity API; operator readonly tab works; follow-up UI wiring — **does not block commit**.

### R11 — FE/backend parity drift on root offerable set (open, non-blocking)

- **Risk**: Future agents assume FE `BACKEND_ROOT_OFFERABLE_TEMPLATE_CODES_PARITY` matches backend policy; currently stale (missing Premount).
- **Mitigation**: Document in `compound-knowledge.md`; update FE constants in follow-up build or add CI parity test.

### Compound closeout status (2026-07-14)

- **Code review**: `APPROVE_WITH_NON_BLOCKING_FOLLOWUPS`
- **Compound**: `COMPOUND_COMPLETE`
- **Commit blockers**: none (P0/P1 = 0)
- **Owner commit GO**: YES with staging exclude list

