# W4-INT-01 — Frozen QuoteSnapshotV2 → Offer/Order Handoff Contract Gate V1

**Task:** W4-INT-01  
**Date:** 2026-07-15  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Starting HEAD:** `3487d2d`  
**Trusted backend:** `:8001` (PID 17020, `C:\w\psiso\backend`)  
**Ghost / non-authoritative:** `:8000` (PID 4392, orphan LISTENING)  
**Canonical workspace:** `80570a4a-a806-4305-a39c-b34a72092694`  
**Canonical quote:** `1`  
**Canonical snapshot:** `QSN2-2026-0001`  
**Scope:** Read-only inspection gate — no Offer/Order/ExecutionPlan mutation  

---

## 1. Verdict

**`W4_INT_01_BLOCKED_ACTIVE_OFFER_AUTHORITY`**

Frozen `QuoteSnapshotV2` is readable, hash-stable, and consumable on **accept** and **Order Snapshot V2 convert** paths. The active Intake V6 **Offer** path (`handoff-to-offer` / `priced-quote/write`) still reprices from live workspace dry-run and does **not** consume the frozen snapshot. Pricing review prefers quote column totals over frozen 7G when quote `grand_total > 0`. Wave 4 implementation may proceed only by fixing Offer authority first.

**Implementation authorization:** `BLOCKED_ACTIVE_OFFER_AUTHORITY`

---

## 2. Repository safety

- No application code changed during this gate.
- No Offer, accept, Order, or ExecutionPlan mutations performed.
- Working tree at accepted HEAD `3487d2d`; gate artifacts are docs-only.

---

## 3. Runtime ownership

| Service | PID | Port | Worktree | Behavioral proof | Action |
|---------|-----|------|----------|-------------------|--------|
| Trusted uvicorn | 17020 | 8001 | `C:\w\psiso\backend` | `GET /api/v1/product-system/quote-snapshot-v2/QSN2-2026-0001` → 200; hash match; spine state shows frozen snapshot | **AUTHORITATIVE** |
| Ghost listener | 4392 | 8000 | N/A (no owning process) | LISTENING only | **NON-AUTHORITATIVE** |

Classification: `ISOLATED_TRUSTED_BACKEND_8001_GHOST_8000_NONAUTHORITATIVE` (carried from W3-INT-01B).

---

## 4. Accepted snapshot evidence

| Field | Value | PASS |
|-------|-------|------|
| `snapshot_code` | `QSN2-2026-0001` | YES |
| Content hash (API JSON) | `ff3224ebb0b9745f2397dab288f542de2c8b07bd9533f569a3ac5ef981c60f7c` | YES |
| Readiness | `partial_with_owner_decisions` | YES |
| 7G status | `ready` | YES |
| 7G `commercial_total` (net) | `2190.072 RON` | YES |
| Quote `grand_total` (gross, VAT-inclusive) | `2649.99 RON` | YES (aligned to priced write) |
| 7H status | `blocked` | YES |
| Owner decisions (frozen) | 5 internal + 2 commercial rule entries | YES |
| Composition graph | 3 nodes / 2 edges | YES |
| Synthetic CPP marker | absent | YES |
| `pricing_authority` in provenance | `commercial_price_proposal_7g` | YES |

**Note:** Gross `2649.99` lives on quote columns and dry-run write response; frozen 7G authority field is net `commercial_total` / `subtotal_commercial` — not a hash defect.

---

## 5. Active Offer call chain

There is **no separate Offer entity**. Intake V6 “Offer” = guarded draft quote + backend-priced totals + commercial spine UI.

### Path inventory

