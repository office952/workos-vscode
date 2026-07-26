# W4-T01B — Intake V6 Snapshot-Authoritative Pricing Review Alignment V1

**Task:** W4-T01B  
**Date:** 2026-07-15  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Starting HEAD:** `f98b804`  
**Verdict:** `W4_PRICING_REVIEW_SNAPSHOT_PASS_COMMITTED`

---

## Summary

Aligned Intake V6 pricing review and commercial spine read model to consume frozen `QuoteSnapshotV2` commercial truth post-freeze. Quote columns are validation-only (`SNAPSHOT_READ_DIRECT_COLUMNS_VALIDATION_ONLY`). Column drift blocks review completion; read model surfaces drift without mutating quote state.

---

## Authority classification (after)

| Path | Classification |
|------|----------------|
| `complete_v6_pricing_review` | **CANONICAL_SNAPSHOT_READ_MODEL** |
| `extract_v6_pricing_review_totals_authoritative` | **CANONICAL_SNAPSHOT_READ_MODEL** |
| `build_v6_pricing_review_spine_projection` | **CANONICAL_SNAPSHOT_READ_MODEL** |
| Quote `grand_total` / `subtotal` / `tax` post-freeze | **SNAPSHOT_BOUND_PROJECTION** |
| Offer stamp linkage | **SNAPSHOT_BOUND_PROJECTION** |
| Pre-freeze (no snapshot) | **PRE_FREEZE_REVIEW_PATH** |
| `accept_v6_quote` | **CANONICAL_SNAPSHOT_READ_MODEL** (unchanged) |
| Live dry-run post-freeze | **not invoked** |

---

## Quote-column policy

**SNAPSHOT_READ_DIRECT_COLUMNS_VALIDATION_ONLY** — snapshot 7G is displayed and persisted on review; quote columns compared for drift; mismatch blocks `complete_v6_pricing_review`.

---

## Live runtime (read-only)

| Field | Value |
|-------|-------|
| Workspace | `80570a4a-a806-4305-a39c-b34a72092694` |
| Quote | `1` |
| Frozen gross | `2649.99 RON` |
| Authority | `quote_snapshot_v2` |
| Orders created | 0 |
| DB mutated | NO |

Evidence: `docs/qa/product-system-active-path-isolation-v1/w4_t01b_gate_evidence.json`

---

## Tests

| Category | Passed | Failed | Skipped | Collection errors |
|----------|--------|--------|---------|-------------------|
| W4-T01B + W4-T01 + Step8 + Order V2 | 54 | 0 | 0 | 0 |

---

## Next task

**W4-INT-02 — Post-implementation Wave 4 gate** (pricing review + Offer authority seams closed; assess whether W4-T02 presentation remains necessary).
