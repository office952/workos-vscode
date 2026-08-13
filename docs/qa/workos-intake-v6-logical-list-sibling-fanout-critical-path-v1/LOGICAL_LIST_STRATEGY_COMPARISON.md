# LOGICAL_LIST_STRATEGY_COMPARISON

Baseline HEAD: `979d22d2`  
Phase: **0 only** (no product-code changes)  
Evidence: in-process stage timings + HTTP contention + discrete Step 2 timeline on QA clone `09cea6e2-…`

## Measured contention (HTTP)

```text
PQ_ALONE_MS            = 526 / 881 / 868
LL_ALONE_MS            = 763 / 471 / 400
PQ_WITH_LL_MS          = 975 / 717
LL_WITH_PQ_MS          = 1062 / 897
FULL_FANOUT_TOTAL_MS   = 770 / 940
FULL_FANOUT_GET_COUNT  = 5 (forced fan-out) / 7 (live discrete save incl. assist+binding)
LOGICAL_LIST_SQL_QUERY_COUNT = 67 (61 nested dry-run)
```

D2 sequential simulation (PQ then LL, no overlap):

```text
click_to_current_proxy_ms = 383 / 661
ll_after_ms               = 597 / 714
```

Discrete concurrent save (depth 80→100):

```text
PQ_DURATION_MS = 1069
LL_DURATION_MS = 1107
PQ_START == LL_START (same ms)
```

In-process LL stage dominance: nested priced_quote_dry_run ≈ **48–51 ms of ~56 ms total** (~87%).

---

## Required fields

```text
OPTION_A_ESTIMATED_EFFECT =
  Offer-path: remove LL nested CPP during PQ → click-to-current ≈ PQ alone class
  (~380–700 ms in D2-sim / alone warm; concurrent PQ today 700–1000+ ms).
  Also permanently removes nested dry-run from LL (LL SQL 67→~6; LL latency drops after CURRENT).
  Cost: FE must project ACM/conn composition rows from pricedQuote or accept missing LL API rows.

OPTION_D2_ESTIMATED_EFFECT =
  Offer-path: same primary win — PQ runs without LL competing → click-to-current ≈ PQ alone class
  (measured proxy 383–661 ms vs concurrent PQ 717–975 / discrete 1069 ms).
  LL still expensive after CURRENT (nested dry-run remains; alone 400–763 ms).
  Contract/API unchanged; composition rows stay server-authored.

CONTRACT_CHANGE_A =
  YES — logical-list response loses server-built ACM/conn composition rows unless FE merges;
  risk of API LL ≠ UI LL divergence.

CONTRACT_CHANGE_D2 =
  NO — backend logical-list contract preserved completely.

OWNERSHIP_CHANGE_A =
  YES (presentation ownership) — FE becomes co-assembler of logical composition display
  from pricedQuote lines; must not become pricing authority. Requires explicit ownership statement.
  Substantial risk of duplicating `_composition_contract_logical_rows` semantics in FE.

OWNERSHIP_CHANGE_D2 =
  NO — LL remains sole author of logical-list rows; CPP remains Ofertă authority via pricedQuote.

DUPLICATE_CPP_REMAINS_A =
  NO (inside LL)

DUPLICATE_CPP_REMAINS_D2 =
  YES (LL still nests dry-run after CURRENT)

CPP_CONTENTION_ON_OFFER_PATH_A =
  NO

CPP_CONTENTION_ON_OFFER_PATH_D2 =
  NO (LL starts only after PQ settles)

STALE_DATA_RISK_A =
  MEDIUM — FE merge must track pricedQuote revision; API/UI row model can drift over time.

STALE_DATA_RISK_D2 =
  LOW–MEDIUM — mitigated by revision/generation discard of late LL responses (required by D2 design).

IMPLEMENTATION_COMPLEXITY_A =
  MEDIUM–HIGH (backend contract + FE composition projection + parity/ownership)

IMPLEMENTATION_COMPLEXITY_D2 =
  LOW–MEDIUM (ReviewStep scheduling + revision token + stale discard; no backend LL change)

CHOSEN_OPTION =
  D2

EXACT_REASON =
  Measured evidence shows concurrent LL (with nested dry-run) starts with pricedQuote and
  inflates offer-path PQ latency (PQ_WITH_LL 717–975 ms / discrete PQ 1069 ms vs D2-sim
  click-to-current proxy 383–661 ms). D2 removes CPP/SQLite contention from the official
  CURRENT path while preserving the full logical-list backend contract and composition rows.
  Per Owner rule: prefer the smallest solution that fixes the operator-critical bottleneck.
  A would remove more computation but requires FE composition projection with contract/
  ownership risk (potential duplication of `_composition_contract_logical_rows`). A is not
  justified yet because D2 already targets click-to-current and nested CPP after CURRENT is
  acceptable under D2. Escalate to A only if D2 implementation fails operator latency/behavior
  targets or nested post-CURRENT CPP remains materially harmful.
```

## A eligibility gate (not satisfied for primary choice)

Moving ACM/connection projection into FE would:

- create a parallel logical-list display contract unless carefully owned;
- risk duplicating backend `_composition_contract_logical_rows` semantics;
- risk future API LL vs UI LL divergence.

Therefore A is **not** chosen as primary despite larger computational deletion.

## Next

```text
/ce-work = NOT_AUTHORIZED_YET
PRODUCT_CODE_CHANGES = 0
COMMIT = NO
PUSH = NO
```

Owner must explicitly authorize `/ce-work` for D2 implementation.