| Path | Entry | Composer | Classification |
|------|-------|----------|----------------|
| **A — V6 handoff-to-offer** | `POST /intake-v6/workspaces/{id}/handoff-to-offer` | `intake_v6_offer_handoff_service` → `create_or_reuse_guarded_draft_quote` + `write_intake_v6_priced_quote_totals` | **ACTIVE_PARALLEL_OFFER_AUTHORITY** |
| **B — V6 priced-quote/write** | `POST /intake-v6/workspaces/{id}/priced-quote/write` | `intake_v6_priced_quote_write_service` → `build_intake_v6_priced_quote_dry_run` | **ACTIVE_PARALLEL_OFFER_AUTHORITY** |
| **C — V6 create-draft-quote** | `POST .../create-draft-quote` | `intake_v6_commercial_quote_service` — live PD preview in linkage snapshot | **ADAPTER_TO_CANONICAL_SNAPSHOT** (pre-price only) |
| **D — QuoteSnapshotV2 read** | `GET /product-system/quote-snapshot-v2/{code}` | `QuoteSnapshotV2Service.get_by_snapshot_code` | **CANONICAL_SNAPSHOT_CONSUMER** (read-only) |
| **E — V6 commercial-spine-state** | `GET .../commercial-spine-state` | `get_v6_commercial_spine_state` | **READ_ONLY_PROJECTION** |
| **F — IV3/IV4 draft quote** | IV3/IV4 workspace routes | legacy commercial quote services | **LEGACY_NON_V6_PATH** |
| **G — Product blueprint dossier** | dossier routers | explicitly no offer creation | **DEAD_PATH** (by design) |

### Answers (active V6 path)

1. **Canonical Offer composer:** `intake_v6_offer_handoff_service` (or direct `priced-quote/write`).
2. **Input consumed:** live workspace payload + `build_intake_v6_priced_quote_dry_run` (7G recompute).
3. **QuoteSnapshotV2 direct:** **NO** on Offer write path.
4. **Quote lines:** written **from** dry-run lines; not commercial authority.
5. **Rebuilds 7G/7H:** **YES** at write time via dry-run (7G); snapshot POST separately froze 7G+7H once.
6. **Live PD/Aggregate:** dry-run path reads live workspace truth; snapshot path froze at POST time.
7. **Live Product System templates:** yes on dry-run / draft creation; **no** on snapshot read-back.
8. **Frontend totals → persisted Offer:** **NO** — `expected_total_gross` / `expected_pricing_hash` are validated against server recomputation; mismatch blocks write.
9. **Multiple paths:** **YES** — handoff vs write vs (post-snapshot) should-be-frozen offer stabilization.
10. **Intake V6 active path:** **A/B** (live repricing), not snapshot consumer.

**Offer authority summary:** `ACTIVE_PARALLEL_OFFER_AUTHORITY` (live dry-run dominates post-snapshot offer stabilization).

---

## 6. Active Order call chain

```
Quote → pricing review → owner approval → accept_v6_quote → convert_v6_quote_to_order
                                              ↓                        ↓
                              sets accepted_snapshot_v2_id     if set → order_snapshot_v2_convert
                                                              else → legacy IV6 convert (reconstruction)
```

| Path | Classification |
|------|----------------|
| `convert_accepted_quote_snapshot_v2_to_order` (when `accepted_snapshot_v2_id` set) | **CANONICAL_FROZEN_ORDER_PATH** |
| `convert_v6_quote_to_order` legacy branch (no `accepted_snapshot_v2_id`) | **ACTIVE_RECONSTRUCTION_PATH** |
| `rebuild_v6_order_snapshot_for_existing_order` | **ACTIVE_RECONSTRUCTION_PATH** |
| IV3/IV4 convert services | **LEGACY_NON_V6_PATH** |
| Order Snapshot V2 read / schema tests | **READ_ONLY_PROJECTION** |

### Answers

1. **Order creator:** `OrdersService.create` via `convert_v6_quote_to_order` or `convert_accepted_quote_snapshot_v2_to_order`.
2. **From Offer/quote:** client fields, `grand_total` / pricing review record, accept metadata.
3. **From QuoteSnapshotV2 (V2 path):** full frozen sections embedded in `snapshot_v2_json`; `total_amount` from `commercial_price_proposal_snapshot.commercial_total`.
4. **Reprice on convert:** **NO** on V2 path; **PARTIAL** on legacy (FX conversion from quote columns + live handoff snapshots).
5. **Live templates/registries:** legacy path queries workspace handoff previews; V2 path **does not**.
6. **Composition graph:** **embedded** in V2 `product_aggregate_snapshot`; legacy uses quote `line_items` PD snapshot.
7. **7G/7H survival:** **YES** on V2 embed; partial 7H preserved.
8. **Partial 7H survival:** **YES** — `estimated_internal_cost_snapshot` copied verbatim; status `blocked` retained.
9. **Order without frozen commercial truth:** **BLOCKED** on V2 path; legacy may proceed if quote priced columns present.
10. **Idempotency:** duplicate convert blocked via `check_existing_order_for_iv3_quote` + linkage convert record; accept idempotent via status gate.

