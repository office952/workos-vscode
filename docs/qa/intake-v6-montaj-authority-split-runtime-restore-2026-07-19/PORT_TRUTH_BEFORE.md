# PORT TRUTH BEFORE

## Health

| Port | Health |
|------|--------|
| 8003 | `{"status":"healthy"}` (served by orphan workers / ghost sockets) |
| 8013 | `{"status":"healthy"}` (live uvicorn from `C:\w\psiso\backend`) |

## ACM workspace `3fb7a2b5-ec60-48e4-8b5c-c8649c0c8982`

Shared finish truth (identical `updated_at=2026-07-19T15:37:15.857960` on both ports):

| Field | 8003 | 8013 |
|-------|------|------|
| mounting_scope | none | none |
| mounting_solution | TPL-ACM-BOXED-MOUNTING-SUPPORT_v1 | same |
| mounting_template_enabled | true | true |
| segmented_background.status | CONFIRMED | CONFIRMED |
| ECM status | DRAFT | DRAFT |
| power_supply_service_corner | null | null |

## ProductDefinition difference (code version, not data)

| Field | :8003 (stale) | :8013 (184b9dc) |
|-------|---------------|-----------------|
| solution_status | **blocked** | **confirmed** |
| blockers | **`MOUNTING_SCOPE_INACTIVE`** | `[]` |
| ACM node included | **no** | **yes** (`included=true`) |
| compatibility | blocked | compatible |

## Aggregate difference

| Field | :8003 | :8013 |
|-------|-------|-------|
| conflicts | `COMPOSITION_GRAPH_BLOCKED`, `PROCESS_RESOLVER_SERVICE_CORNER_REQUIRED` | `[]` |

## Evidence :8003 is pre-184b9dc

1. Emits `MOUNTING_SCOPE_INACTIVE` (removed in `184b9dc` composition contract).
2. Omits ACM child from composition graph under scope none.
3. Aggregate still surfaces `PROCESS_RESOLVER_SERVICE_CORNER_REQUIRED` for confirmed multi-panel segmented WS.
4. No living `--port 8003` uvicorn parent — only orphan `spawn_main` workers from dead reload parents.

## Evidence :8013 is 184b9dc

1. Parent launched from `C:\w\psiso\backend\.venv` with `--port 8013`.
2. PD `blockers=[]`, `solution_status=confirmed`, ACM included.
3. Aggregate conflicts empty.
4. Matches unit/runtime proof recorded under authority-split QA pack.

## FE :3000 before restore

Parent chain explicitly `BACKEND_PORT=8013` → FE proxy returns repaired truth (not stale :8003).
