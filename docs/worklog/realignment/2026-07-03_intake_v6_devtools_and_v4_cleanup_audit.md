# Intake V6 DevTools Runtime Audit + V4 Compatibility Cleanup Plan

## 1. Context

Scope for this slice was intentionally narrow:
- extend the confirmed Intake V6 stability baseline with browser DevTools/runtime findings
- separate real runtime issues from naming-only or compat-only V4 residue
- avoid ReviewStep relitigation, UI redesign, or large semantic refactors
- allow only a small safe fix if a concrete DevTools/accessibility issue was localized

Working baseline preserved:
- Intake V6 remains the entry point
- current UI/UX remains in place
- operator confirms, SVG analyzer only suggests
- Product Truth remains canonical
- Pricing Registry does not repair Product Truth gaps
- ConfirmStep semantic refresh is out of scope for this slice

## 2. DevTools Issues Table

| ID | Surface | Symptom | Evidence | Cause | Status |
| --- | --- | --- | --- | --- | --- |
| DT-01 | Intake V6 operator route | `POST /api/v1/intake-v6/workspaces/ensure-for-intake-request` returns 404 | Browser capture on `/intake-v6/IR-MR425S9/operator`; frontend calls `ensure-for-intake-request`; backend route exists | Missing intake request record for route key `IR-MR425S9`, not a missing endpoint and not a proven base-URL bug | Confirmed runtime data issue |
| DT-02 | App-wide dev router config | React Router future flag warning (`v7_startTransition`) | Reproduced on Intake V6 and Quotes pages | Dev-only library warning; current router config has not opted into the future flag | Confirmed dev warning |
| DT-03 | Browser/apple mobile warning | User-reported `apple-mobile-web-app-capable` warning | `frontend/index.html` already includes the meta tag; confirm page inspection also saw the tag at runtime | Warning is not caused by current app HTML omission in this repo; likely stale browser/devtools interpretation or another document context | Not reproducible as app defect |
| DT-04 | Intake V6 Radix sheet accessibility | Missing `Description` / `aria-describedby` warning suspected from Radix overlay content | `IntakeV6LiveCalculationSummary` used `SheetContent` with title plus free text but no `SheetDescription` | Legitimate local accessibility gap in an active Intake V6 sheet | Fixed in this slice |

## 3. 404 Endpoint Table

| Endpoint | Caller | Observed Status | Backend Reality | Assessment |
| --- | --- | --- | --- | --- |
| `/api/v1/intake-v6/workspaces/ensure-for-intake-request` | `ensureIntakeV6WorkspaceForIntakeRequest(...)` in frontend Intake V6 API | 404 for `IR-MR425S9` | Backend `ensure_intake_v6_workspace_for_intake_request(...)` exists and returns 404 when intake request code is missing | Route is valid; failing key is missing from data source |

Notes:
- frontend runtime base is `http://127.0.0.1:8005` via `frontend/.env.local`
- frontend route resolution correctly treats `IR-*` / `WI-*` params as intake-request keys, then calls `resolveIntakeV6Workspace(...)`
- current operator error text is technically accurate for a missing resolved workspace, but it collapses distinct causes into one user-facing message

## 4. Browser Warnings Table

| Warning | Scope | Severity | Current Status | Action |
| --- | --- | --- | --- | --- |
| React Router future flag warning | App-wide dev runtime | Low | Active in dev | Leave for dedicated router upgrade/config slice |
| Apple mobile web app capable warning | Browser/devtools context | Low | Not attributable to current app HTML | No code change in this slice |
| Radix missing description / `aria-describedby` | Active Intake V6 overlay | Medium | Fixed for the identified live-calculation sheet | Keep auditing other dialog/sheet surfaces only when reproduced |

## 5. V4 References Table

| Surface | Example | Runtime Role | Classification | Risk |
| --- | --- | --- | --- | --- |
| Frontend V6 API namespace | `frontend/src/lib/intakeV6/intakeV6Api.ts` re-exports and aliases many `intakeV4Api` contracts | Active on every V6 API call and type surface | Runtime active | High conceptual coupling |
| Frontend V6 display/helper wrappers | `intakeV6OperatorUiDisplay.ts`, `intakeV6ConfirmSummary.ts`, `intakeV6FaceFinishOptions.ts` | Active helper layer used by current V6 UI | Compat wrapper internals | Medium |
| Frontend finish hydration namespace | `intakeV6FinishHydration.ts` | Active in ReviewStep hydration path | Compat wrapper internals | Medium |
| Backend public schema namespace | `backend/schemas/intake_v6.py` aliases a large V4 schema set | Active contract boundary for V6 routes | Runtime active | High conceptual coupling |
| Backend finish truth namespace | `backend/services/intake_v6_finish_truth_service.py` | Active service boundary | Compat wrapper internals | Medium |
| Backend material breakdown namespace | `backend/services/intake_v6_material_breakdown_service.py` calling V4 builder then normalizing | Active preview runtime | Runtime active | High |
| Backend commercial quote namespace | `backend/services/intake_v6_commercial_quote_service.py` using V4 draft/snapshot builders and migrating legacy linkage | Active quote runtime | Runtime active | High |
| Backend response normalization | `backend/services/intake_v6_response_normalization.py` string-replaces `V4` into `V6` | Active post-processing layer | Compat wrapper internals | Medium to high due to masking |
| Frontend tests with direct V4 imports | `intakeV6ArtworkOnlyGuard.test.ts` imports V4 helpers directly | Test-only | Historical/test compat | Low production risk |