**Order authority summary:** `CANONICAL_FROZEN_ORDER_PATH` exists but is **gated behind accept setting `accepted_snapshot_v2_id`**; legacy reconstruction remains reachable.

---

## 7. Snapshot consumption matrix

| Frozen field | Offer consumer (A/B) | Order consumer (V2) | Rebuilt live? | Required action |
|--------------|---------------------|---------------------|---------------|-----------------|
| `snapshot_id` / `snapshot_code` | NOT_PROVEN (not read) | Copied + FK `quote_snapshot_v2_id` | No | W4-T01: Offer must reference |
| workspace / quote identity | Linkage only | Copied in OrderSnapshotV2 | No | OK on order path |
| `commercial_price_proposal_snapshot` | **Rebuilt** via dry-run | **Copied** verbatim | **YES** on offer | **W4-T01 block live rebuild** |
| accepted net/gross/VAT | Quote columns from dry-run gross | `accepted_commercial_total` from 7G net | **YES** on offer | Align gross/net policy in W4-T01 |
| `estimated_internal_cost_snapshot` | Not exposed on offer write | **Copied** verbatim | No on V2 convert | Offer: restricted reference only |
| `owner_decisions_snapshot` | Not on offer write | **Copied** | No | Offer: surface unresolved (read-only) |
| `product_definition_snapshot` | Draft linkage snapshot (live) | **Copied** | **YES** pre-snapshot | Frozen after snapshot POST |
| `product_aggregate_snapshot` | Not on offer write | **Copied** incl. graph | No on V2 | OK |
| composition graph | In aggregate snapshot | **Embedded** | No on V2 | OK |
| active modules | In CPP/EIC provenance strings | Via frozen CPP/EIC | **YES** on offer dry-run | W4-T01 |
| graph-cost provenance | In 7H provenance | Preserved in EIC snapshot | No on V2 | OK |
| mounting / finish / cant / volum | Workspace live on dry-run | Frozen in PD/aggregate/input_summary | **YES** on offer | W4-T01 |
| blockers / warnings | Dry-run blockers | **Copied** | Partial | OK on order |
| authority identifiers | Provenance on snapshot | **Copied** | No on V2 | Offer must cite snapshot hash |
| generated timestamp / version | Snapshot record | **Copied** | No | OK |

---

## 8. Offer authority classification

**`ACTIVE_PARALLEL_OFFER_AUTHORITY`**

Live `build_intake_v6_priced_quote_dry_run` + `write_intake_v6_priced_quote_totals` remain the active Offer stabilization path after snapshot freeze. This violates Wave 4 primary contract.

---

## 9. Order authority classification

**`CANONICAL_FROZEN_ORDER_PATH`** (preferred, implemented) with **`ACTIVE_RECONSTRUCTION_PATH`** fallback (legacy IV6 convert).

---

## 10. Parallel authority findings

| Finding | Location | Classification |
|---------|----------|----------------|
| Commercial dry-run recompute on offer write | `intake_v6_priced_quote_write_service` | **FORBIDDEN_ACTIVE_AUTHORITY** (post-snapshot) |
| Handoff-to-offer triggers live write | `intake_v6_offer_handoff_service` | **FORBIDDEN_ACTIVE_AUTHORITY** |
| Pricing review prefers quote columns | `_extract_v6_pricing_review_totals` | **FORBIDDEN_ACTIVE_AUTHORITY** when snapshot exists |
| Legacy order convert from quote line_items + live handoff | `convert_v6_quote_to_order` fallback | **FORBIDDEN_ACTIVE_AUTHORITY** (fallback) |
| `expected_total_gross` UI gate | priced write + frontend | **READ_ONLY_VALIDATION** |
| Accept gate reads snapshot only | `quote_snapshot_v2_accept_gate_service` | **READ_ONLY_VALIDATION** |
| Order V2 convert reads snapshot only | `order_snapshot_v2_convert_service` | **CANONICAL_SNAPSHOT_CONSUMER** |
| IV3/IV4 quote-to-order | separate routers | **LEGACY_ISOLATED** |
| QuoteOrchestrator / CostEngine on snapshot read | forbidden substrings guarded in tests | **DEAD_PATH** on V2 |

