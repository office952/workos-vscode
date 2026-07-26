# Worklog — ACP face-treatment authority + FinishSetup persistence foundation

| Field | Value |
|-------|-------|
| Date | 2026-07-18 |
| GO | `GO_FIX_ACP_MIXED_FACE_AUTHORITY_AND_PERSISTENCE_FOUNDATION` |
| Branch | `feature/product-system-active-path-isolation-v1` |
| HEAD before | `e7082c2` |
| Audit docs commit | `3b93a42` |
| HEAD after foundation | `bd3fae5` (approx; see git log) |

## What shipped

1. Face-treatment registry `acp_face_treatment/v1`
2. Geometry roles: `CUTOUT_TEXT`, `CUTOUT_LOGO`, `ACRYLIC_INSERT`
3. ACM shell capabilities: `boxed_acp_shell`, `local_face_treatments`
4. FinishSetup binding fields: `local_zone_id`, `face_treatment_code`, confirmation, provenance, local_configuration_status
5. PD nested `face_treatment_instances` + readiness summary
6. Legacy LIGHT-ROUTED rejected as V6 binding authority (`PARALLEL_LEGACY_COST_PATH`)
7. No CPP / tasking / Execution / schema migration / seed

## Backend restart proof

| Item | Value |
|------|-------|
| Old stale | PID 14152 ghost + orphan spawn; OpenAPI lacked `mounting_fixing_system` |
| Action | `taskkill` process tree; `npm run dev:backend` |
| New listen | PID 9200 reloader — `uvicorn main:app --host 127.0.0.1 --port 8001 --reload` |
| Health | `{"status":"healthy"}` |
| OpenAPI | `IntakeV4FinishSetup` includes `svg_component_bindings`, `mounting_fixing_system` |

## Runtime proof

- Unit/in-process normalize + PD projection PASS
- HTTP `PUT/GET` FinishSetup mixed-face (`test_http_mixed_face_finish_setup_save_and_refresh`) PASS
- FE vitest + `pnpm build` PASS
- No full Step 1/2 UI treatment editor (contract-first; not required for foundation)

## UI

Contract-first — no new Step 2 editors. FE types + upsert identity fixed so multiple ACM treatments coexist.

## Aggregate

No BOM/process projection.

## Roadmap checkpoint

Stops at: face-treatment authority + persistence foundation.  
Next safe step: **STOP FOR OWNER RUNTIME REVIEW** (or Option 1 local face modules after owner GO).