## 6. Classification of V4 Residue

### A. Runtime active in V6
- `frontend/src/lib/intakeV6/intakeV6Api.ts`
- `backend/schemas/intake_v6.py`
- `backend/services/intake_v6_material_breakdown_service.py`
- `backend/services/intake_v6_commercial_quote_service.py`
- any V6 flow whose authoritative payload shape is still `IntakeV4*` under alias

Meaning:
- this is not just naming debt; V6 runtime behavior is still materially delegated to V4 contracts/builders
- these are the dangerous surfaces because they keep V4 as the active mental model behind V6

### B. Compat / legacy wrapper internals
- `frontend/src/lib/intakeV6/intakeV6ConfirmSummary.ts`
- `frontend/src/lib/intakeV6/intakeV6OperatorUiDisplay.ts`
- `frontend/src/lib/intakeV6/intakeV6FaceFinishOptions.ts`
- `frontend/src/lib/intakeV6/intakeV6FinishHydration.ts`
- `frontend/src/lib/intakeV6/intakeV6FinishPayloadSync.ts`
- `backend/services/intake_v6_finish_truth_service.py`
- `backend/services/intake_v6_response_normalization.py`

Meaning:
- these can remain temporarily if quarantined behind V6 names and documented as adapters
- they should not leak V4 semantics upward into operator-facing reasoning or new feature design

### C. Historical / test-only
- `frontend/src/lib/intakeV6/intakeV6ArtworkOnlyGuard.test.ts` direct V4 imports
- older compat wording in legacy-focused tests already adjusted in prior cleanup slices

Meaning:
- these are not production runtime blockers, but they keep V4 visible in developer cognition

### D. Dead / removable without proof of runtime need
- none newly proven dead in this slice beyond test-historic direct V4 imports

Meaning:
- this slice did not justify blind deletion
- the right move is quarantine first, then removal when call sites are cut over

## 7. Fixes Applied

Small safe fix applied:
- added `SheetDescription` to the active Intake V6 live-calculation details sheet in `frontend/src/components/workos/intake-v6/IntakeV6LiveCalculationSummary.tsx`
- this preserves existing text and behavior, but satisfies the Radix accessibility contract more explicitly

## 8. What Was Not Modified

Not changed in this slice:
- no ConfirmStep semantic refresh
- no ReviewStep stabilization changes
- no router future-flag configuration change
- no route/base-URL rewrite for `ensure-for-intake-request`
- no broad V4 rename sweep
- no schema/service refactor to replace active V4 runtime dependencies

## 9. Remaining Risks

- V6 still depends on V4 types as runtime truth in both frontend and backend namespace boundaries
- response normalization by string replacement can hide semantic drift instead of removing it
- operator route error handling still merges multiple 404 causes into a single generic missing-workspace message
- additional dialog/sheet accessibility warnings may still exist outside the localized live-calculation sheet if other overlays open without description components
- React Router future warning will continue to pollute DevTools until a dedicated router-config slice handles it

## 10. Smart Plan to Eliminate V4

Principle:
- eliminate V4 as the active mental model inside Intake V6 by tightening V6-owned boundaries first, not by mass-renaming files

Recommended order:
1. Freeze the public V6 boundary.
   - stop expanding `intakeV6Api.ts` as a re-export umbrella for `intakeV4Api`
   - define V6-owned exported types for the subset actually consumed by current V6 UI
2. Quarantine compat adapters.
   - move V4-backed helpers into clearly named adapter buckets such as `compat/` or `legacy/`
   - keep V6-facing imports stable while making compat explicit internally
3. Replace schema aliases at the backend boundary.
   - start with the highest-churn contracts used by active previews: workspace, pricing preview, breakdown, quote handoff
   - keep internal V4 builders temporarily, but stop exporting raw `IntakeV4*` aliases as the V6 public schema surface
4. Remove string-replace normalization as a semantic bandage.
   - convert the highest-risk preview responses into V6-native mappers with explicit field ownership
5. Clean test cognition last.
   - after runtime boundaries are cleaner, update or isolate tests that still import V4 helpers directly

## 11. Next Safe Micro-Slice

Recommended next micro-slice:
- split Intake V6 route-load 404 handling into distinct frontend messages for:
  - missing intake request code on `ensure-for-intake-request`
  - missing workspace id on direct workspace fetch
- keep the current route logic and backend behavior unchanged
- output should remain UI-neutral: just more truthful error classification plus a focused test around the loader error mapping

Why this slice first:
- it improves runtime truth immediately
- it reduces DevTools ambiguity around the confirmed 404
- it does not reopen ReviewStep or require V4 runtime surgery