**Parallel authority present:** **YES** (Offer + pricing review + legacy convert).

---

## 11. Commercial freeze

- **Frozen:** 7G `commercial_total` / lines / provenance inside `QSN2-2026-0001`.
- **Leak:** Offer write and pricing review can still treat live quote columns / dry-run as authority after freeze.
- **7G frozen consumption:** **PASS** on snapshot read and order V2 convert; **FAIL** on active Offer path.

---

## 12. Internal-cost freeze

- **Frozen:** 7H snapshot `status=blocked`, `estimated_total_internal_cost=1560.3836`, BOM provenance in snapshot.
- **Partial state preserved:** **PASS** on snapshot and order V2 embed.
- **Not promoted to complete:** **PASS** — no silent resolution detected.

---

## 13. Partial 7H policy

**Overall policy:** `OFFER_AND_ORDER_ALLOWED_EXECUTION_BLOCKED`

- Accept gate allows `partial_with_owner_decisions` when `confirm_owner_decisions_acknowledged=true`.
- Order V2 convert requires accept-time partial gate metadata.
- 7H `blocked` does not hard-block accept/convert; it **does** block execution-ready internal costing.

---

## 14. Owner-decision downstream classification

| Decision | Classification | Rationale |
|----------|----------------|-----------|
| `INTERNAL_SABLON_FOREX_COST` | `MUST_RESOLVE_BEFORE_PRODUCTION_RELEASE` | Critical owner set in `estimated_internal_cost_service` |
| `INTERNAL_AMBALARE_RULE` | `INTERNAL_ANALYSIS_ONLY` | Packaging rule catalog gap; not accept-blocking |
| `INTERNAL_MONTAJ_RULE` | `MUST_RESOLVE_BEFORE_PRODUCTION_RELEASE` | Montaj rule unresolved; execution consumer |
| `INTERNAL_CONSUMABLES_RULE` | `MUST_RESOLVE_BEFORE_PRODUCTION_RELEASE` | Owner decision required for consumables costing |
| `OVERHEAD_ALLOCATION_PENDING` | `INTERNAL_ANALYSIS_ONLY` | Overhead allocation policy pending; not commercial gate |

Commercial rule entries (`AMBALARE_COMMERCIAL_RULE`, `MONTAJ_COMMERCIAL_RULE`) are presentation/commercial catalog — `INTERNAL_ANALYSIS_ONLY` for Offer/Order handoff.

---

## 15. Product graph preservation

**Order V2 path:** **YES** — `product_aggregate_snapshot` + `component_instances` + `offer_scope_snapshot` copied verbatim.

**Offer path:** **PARTIAL** — live workspace drives dry-run; frozen graph not read post-snapshot.

---

## 16. Graph-cost provenance preservation

**Order V2:** **YES** — 7H provenance strings and aggregate BOM provenance frozen inside snapshot.

**Offer:** **NOT_PROVEN** — dry-run does not consume frozen provenance.

---

## 17. Offer contract (minimum canonical)

**Must preserve when Offer is snapshot-backed:**

| Element | Treatment |
|---------|-----------|
| Source snapshot ID/hash | **Copied** (immutable reference) |
| Frozen official 7G proposal | **Referenced** (no recompute) |
| Customer-facing lines | **Presentation** from frozen 7G lines |
| Product/composition summary | **Referenced** from frozen PD/aggregate |
| Terms / VAT | **Copied** from frozen commercial totals policy |
| Internal-cost reference | **Referenced** separately; restricted visibility |
| Unresolved internal decisions | **Copied**; cannot auto-resolve |
| Acceptance readiness | **Derived** from snapshot readiness + gates |
| Provenance | **Immutable** snapshot metadata |

**Forbidden:** live dry-run repricing after snapshot exists; PD/Aggregate rebuild for accepted truth.

---

## 18. Order contract (minimum canonical)

