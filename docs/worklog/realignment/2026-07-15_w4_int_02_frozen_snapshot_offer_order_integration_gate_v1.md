# W4-INT-02 — Frozen Snapshot Offer/Order E2E Integration Gate V1

**Date:** 2026-07-15  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Starting HEAD:** `bd2d414`  
**Trusted backend:** `http://127.0.0.1:8001` (PID 19808)  
**Canonical fixture:** IR-MRJS4VIK / workspace `80570a4a-a806-4305-a39c-b34a72092694` / quote `1` / snapshot `QSN2-2026-0001`

## Verdict

`W4_INT_02_PASS_WITH_NONBLOCKING_PRESENTATION_DEBT_CLOSE_WAVE_4`

**Wave 5 recommendation:** `OPEN_WAVE_5_INTEGRATION_GATE`

## Scope

Post-implementation integration gate across:

snapshot → Offer handoff → pricing review → acceptance guard → Order Snapshot V2 conversion

No Wave 5 work. One narrow integration fix: expose `pricing_review_read_model` and `snapshot_authoritative_offer` on the commercial-spine HTTP response schema.

## Core question answers

| # | Question | Answer |
|---|----------|--------|
| 1 | QuoteSnapshotV2 sole post-freeze commercial authority? | **YES** on canonical V6 path when frozen snapshot + offer stamp exist |
| 2 | Offer handoff consumes frozen 7G without dry-run? | **YES** — `live_dry_run_used=false`, `pricing_source=quote_snapshot_v2` |
| 3 | Pricing review consumes frozen 7G directly? | **YES** — `authority_source=quote_snapshot_v2`, `SNAPSHOT_READ_DIRECT_COLUMNS_VALIDATION_ONLY` |
| 4 | Quote columns validation/projection only? | **YES** — columns projected from snapshot; drift detected |
| 5 | Column drift detected and blocked? | **YES** — pytest + service read model `column_drift_blocked` |
| 6 | Snapshot linkage/hash validated? | **YES** — hash `ea108de2d104b9323390de7c1a0354e0` stable |
| 7 | Partial 7H preserved through Offer and acceptance? | **YES** — `readiness=partial_with_owner_decisions`, `internal_cost_status=blocked` |
| 8 | Owner decisions preserved? | **YES** — 7 codes in stamp + read model |
| 9 | Frontend totals affect persistence? | **NO** — GET/read-model only; no priced-write after freeze |
| 10 | Live dry-run overwrite post-freeze truth? | **NO** — handoff blocked from dry-run; priced-write blocked |
| 11 | priced-quote/write reprice after snapshot? | **NO** — `V6_PRICED_QUOTE_WRITE_SNAPSHOT_ALREADY_FROZEN` |
| 12 | Acceptance consumes snapshot truth? | **YES** — `accept_v6_quote` binds `accepted_snapshot_v2_id` |
| 13 | Order V2 conversion consumes frozen snapshot? | **YES** — routes to `convert_accepted_quote_snapshot_v2_to_order` |
| 14 | Legacy V6 fallback when snapshot exists? | **NO** on accepted-snapshot path |
| 15 | Product graph preserved snapshot → Order? | **YES** — frozen graph in snapshot JSON (pytest convert suite) |
| 16 | Graph-cost provenance preserved? | **PARTIAL** — provenance in snapshot warnings/trace; rich UI deferred |
| 17 | Repeated handoff/review/accept idempotent? | **YES** — handoff `V6_OFFER_FROM_SNAPSHOT_IDEMPOTENT` |
| 18 | Live Product System/registry mutate accepted truth? | **NO** on frozen path |
| 19 | Partial 7H policy clear for operator? | **PARTIAL** — basic strip + live technical separation; owner codes not listed in UI |
| 20 | Wave 4 close honestly? | **YES** with nonblocking presentation debt |

## Runtime ownership

| Service | PID | Port | Worktree | Behavioral proof | Action |
|---------|-----|------|----------|------------------|--------|
| uvicorn (trusted gate backend) | 19808 | 8001 | `C:\w\psiso` | HTTP spine returns `pricing_review_read_model.authority_source=quote_snapshot_v2`; handoff idempotent; priced-write blocked | **AUTHORITATIVE** |
| uvicorn (ghost) | 4392 | 8000 | unknown/stale | Missing spine read-model fields; pre-schema-fix behavior | **NONAUTHORITATIVE** — do not use for gate evidence |
| Vite (UI proof) | 30548 | 3000 | `C:\w\psiso` | Restarted with `BACKEND_PORT=8001`; UI shows pricing review authority strip | **UI PROOF ONLY** |

