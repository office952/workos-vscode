# UI-TRUTH-01A — Runtime Truth Contract and Health Hook V1

**Task:** `UI-TRUTH-01A` / `RUNTIME_TRUTH_CONTRACT_AND_HEALTH_HOOK_V1`  
**Starting HEAD:** `92f19fe`  
**Owner GO:** YES  
**Verdict:** `UI_TRUTH_01A_RUNTIME_TRUTH_FOUNDATION_PASS`  
**Date:** 2026-07-15

## Scope delivered

Frontend-only foundation for `AUTH_BACKEND_DB_ENV_SEPARATED` — **no banner visual changes**.

| Deliverable | Path |
|-------------|------|
| Types | `frontend/src/types/runtimeStatus.ts` |
| Normalizers + fetch | `frontend/src/lib/runtimeHealth.ts` |
| Hook | `frontend/src/hooks/useRuntimeHealth.ts` |
| Tests | `runtimeHealth.test.ts` (26), `useRuntimeHealth.test.ts` (15) |

## Hook contract

- Same-origin: `/api/v1/system/health`, `/api/v1/system/version`
- Poll: 45s; stale: 120s; timeout: 6s
- Manual refresh; visibility refresh; AbortController cleanup
- Diagnostics: opt-in `fetchDiagnostics: false` default; 403 does not mark backend down
- Mock: environment `demo` only — never healthy backend fallback

## Verification

| Check | Result |
|-------|--------|
| Tests | **41/41 PASS** |
| Frontend build | **PASS** |
| EnvironmentBanner unchanged | **YES** (no `useRuntimeHealth` import) |
| Intake | **200** |
| DB writes | **0** |
| Parity | **ALL_FALSE** |

## Next

**UI-TRUTH-01B** — Banner rendering and Romanian terminology (not auto-started).  
**APP-AUTH-06C** — BLOCKED.

## Evidence

`docs/qa/product-system-active-path-isolation-v1/ui_truth_01a/`

## DELIVERY FOOTER

```
Task: UI-TRUTH-01A
Owner GO: YES
Runtime truth types: PASS
Health normalizer: PASS
Environment normalizer: PASS
Diagnostics boundary: PASS
DB empty checks: UNKNOWN
Same-origin health: YES
Direct backend URL: NO
Polling: 45000ms
Stale: 120000ms
Manual refresh: YES
Timeout: 6000ms
Tests: 41 PASS / 0 FAIL
Frontend build: PASS
Banner visual: UNCHANGED
Implementation authorized: UI-TRUTH-01A ONLY
Next: UI-TRUTH-01B
Verdict: UI_TRUTH_01A_RUNTIME_TRUTH_FOUNDATION_PASS
```
