# RUNTIME-CONFIG-03 — Canonical startup port alignment and restart proof

**Task:** `RUNTIME-CONFIG-03` — `CANONICAL_STARTUP_PORT_ALIGNMENT_AND_RESTART_PROOF_V1`  
**Date:** 2026-07-15  
**Starting HEAD:** `757d6fd`  
**Verdict:** `RUNTIME_CONFIG_03_CANONICAL_STARTUP_ALIGNMENT_PASS`

## Owner P1–P10 confirmation

Owner explicitly confirmed in chat (recorded, not deferred):

- **P1 A** — parity signal useful observe-only  
- **P2 A** — duplicate volume acceptable ephemeral  
- **P3 CONFIRMED** — ACTIONABLE split into 6 classes  
- **P4 A** — Sandu read-only  
- **P5 A** — two consumers frozen  
- **P6 DEFER** — catalog API  
- **P7 A** — no persistence  
- **P8 A** — no manager projection  
- **P9 CONFIRMED** — parity flags false  
- **P10 AMENDED** — RUNTIME-CONFIG-03 → UI-TRUTH-01 → APP-AUTH-06C  

Evidence: `owner_decision_04_confirmation.json`, updated `owner_decision_04/owner_decision_package.json`

## Root cause closure

RUNTIME-RECOVERY-02 proved `WRONG_PROXY_TARGET`: Vite default `8000` while canonical backend `8001`. This task aligns launchers and Vite default so **no manual `BACKEND_PORT` is required**.

## Canonical contract

```
Backend:   127.0.0.1:8001
Frontend:  127.0.0.1:3000
API:       same-origin /api
Proxy:     http://127.0.0.1:8001
DB:        C:\w\psiso\backend\dev.db
Parity:    ALL_FALSE (cleared at launcher start)
```

Implementation: `scripts/_workos-dev-contract.ps1`

## Owner start command

```powershell
npm run dev:stack
```

Equivalent: `.\scripts\dev.ps1` (Windows). Split: `npm run dev:backend` + `npm run dev:frontend`.

## Changes (startup config only)

| File | Change |
|------|--------|
| `scripts/_workos-dev-contract.ps1` | New canonical port contract |
| `scripts/dev-backend.ps1` | Default port 8001 |
| `scripts/dev-frontend.ps1` | New launcher; sets BACKEND_PORT |
| `scripts/dev.ps1` | 8001/3000 contract |
| `scripts/start-dev.ps1` | 8001 backend; BACKEND_PORT in frontend job; safer stale handling |
| `frontend/vite.config.ts` | Proxy default `127.0.0.1:8001` |
| `package.json` | `dev:backend`, `dev:frontend`, `test:startup-contract` |
| `start_app.sh` | Bash default 8001 |
| `.env.example` | BACKEND_PORT=8001 |
| `scripts/canonical_startup_contract.test.mjs` | 11 static contract tests |

## Restart proof

Two cycles without manual `BACKEND_PORT`:

| Cycle | Backend | Frontend | Intake proxy | Listeners B/F | Result |
|-------|---------|----------|--------------|---------------|--------|
| 1 | healthy | 200 | 200 | 1 / 1 | PASS |
| 2 | healthy | 200 | 200 | 1 / 1 | PASS |

Launchers used: `dev-backend.ps1` + `dev-frontend.ps1` (same contract as `dev:stack`; combined script streams logs interactively).

## Route health (10/10 HEALTHY)

All routes shell 200; API probes 200 where applicable.

## DB invariance

Before/after: integrity ok; intake 4; orders 6; employees 8; **0 business writes**.

## Parity invariance

ALL_FALSE; no persistence; no enforcement.

## Tests and build

- `npm run test:startup-contract` — **11/11 PASS**
- `pnpm run build` (frontend) — **PASS**

## Open debt (not in scope)

- **Banner truth** → UI-TRUTH-01 plan  
- **Split API paths** (proxy vs direct 8001) — MEDIUM risk, documented

## Next task

`UI-TRUTH-01-ENVIRONMENT-BANNER-OPERATIONAL-HEALTH-TRUTH-PLAN`

## Delivery footer

```
Task: RUNTIME-CONFIG-03
Starting HEAD: 757d6fd
Owner P1–P10 confirmed: YES
Canonical backend: 8001
Canonical frontend: 3000
Manual BACKEND_PORT required: NO
Restart cycles: 2 PASS
Intake: PASS
Routes: 10/10
DB invariance: PASS
Parity: ALL_FALSE PASS
Frontend build: PASS
Focused tests: PASS
Owner command: npm run dev:stack
Next: UI-TRUTH-01
Verdict: RUNTIME_CONFIG_03_CANONICAL_STARTUP_ALIGNMENT_PASS
```
