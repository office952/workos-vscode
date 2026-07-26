# 2026-07-19 — Segmented background operator confirmation path

| Field | Value |
|-------|-------|
| Date | 2026-07-19 |
| Branch | `feature/product-system-active-path-isolation-v1` |
| HEAD initial | `7eaa093` |
| Scope | Analyzer proposal → operator confirm/reject → finish_setup persist → PD/Aggregate read-back |
| GO | Analyzer + minimal UI + finish_setup + tests + screenshots — **no** pricing/Execution/DB migration |

## Research tracks

| Track | Agent | Result |
|-------|-------|--------|
| Analyzer proposal | [Analyzer](6101dadc-ae78-4de0-b1a8-847dc1aa0407) | Closed contours exist; propose unused; hook after Contur suport |
| finish_setup / UI host | [Persist UI](eac1f23e-f6c5-4eba-9042-fbcf260fd329) | Review beside ACP modules; PUT finish-setup |

## Selected integration path

1. FE `proposeSegmentedBackgroundFromCandidates` after Contur suport association (PROPOSED only).  
2. `IntakeV6SegmentedBackgroundPanel` on Review.  
3. Confirm/Reject → `finish_setup.segmented_background` via existing PUT.  
4. BE `persist_segmented_background_on_finish` normalizes + blocks illegal CONFIRMED.  
5. PD rebuild keyed on segmented truth; Aggregate projection informational `future_task_intent` only.

## API / UI paths

```
WRITE: PUT /api/v1/intake-v6/workspaces/{id}/finish-setup
READ:  GET /api/v1/intake-v6/workspaces/{id}
PD:    GET /api/v1/product-system/product-definition/{template}?workspace_id=
AGG:   GET /api/v1/product-system/aggregate/{template}?workspace_id=
UI:    Intake V6 Review — IntakeV6SegmentedBackgroundPanel
```

## Files changed

- Backend: schema field, confirm/reject/persist service, finish_setup hook, PD marker, tests
- Frontend: segmentedBackground helpers, panel, SvgAnalyzer propose, Review wire, tests
- Docs/QA: screenshots + this worklog + MIXED messages already aligned

## Tests

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_acm_segmented_background_v1.py tests/test_acm_segmented_background_confirmation_path_v1.py -q

cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/lib/intakeV6/segmentedBackground.test.ts src/components/workos/intake-v6/IntakeV6SegmentedBackgroundPanel.test.tsx
```

Results: **24** backend + **10** frontend passed.

## Screenshots

`docs/qa/segmented-background-confirmation-2026-07-19/screenshots/`

## Runtime proof

- Proposal → zero PD `segmented_background`  
- Reject → REJECTED, zero confirmed  
- Confirm → PD + Aggregate with panels/bindings  
- Cutout/insert CONFIRMED write → HTTP 422 / ValueError blockers  
- Applied crossing → allowed + two-stage  
- `future_task_intent_authority: INFORMATIONAL_ONLY` (not parallel task source)

## Deferred

- Live browser E2E with Desktop SVG fixtures on running stack  
- Rich element-binding auto from letter centroids  
- Finish Contract / 220V / Oracal / Execution

## Next step

One coherent build: **live Intake E2E with Desktop SVG fixtures** (proposal → confirm → reload) still without pricing/Execution — OR **Finish Contract shell** if owner prefers finish truth next.
