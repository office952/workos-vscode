# W4-T01 — Intake V6 Frozen Snapshot Authoritative Offer Consumer V1

**Task:** W4-T01  
**Date:** 2026-07-15  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Starting HEAD:** `851b9f1`  
**Verdict:** `W4_OFFER_SNAPSHOT_CONSUMER_PASS_COMMITTED`

---

## Summary

Implemented snapshot-authoritative Offer consumption for Intake V6. When a frozen `QuoteSnapshotV2` exists, `handoff-to-offer` and post-snapshot boundaries consume frozen 7G commercial truth — live `build_intake_v6_priced_quote_dry_run` is not invoked as pricing authority. `priced-quote/write` is blocked with `V6_PRICED_QUOTE_WRITE_SNAPSHOT_ALREADY_FROZEN`.

---

## Authority classification (after)

| Path | Classification |
|------|----------------|
| `handoff-to-offer` (snapshot exists) | **CANONICAL_SNAPSHOT_CONSUMER** |
| `write_intake_v6_offer_from_frozen_snapshot_v2` | **CANONICAL_SNAPSHOT_CONSUMER** |
| `priced-quote/write` (pre-snapshot) | **PRE_FREEZE_PRICING_PATH** |
| `priced-quote/write` (post-snapshot) | **BLOCKED** (`SNAPSHOT_ALREADY_FROZEN`) |
| `build_intake_v6_priced_quote_dry_run` (post-snapshot) | **not called** on Offer path |
| `complete_v6_pricing_review` | **READ_ONLY_PROJECTION** (still prefers quote columns — W4-T01B) |
| `accept_v6_quote` | **CANONICAL_SNAPSHOT_CONSUMER** (unchanged) |
| `convert_accepted_quote_snapshot_v2_to_order` | **CANONICAL_FROZEN_ORDER_PATH** (unchanged) |
| IV3/IV4 offer paths | **LEGACY_ISOLATED_PATH** |

---

## Pre-freeze / post-freeze boundary

| Phase | Behavior |
|-------|----------|
| Before snapshot | Live dry-run + `priced-quote/write` allowed |
| After snapshot | Offer handoff projects from frozen snapshot; repricing blocked |

**No-snapshot handoff policy:** `LEGACY_PRE_FREEZE_COMPATIBILITY` — existing dry-run write path retained.

---

## Live runtime (canonical fixture)

| Field | Value |
|-------|-------|
| Workspace | `80570a4a-a806-4305-a39c-b34a72092694` |
| Quote | `1` |
| Snapshot | `QSN2-2026-0001` |
| First handoff | `V6_OFFER_FROM_SNAPSHOT_WRITTEN` |
| Second handoff | `V6_OFFER_FROM_SNAPSHOT_IDEMPOTENT` |
| Priced-write post-snapshot | `V6_PRICED_QUOTE_WRITE_SNAPSHOT_ALREADY_FROZEN` |
| Orders created | 0 |
| Snapshot hash | unchanged |

Evidence: `docs/qa/product-system-active-path-isolation-v1/w4_t01_gate_evidence.json`

---

## Tests

| Category | Passed | Failed | Skipped | Collection errors |
|----------|--------|--------|---------|-------------------|
| W4-T01 focused + order V2 | 42 | 0 | 0 | 0 |
| Extended Wave 3/4 subset | 71 | 2 | 0 | 0 |

Failures: `PREEXISTING_FIXTURE_DEBT` (`test_output_composition_*`)

---

## Files changed

**Backend**
- `backend/services/intake_v6_snapshot_authoritative_offer_service.py` (new)
- `backend/services/intake_v6_offer_handoff_service.py`
- `backend/services/intake_v6_priced_quote_write_service.py`
- `backend/services/intake_v6_quote_to_order_service.py`
- `backend/tests/test_intake_v6_snapshot_authoritative_offer.py` (new)
- `backend/tests/test_intake_v6_offer_handoff_service.py`
- `backend/scripts/w4_t01_live_gate_smoke.py` (new)

**Frontend**
- `frontend/src/components/workos/intake-v6/IntakeV6QuoteCommercialSpinePanel.tsx`
- `frontend/src/lib/intakeV6/intakeV6PricedQuoteTypes.ts`
- `frontend/src/lib/intakeV6/intakeV6Api.ts`

---

## Remaining Wave 4 work

1. **W4-T01B** — `complete_v6_pricing_review` snapshot-authoritative totals (quote columns still win when `grand_total > 0`)
2. **W4-T02** — partial 7H Offer presentation policy (restricted visibility in UI)
3. **W4-T03** — hard-block legacy order convert when snapshot exists without `accepted_snapshot_v2_id`
4. **W4-INT-02** — post-implementation integration gate

---

## Next allowed task

**W4-T01B — Snapshot-authoritative pricing review alignment**

---

## Delivery footer

```
Task: W4-T01 — INTAKE_V6_FROZEN_SNAPSHOT_AUTHORITATIVE_OFFER_CONSUMER_V1
Starting HEAD: 851b9f1
Trusted backend: 8001
Canonical Offer authority: quote_snapshot_v2
Snapshot required after freeze: YES (for repricing block)
Live repricing after snapshot: NO
Dry-run used as Offer authority: NO (when snapshot exists)
Quote-line authority: NO
Snapshot ID preserved: YES
Snapshot hash preserved: YES
7G frozen: PASS
7H partial preserved: PASS
Owner decisions preserved: PASS
Product graph preserved: PARTIAL (referenced via snapshot stamp; full graph on order path)
Frontend persisted authority: NO
Handoff idempotent: PASS
Priced-write post-snapshot: BLOCKED
Parallel authority: NO (Offer path)
Focused tests: PASS (42/42)
Runtime: PASS
Runtime fixture changed: YES (offer stamp on quote 1)
Offer created: YES (projection stamp)
Order created: NO
Code changed: YES
Verdict: W4_OFFER_SNAPSHOT_CONSUMER_PASS_COMMITTED
```
