# W3-T03 — INTAKE_V6_CANONICAL_7G_7H_SNAPSHOT_UNIFICATION_V1

**Date:** 2026-07-14  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Starting HEAD:** `2c3d538`  
**Verdict:** `W3_SNAPSHOT_UNIFY_PASS_COMMITTED` (pending commit hash)

## Summary

Converged Intake V6 Quote Snapshot V2 creation onto canonical `QuoteSnapshotV2Service` compose (7G + 7H). Removed synthetic CPP construction from persisted quote lines. Snapshot freeze now:

- Rebuilds full V6 `quote_input` via `resolve_intake_v6_canonical_quote_input` (same path as priced dry-run)
- Re-validates live dry-run gross against persisted quote totals before freeze
- Embeds frozen 7G/7H, Product Definition, Product Aggregate (incl. `composition_graph`)
- Applies V6 commercial-first readiness: 7G ready + 7H blocked → `partial_with_owner_decisions`
- Fail-closed on 7G blocked, synthetic CPP, dry-run reprice mismatch

## Root cause

`intake_v6_quote_snapshot_v2_service._quote_snapshot_v2_payload` synthesized `CommercialPriceProposalPreview` from quote line items and write-trace summary, bypassing live 7G/7H. Write trace stored `pricing_input_trace` metadata only (not full quote_input), so even a naive canonical call would block 7G.

## Runtime (IR-MRJS4VIK / workspace `80570a4a-a806-4305-a39c-b34a72092694`)

| Check | Result |
|-------|--------|
| Dry-run 7G authority | `commercial_price_proposal_7g` |
| Official gross | 1888.68 RON |
| Canonical 7G | ready, subtotal 1560.891 |
| Canonical 7H | blocked (missing internal unit cost) |
| Readiness after V6 policy | `partial_with_owner_decisions` |
| Composition graph | frozen in aggregate snapshot |
| `volum_aluminum_module_template_code` | null — **NONBLOCKING_FOR_CASE_B_SNAPSHOT_BLOCKS_FULL_WAVE_3** |

No priced quote on fixture — snapshot POST not exercised on production fixture (no DB mutation).

## Tests

Focused: 33 passed / 2 pre-existing failures (`QuoteOutputCompositionService._latest_quote_snapshot_v2` missing — unrelated).

## Wave 3 exit

`WAVE_3_IMPLEMENTATION_COMPLETE_BLOCKED_VOLUM_PREREQUISITE` — W3-T03 slice complete; full Wave 3 closure still blocked on W2-PREREQUISITE-VOLUM-TRUTH.