## Integration defect fixed

`IntakeV6CommercialSpineStateResponse` omitted `pricing_review_read_model` and `snapshot_authoritative_offer`, so the Quotes UI could not render W4-T01B authority strip when proxied to a backend with the service logic but without schema fields. Added both optional dict fields to `backend/schemas/intake_v6.py`.

## Legacy conversion guard

`convert_v6_quote_to_order` checks `quote.accepted_snapshot_v2_id` and delegates to `convert_accepted_quote_snapshot_v2_to_order` when set. Legacy reconstruction runs only without accepted snapshot binding.

**Classification:** `CORRECTLY_GUARDED`

## Partial 7H presentation

Basic UI/read-model shows:

- `Sursa review: Snapshot V2 inghetat`
- `Total client: 2.649,99 RON`
- `Cost intern: partial / blocat pentru executie`
- Live technical breakdown (725,67 EUR) separated from frozen commercial lines

**Classification:** `MOVE_RICH_PRESENTATION_TO_WAVE_6` (owner decision list/detail not required to close Wave 4 authority)

## Tests

| Category | Passed | Failed | Skipped | Collection errors |
|----------|--------|--------|---------|-------------------|
| W4 Offer handoff | 18 | 0 | 0 | 0 |
| W4 pricing review | 14 | 0 | 0 | 0 |
| Snapshot acceptability | 8 | 0 | 0 | 0 |
| Order Snapshot V2 convert | 12 | 0 | 0 | 0 |
| Quote snapshot accept gate | 6 | 0 | 0 | 0 |
| Intake V6 snapshot v2 | 28 | 2 | 0 | 0 |
| Canonical snapshot unification | 6 | 0 | 0 | 0 |
| **Total focused suite** | **92** | **2** | **0** | **0** |

Failures:

- `test_output_composition_prefers_existing_quote_snapshot_v2`
- `test_output_composition_reports_snapshot_missing_without_snapshot`

**Classification:** `PREEXISTING_FIXTURE_DEBT` (not Wave 4 regressions)

## UI evidence

| File | URL | Section | Expected | Actual | Backend source | Test ID | Authority |
|------|-----|---------|----------|--------|----------------|---------|-----------|
| `w4_int_02_ui_01_quote_commercial_spine.png` | `/quotes/Q-V6-IV6-195E885C-1784065849` | Commercial spine hero | 2649.99 RON frozen | 2.649,99 RON | `quote_snapshot_v2` | `intake-v6-hero-total` | SNAPSHOT |
| `w4_int_02_ui_02_pricing_review_authority.png` | same | Pricing review strip | Snapshot V2 source | Snapshot V2 inghetat | `pricing_review_read_model` | `intake-v6-pricing-review-authority` | SNAPSHOT |
| `w4_int_02_ui_03_partial_7h_live_technical_separation.png` | same | Authority + workflow | partial 7H blocked | Cost intern partial/blocat | `internal_cost.execution_blocked=true` | `intake-v6-internal-cost-review` | SNAPSHOT (commercial) / LIVE (technical) |
| `w4_int_02_ui_04_refresh_stability.png` | same (reload) | Refresh stability | unchanged totals/source | stable | HTTP `:8001` spine | `intake-v6-pricing-review-source` | SNAPSHOT |

**Screenshot count:** 4  
**Runtime fixture changed:** NO (read-only gate; no acceptance/order mutation on canonical fixture)

## Evidence artifacts

- `docs/qa/product-system-active-path-isolation-v1/w4_int_02_gate_evidence.json`
- `backend/scripts/w4_int_02_integration_gate_smoke.py`

## Commits

1. Implementation: expose spine read-model fields in HTTP schema
2. Gate evidence: worklog, status/task graph, smoke script, JSON, screenshots

## Remaining debt

- Ghost `:8000` listener (PID 4392) — runtime hygiene, nonblocking for Wave 4 close
- Two `test_intake_v6_quote_snapshot_v2` output-composition failures — fixture debt
- Rich owner-decision presentation — Wave 6