**Embed strategy:** `EMBED_REQUIRED_FROZEN_SECTIONS_WITH_HASH`

Justification: `order_snapshot_v2_convert_service` already builds `OrderSnapshotV2` with frozen PD, aggregate, 7G, 7H, owner decisions, blockers, provenance, and `content_hash`; Execution consumers can read `snapshot_v2_json` without live Product System queries.

---

## 19. Repricing checks

| Stage | Reprices? |
|-------|-----------|
| Offer handoff / priced write | **YES** (live dry-run) |
| Pricing review | **NO** recompute, but may **read quote columns** instead of snapshot |
| Accept | **NO** |
| Order V2 convert | **NO** |
| Legacy order convert | **PARTIAL** (FX + live handoff snapshots) |

---

## 20. Live Product System dependency

| Stage | Live PS dependency |
|-------|-------------------|
| Post-snapshot Offer | **YES** — defect |
| Accept | **NO** |
| Order V2 convert | **NO** |
| Legacy convert | **YES** |

---

## 21. Frontend authority

Frontend sends `expected_total_gross` and `expected_pricing_hash` as **confirmation hints** only. Backend recomputes via dry-run and rejects mismatch. **Frontend persisted authority: NO.**

---

## 22. Idempotency requirements

- Snapshot POST: idempotent reject (`V6_SNAPSHOT_ALREADY_EXISTS`) — proven live W3-INT-01B.
- Accept: blocked if already accepted.
- Convert: blocked if order exists (`ORDER_ALREADY_EXISTS`).
- W4 must preserve these and add Offer idempotency when snapshot-backed (no second live write).

---

## 23. Tests

### Focused gate run (full requested set)

| Category | Passed | Failed | Skipped | Collection errors |
|----------|--------|--------|---------|-------------------|
| Snapshot / offer / order / accept | 94 | 7 | 0 | 32 |

### Core V6 subset (authoritative for gate)

| Category | Passed | Failed | Skipped | Collection errors |
|----------|--------|--------|---------|-------------------|
| `test_intake_v6_quote_snapshot_v2` + `test_order_snapshot_v2_convert` + offer handoff + accept gate | 63 | 2 | 0 | 0 |

### Failure classification

| Failure | Classification |
|---------|----------------|
| `test_output_composition_*` (2) | `PREEXISTING_FIXTURE_DEBT` (`_latest_quote_snapshot_v2` seam) |
| `test_quote_snapshot_v2.py` (5) | `PREEXISTING_ROUTE_AUTH_DEBT` / fixture drift |
| `test_intake_v4_quote_to_order_owner_approval` (32 errors) | `PREEXISTING_FIXTURE_DEBT` (`product_system_template_not_found` seed) |

**Focused tests verdict:** **PARTIAL** (core order/accept/snapshot path green; known debt failures classified).

---

## 24. Regressions

No new regressions introduced (read-only gate). Wave 3 snapshot regression covered by passing `test_intake_v6_quote_snapshot_v2` core cases and `test_order_snapshot_v2_convert`.

---

## 25. Temporary debt

| ID | Debt |
|----|------|
| TD-W4-OFFER-LIVE-REPRICE-001 | Active Offer path reprices after snapshot freeze |
| TD-W4-PRICING-REVIEW-COLUMNS-001 | Pricing review prefers quote columns over snapshot commercial_total |
| TD-W4-LEGACY-ORDER-CONVERT-001 | Legacy IV6 convert reconstruction path still reachable |
| TD-W3-GHOST-8000-001 | Orphan `:8000` listener (carried) |
| TD-W3-FIXTURE-COMPOSITION-001 | `_latest_quote_snapshot_v2` test seam (carried) |

---

## 26. Implementation authorization

**`BLOCKED_ACTIVE_OFFER_AUTHORITY`**

Wave 4 coding may start **only** to remove Offer-side parallel authority; Order V2 path is implementation-ready pending Offer/snapshot alignment.

---

## 27. Wave 4 implementation spine (serialized)

1. **W4-T01 — Snapshot-authoritative Offer composition**  
   When frozen `QuoteSnapshotV2` exists for quote/workspace, block live `priced-quote/write` / `handoff-to-offer` repricing; build Offer read model from snapshot hash + 7G + presentation lines.

