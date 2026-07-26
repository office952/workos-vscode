# W7-INT-01 — Full frozen-spine request→ExecutionReality E2E gate

**Date:** 2026-07-15  
**Task:** `FULL_FROZEN_SPINE_REQUEST_TO_EXECUTIONREALITY_E2E_GATE_V1`  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Starting HEAD:** `1586c16`  
**Verdict:** `W7_INT_01_PASS_WITH_NONBLOCKING_POST_PROGRAM_DEBT`

## Scenario strategy

`SINGLE_SCENARIO_WITH_CONTROLLED_STAGE_FIXTURES`

| Stage | Fixture | ID |
|-------|---------|-----|
| Intake V6 → QuoteSnapshotV2 → Offer | Frozen read-only | workspace `80570a4a-a806-4305-a39c-b34a72092694`, quote `1`, `QSN2-2026-0001` |
| Order → Plan → Truth → Resolution → Reality | Controlled gate fixture | order `23099` `ORD-W5INT02-GATE` |

Upstream commercial spine is **not re-run live** (quote 1 / QSN2 immutable). Downstream execution chain is **re-run live** on `:8001`.

## Runtime ownership

| Service | PID | Port |
|---------|-----|------|
| Backend | 26888 | 8001 |
| Frontend | 30548 | 3000 |

## Tests

| Category | Passed | Failed | Skipped | Notes |
|----------|--------|--------|---------|-------|
| Frozen-spine backend bundle | 159 | 0 | 2 | 2 `output_composition` = PREEXISTING_FIXTURE_DEBT |
| Frontend operator UI | 20 | 0 | 0 | |
| **Gate total** | **179** | **0** | **2** | |

## Runtime proof

- `w7_int_01_gate_evidence.json` — PASS
- W5 chain subprocess — all `pass_checks` true
- QSN2 hash unchanged after execution run
- Order snapshot unchanged after resolution/start/reality
- Task truth post-chain: 13 tasks, mounting + logo segment, `RELEASE_ALLOWED` after full resolve
- ExecutionReality start 200

## Classifications

- Task identity: `COMPLETE_WITH_LOGO_DEBT`
- 7H: `PARTIAL_WITH_OWNER_DECISIONS`
- ExecutionReality: `REFERENCE_SUFFICIENT`
- Logo path: `ACCEPTED_PARTIAL_NONBLOCKING`
- Legacy active authority: **NO**
- Frontend policy authority: **NO**
- Live Product System rebuild after freeze: **NO** (QSN2 hash stable)

## Screenshots

13 captures in `w7_int_01_screenshots/`

## Program recommendation

`FROZEN_SPINE_COMPLETE_MOBILE_FINAL_PHASE_PENDING`

## Owner path (execution spine)

1. `http://127.0.0.1:3000/execution/23099` — component tasks (Vector Prep, Cut Acm Panel, logo segment)
2. Production strip blocked → **Detalii decizii**
3. Resolve `INTERNAL_SABLON_FOREX_COST` → still blocked
4. Resolve remaining blockers → **Productie permisa**
5. Start `vector_prep` via API/UI → ExecutionReality visible
6. `http://127.0.0.1:3000/quotes/1` — frozen QSN2 offer reference (read-only)

## Accepted post-program debt

- Full live single-scenario intake→order rerun
- OperatorView manual refresh
- Full audit timeline
- Employee Mobile UI
- 2 output_composition pytest fixtures
- ShopFloor reduced projection
