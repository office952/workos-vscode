# Intake V6 workspace 404 stale-id audit + loader error classification

## 1. Context

Scope:
- reproduce and classify Intake V6 workspace 404s around `/intake-v6/IR-MR42Q8RI/operator`
- audit stale workspace id propagation across loader, route changes, autosave/sync, and preview hooks
- apply only a small safe fix with no UI/UX redesign
- do not reopen ReviewStep stabilization except for remaining stale refetch behavior

Baseline preserved:
- ReviewStep still uses domain-based refresh
- finish-save hydration remains separated through `FINISH_SETUP_PERSIST_SUCCESS`
- analyzer state is not rehydrated after finish save
- Product Truth remains canonical; Pricing Registry is not used as a repair layer

## 2. DevTools 404 table

| Scenario | Method | URL | Status | Moment | Repeated? | Result |
| --- | --- | --- | --- | --- | --- | --- |
| Requested route current data | POST | `http://127.0.0.1:8005/api/v1/intake-v6/workspaces/ensure-for-intake-request` | 200 | initial load of `/intake-v6/IR-MR42Q8RI/operator` | no | route resolves successfully |
| Requested route current previews | GET | `.../workspaces/187e351c-0bde-448d-b764-58bf2456ae06/{product-system-binding,material-breakdown,nesting-preview,pricing-input-preview,priced-quote-dry-run,quote-handoff-preview}` | 200 | after ensure resolves | no | current workspace previews load |
| Direct missing workspace route | GET | `http://127.0.0.1:8005/api/v1/intake-v6/workspaces/00000000-0000-4000-8000-000000000000` | 404 | initial load of direct UUID route | no | classified as workspace missing/stale |
| SPA transition old to new route | POST/GET | old `111677e0-c867-41b7-91a4-f77e1d921a35` before route mark; new `187e351c-0bde-448d-b764-58bf2456ae06` after route mark | 200 | old route load, then History API route change to `IR-MR42Q8RI` | no stale 404 after route mark | no contamination observed after fix |

No reproducible 404 was observed on `/intake-v6/IR-MR42Q8RI/operator` after the fix. The only confirmed direct workspace GET 404 in this run was the intentionally missing UUID route used to validate the classifier.

## 3. Workspace ids observed

| Route / Source | Observed workspace id | Workspace code | Status |
| --- | --- | --- | --- |
| `/intake-v6/IR-MR42Q8RI/operator` | `187e351c-0bde-448d-b764-58bf2456ae06` | `IV6-1A59D22C` | current/resolved |
| `/intake-v6/IR-MR2MP11C/operator` | `111677e0-c867-41b7-91a4-f77e1d921a35` | `IV6-4BBFDDD2` | previous route during SPA transition test |
| `/intake-v6/00000000-0000-4000-8000-000000000000/operator` | `00000000-0000-4000-8000-000000000000` | none | missing/stale direct workspace id |

## 4. Workspace current vs workspace stale

Current for the requested route:
- route key: `IR-MR42Q8RI`
- resolved workspace id: `187e351c-0bde-448d-b764-58bf2456ae06`
- preview requests after resolution use this id and return 200

Stale/missing class:
- direct UUID route such as `00000000-0000-4000-8000-000000000000` makes `GET /workspaces/{id}` and receives backend `workspace_not_found`
- before the fix, a route change could leave the previous `state.workspace?.id` visible until the new route load completed, allowing preview hooks to start from a stale id

## 5. Frontend source of stale id

Primary source:
- `useIntakeV6Workspace(workspaceId)` kept the old `state.workspace` during `LOAD_START`
- `activeWorkspaceId` and child steps could derive id from `state.workspace?.id`
- ReviewStep uses `const workspaceId = state.workspace?.id` and starts multiple preview effects from that value

Preview/refetch hooks audited:
- product-system binding
- task preview
- material breakdown
- pricing input preview
- priced quote dry run
- production dry run
- AI informational preview
- production handoff preview
- task generation dry run
- order-bound task readiness
- quote handoff preview

These effects already use local `cancelled` flags, so stale responses are not expected to overwrite state after cleanup. The risk was request start on the previous id before the route state was cleared.

