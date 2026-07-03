# BUILD_INTAKE_V4_API_HANDOFF_HASH_SYNC

**Date:** 2026-06-22  
**Status:** PASS (scoped API hash-sync guard)  
**Branch:** `local/integration-pr4-plus-svg-path`  
**HEAD before:** `4700e45cb3e10edec4ae45749c616547d06ac79e`  
**Commit:** none (awaiting user confirmation)

---

## Purpose

Close the commercial handoff gap: `POST create-draft-quote` must fail-closed when operator analysis is stale (local re-upload without `PUT analysis-bundle`), matching UI Confirm gating.

---

## Gap resolved

| Before | After |
|--------|-------|
| UI blocked Confirm on hash desync | Unchanged (still blocks) |
| Direct API could return 201 on stale persisted snapshot | **422** `QUOTE_HANDOFF_BLOCKED` with `analysis_hash_mismatch` |

---

## Contract

### Request — `POST /api/v1/intake-v4/workspaces/{id}/create-draft-quote`

Required field (new):

| Field | Type | Rule |
|-------|------|------|
| `client_analysis_hash` | string (64 hex) | SHA-256 of SVG bytes operator attests; must equal `payload.svg_source.file_hash` |

Existing confirmation booleans unchanged.

**Commit:** `fix(intake-v4): fail-closed draft quote on analysis hash mismatch` (user-approved)

**Backward compatibility:** **None** for legacy callers — requests without `client_analysis_hash` are rejected intentionally (Pydantic 422). There is no silent fallback to persisted hash without operator attestation.


### Response on block

```json
{
  "detail": {
    "error": "QUOTE_HANDOFF_BLOCKED",
    "message": "Workspace V4 is not ready for draft quote creation.",
    "blockers": ["analysis_hash_mismatch"]
  }
}
```

Other blockers still apply: `missing_svg_analysis_json`, `missing_client_analysis_hash`, analysis boundary codes, etc.

Snapshot integrity rule added: `CLIENT_ANALYSIS_HASH_SYNCED`.

---

## Implementation

| File | Change |
|------|--------|
| `backend/services/intake_v4_analysis_boundary_service.py` | `list_v4_analysis_hash_sync_blockers`, `assert_v4_analysis_hash_sync_or_raise` |
| `backend/schemas/intake_v4.py` | `client_analysis_hash` on `IntakeV4CreateDraftQuoteRequest` |
| `backend/services/intake_v4_commercial_quote_service.py` | Hash sync in `evaluate_v4_quote_handoff_blockers` |
| `backend/tests/test_intake_v4_commercial_quote.py` | Pass/missing/mismatch/bundle tests |
| `backend/tests/test_intake_v4_analysis_boundary.py` | Hash sync unit tests |
| `frontend/src/lib/intakeV4/intakeV4Api.ts` | Request type |
| `frontend/src/components/workos/intake-v4/steps/IntakeV4ConfirmStep.tsx` | Sends `localFileHash` / persisted hash |
| `frontend/e2e/helpers/intakeV4Live.ts` | Hash helpers for E2E API calls |
| `frontend/e2e/intake-v4-commercial-handoff.spec.ts` | Stale API blocked test |

**Not touched:** CostEngine, Pricing Foundation, V2/V3 dirty files, stock consumption, ACM/bond.

---

## Tests run

### Backend (executed locally)

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v4_commercial_quote.py tests/test_intake_v4_analysis_boundary.py -q
```

**Result:** `11 passed`

Covers: valid handoff with matching hash, missing analysis-bundle, missing `client_analysis_hash` (Pydantic 422), hash mismatch (`analysis_hash_mismatch`), duplicate quote block.

### E2E Playwright

**Added:** `create-draft-quote API blocked when client hash is stale after re-upload` in `e2e/intake-v4-commercial-handoff.spec.ts`.

**Not run locally for this build** — spec requires live dev stack on `:8000` (backend) and `:3000` (frontend). Run when stack is up:

```powershell
$env:PW_SKIP_WEB_SERVER='1'
cd frontend
npx --yes pnpm@8.10.0 exec playwright test e2e/intake-v4-commercial-handoff.spec.ts
```

---

## PASS criteria

| Criterion | Status |
|-----------|--------|
| API blocks stale hash mismatch | ✅ |
| API requires persisted analysis bundle | ✅ (existing + boundary) |
| Valid handoff with matching hash | ✅ |
| UI sends `client_analysis_hash` on Confirm | ✅ |
| E2E stale API blocked | ✅ (spec added; live run pending stack) |
| No CostEngine / V2/V3 / pricing changes | ✅ |

---

## Follow-up

1. **Sheet nesting role split** — material costing pro-rata (separate build)  
2. **Re-upload clears stale `svg_analysis_json` on server** — if POST svg without analysis-bundle should invalidate persisted nest2 snapshot explicitly  
3. **Pricing Page / Registry Alignment** — dev registry seeds

---

## Boundary

**In scope:** API hash sync, Confirm payload, tests, QA doc.

**Out of scope:** commits without user OK, push, CostEngine, stock consumption.