2. **W4-T01b — Pricing review snapshot alignment**  
   `complete_v6_pricing_review` must prefer frozen snapshot commercial totals (and hash) over quote columns when snapshot is authority.

3. **W4-T02 — Partial 7H Offer presentation policy**  
   Separate internal-cost reference on Offer; surface owner decisions; no silent resolution.

4. **W4-T03 — Legacy convert guard**  
   Hard-block legacy `convert_v6_quote_to_order` branch when snapshot exists but `accepted_snapshot_v2_id` missing (force accept metadata repair).

5. **W4-T04 — Idempotency + regression tests**  
   Offer-after-snapshot, accept, order V2, no-reprice proofs.

6. **W4-INT-02 — Wave 4 integration gate**  
   Live proof on `:8001` with read-only spine checks.

---

## 28. Parallel-safe work

- OrderSnapshotV2 schema documentation and read models (no Offer dependency).
- Owner-decision visibility UI (read-only projection).
- Test matrix expansion for accept/order (no live POST).
- Ghost `:8000` cleanup (ops, non-blocking).

---

## 29. Canonical updates

- `docs/master/workos-e2e/WORKOS_E2E_STATUS.md` — Wave 4 gate recorded; HEAD → gate commit.
- `docs/master/workos-e2e/WORKOS_E2E_TASK_GRAPH.md` — W4-INT-01 complete; W4-T01 authorized as first implementation task.

---

## 30. Commit

Gate docs commit created after this worklog (isolated, no implementation).

---

## 31. First allowed Wave 4 implementation task

**W4-T01 — Snapshot-authoritative Intake V6 Offer consumer**

Wire `handoff-to-offer` / post-snapshot `priced-quote/write` to consume frozen `QuoteSnapshotV2` (7G commercial truth, hash, provenance) and forbid live `build_intake_v6_priced_quote_dry_run` when a frozen snapshot exists for the workspace/quote.

---

## 32. Honest opinion

The hard part of Wave 3 shipped: dual snapshot freeze, accept gate, and Order Snapshot V2 convert are disciplined and test-backed. The remaining gap is naming—“Offer” still means “run dry-run again”—which will erode trust the moment live registry values move. Fix Offer authority before touching acceptance UX polish. Pricing review’s quote-column preference is a subtle footgun worth fixing in the same W4-T01 boundary.

---

## 33. Roadmap awareness checkpoint

- Wave 1–3: **COMPLETE**
- Wave 4 integration gate: **COMPLETE (this document)** — implementation **not** authorized for Order work until Offer authority fixed
- Waves 5–7: **remain blocked**

---

## 34. Delivery footer

```
Task: W4-INT-01 — FROZEN_QUOTE_SNAPSHOT_TO_OFFER_ORDER_HANDOFF_CONTRACT_GATE_V1
Starting HEAD: 3487d2d
Trusted backend: 8001
Snapshot: QSN2-2026-0001
Snapshot hash verified: YES
Offer authority: ACTIVE_PARALLEL_OFFER_AUTHORITY
Order authority: CANONICAL_FROZEN_ORDER_PATH (with ACTIVE_RECONSTRUCTION_PATH fallback)
Offer reprices: YES
Order reprices: NO (V2 path) / PARTIAL (legacy)
Product graph preserved: PARTIAL (YES on Order V2; NO on Offer)
Graph-cost provenance preserved: YES (Order V2) / NOT_PROVEN (Offer)
7G frozen consumption: PASS (snapshot/order) / FAIL (offer)
7H partial state preserved: PASS
Owner-decision policy: OFFER_AND_ORDER_ALLOWED_EXECUTION_BLOCKED
Frontend persisted authority: NO
Parallel authority: YES
Focused tests: PARTIAL
Passed: 63 (core) / 94 (full set)
Failed: 2 (core) / 7 (full set)
Skipped: 0
Collection errors: 0 (core) / 32 (full set)
Wave 4 implementation: BLOCKED_ACTIVE_OFFER_AUTHORITY
Code changed: NO
Commit: YES (docs)
Push: NO
PR: NO
Verdict: W4_INT_01_BLOCKED_ACTIVE_OFFER_AUTHORITY
```