Fix applied:
- `LOAD_START` now receives the route `workspaceId`
- when the route key changes, reducer resets to initial loading state and clears old `workspace`, SVG/analyzer state, and stale local flags
- hook always dispatches route-aware `LOAD_START` before cached hydration or remote load
- hook ignores load success/error if `workspaceIdRef.current` no longer matches the request route key

## 6. Backend 404 behavior

Endpoint:
- `GET /api/v1/intake-v6/workspaces/{workspace_id}` in `backend/routers/intake_v6_workspaces.py`

Service behavior:
- `_get_record_or_404(...)` tries exact `id`, then `workspace_code`, then intake request code
- if no record is found, it raises `404` with detail `{ error: "workspace_not_found", workspace_id }`

Ensure behavior:
- `POST /api/v1/intake-v6/workspaces/ensure-for-intake-request`
- if intake request code is missing in source data, it raises `404` with detail `{ error: "intake_request_not_found", intake_request_code }`

No deleted/stale-specific state was found beyond `archived_at` exclusion in lookup-by-intake-code/list paths. Direct id lookup does not currently filter archived workspaces.

## 7. Fix applied or no-fix reason

Applied:
- route-aware `LOAD_START` state reset
- stale request response guard in `useIntakeV6Workspace`
- loader error classification codes in state
- reducer tests for stale route reset and classifier storage

No backend change was needed because backend already returns distinct error details.

## 8. Loader error classification

Implemented classification in `useIntakeV6Workspace`:

| Code | Condition | Meaning |
| --- | --- | --- |
| `INTAKE_REQUEST_NOT_FOUND` | 404 while route key is `IR-*` / `WI-*` and load uses ensure endpoint | intake request code does not exist / cannot be resolved |
| `WORKSPACE_NOT_FOUND` | 404 while route key is direct workspace id/code | workspace id is missing or stale |
| `BACKEND_UNAVAILABLE` | network/fetch/timeout/refused-style error | backend unavailable |
| `UNKNOWN_LOAD_ERROR` | fallback | unexpected load failure |

State now carries `loadErrorCode` separately from the visible `error` message.

## 9. Sync status audit

The visible `Sincronizare automata in asteptare` status is not driven by workspace load requests. It is rendered by `IntakeV6ReviewSaveFooter` from `pendingSave`, which is derived from Review local edits (`selectorPendingSave` / `commercialInputsPendingSave`).

Impact of the fix:
- route changes now clear old workspace/analyzer/local state before the new route resolves
- stale workspace state should no longer keep pending-save UI alive across route keys
- autosave does not remain blocked by a stale workspace id in the loader path

Not changed:
- no visible copy changes
- no autosave policy changes
- no ReviewStep refresh strategy changes

## 10. Tests

Ran:
- `pnpm.cmd --dir frontend exec vitest run src/lib/intakeV6/intakeV6WorkspaceReducer.test.ts` — 13 tests passed
- `pnpm.cmd --dir frontend exec tsc --noEmit --pretty false` — passed; only pnpm config warning
- browser verification on `/intake-v6/IR-MR42Q8RI/operator` — no 404s observed, current workspace previews 200
- browser verification on missing direct UUID route — one GET 404, classified visible message for workspace stale/missing
- browser SPA transition from `IR-MR2MP11C` to `IR-MR42Q8RI` — no stale 404 after route-change mark

## 11. Remaining risks

- user-reported exact stale UUID was not captured in this run, so the fix targets the stale-state mechanism rather than a known persisted bad id value
- other open, unshared browser pages can still emit old 404s independently until reloaded/HMR-applied
- direct archived workspace id behavior is not differentiated from missing workspace id
- preview hooks still use individual effect cancellation rather than a shared request coordinator

## 12. Next safe step

Add a tiny regression test around `useIntakeV6Workspace` itself with mocked API calls:
- render hook with route key A and hydrated workspace A
- rerender with route key B before B resolves
- assert child-visible state has `workspace === null` while B loads
- assert late A response cannot overwrite B state

This would lock the behavior at hook level without touching UI/UX.
