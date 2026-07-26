# W5-INT-01 — Accepted Frozen Snapshot → Order → Execution Contract Gate V1

**Date:** 2026-07-15  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Starting HEAD:** `314492b`  
**Trusted backend:** `http://127.0.0.1:8001` (PID 19808)  
**Canonical fixture:** IR-MRJS4VIK / workspace `80570a4a-a806-4305-a39c-b34a72092694` / quote `1` / snapshot `QSN2-2026-0001`

## Verdict

`W5_INT_01_PASS_WITH_OWNER_POLICY_PREREQUISITE`

**Implementation authorization:** `READY_FOR_W5_T01_EXECUTION_RELEASE_GUARD`

## Scope

Contract and integration gate from accepted QuoteSnapshotV2 through OrderSnapshotV2 to ExecutionPlan V2. No canonical fixture mutation. No Execution implementation.

## Primary question answers

| # | Question | Answer |
|---|----------|--------|
| 1 | Which service accepts V6 quote? | `accept_v6_quote` (`intake_v6_quote_to_order_service.py`) via `POST /api/v1/intake-v6/quotes/{id}/accept` |
| 2 | Snapshot identity bound on acceptance? | `quotes.accepted_snapshot_v2_id` + accept metadata in linkage `accept_decision.snapshot_v2` |
| 3 | Which service converts to Order? | `convert_accepted_quote_snapshot_v2_to_order` (routed by `convert_v6_quote_to_order` when `accepted_snapshot_v2_id` set) |
| 4 | OrderSnapshotV2 embedded data? | Frozen PD, aggregate, 7G, 7H, owner decisions, component scope, graph instances, provenance, accepted totals |
| 5 | Order rebuild Product Definition? | **NO** — verbatim copy from QuoteSnapshotV2 |
| 6 | Order rebuild Product Aggregate? | **NO** — verbatim copy |
| 7 | Order rebuild 7G/7H? | **NO** — copied from frozen snapshot |
| 8 | Reread live Product System templates? | **NO** on frozen convert path |
| 9 | Quote columns as authority? | **NO** — `total_amount` from snapshot commercial total, not `grand_total` columns |
| 10 | Order preserves accepted commercial total? | **YES** — pytest proves snapshot total wins over quote columns |
| 11 | Partial 7H preserved? | **YES** — `estimated_internal_cost_snapshot` + readiness propagated |
| 12 | Owner decisions preserved? | **YES** — `owner_decisions_snapshot` in OrderSnapshotV2 |
| 13 | Composition graph preserved? | **YES** — `component_instances`, `offer_scope_snapshot`, `product_aggregate_snapshot` |
| 14 | ExecutionPlan consumes OrderSnapshotV2? | **YES** — `build_execution_plan_v2_preview` reads `order.snapshot_v2_json` only |
| 15 | ExecutionPlan reconstructs live PS? | **NO** — forbidden imports; static analysis + tests |
| 16 | Task templates from frozen component identities? | **PARTIAL** — `source_component_code` + `source_operation_code` from frozen aggregate; graph node IDs not fully surfaced as task keys |
| 17 | Owner-decision blockers reach production release? | **NOT FULLY** — preserved in snapshot; explicit production-release guard not yet wired |
| 18 | Execution begin with unresolved decisions? | **POSSIBLE** — task start gate has template-decision readiness but no owner-code production block |
| 19 | Registry/template changes after Order alter plan? | **NO** for V2 path — preview deterministic from frozen JSON; legacy path isolated |
| 20 | Wave 5 implementation begin safely? | **YES with prerequisite** — frozen Order→Execution adapter proven; owner production policy is first implementation task |

## Runtime ownership

| Service | PID | Port | Worktree | Behavioral proof | Action |
|---------|-----|------|----------|------------------|--------|
| uvicorn (trusted) | 19808 | 8001 | `C:\w\psiso` | Spine `authority_source=quote_snapshot_v2`; gross 2649.99; quote not accepted; 0 orders/plans | **AUTHORITATIVE** |
| uvicorn (ghost) | 4392 | 8000 | stale | Pre-W4 schema behavior | **NONAUTHORITATIVE** |

## Acceptance authority — `CANONICAL_SNAPSHOT_ACCEPTANCE`

**Chain:** `POST accept` → `accept_v6_quote` → `resolve_snapshot_for_accept` → `validate_snapshot_for_accept` → persist `accepted_snapshot_v2_id`.

**Guards:** pricing review complete; owner approval valid; frozen snapshot; hash/linkage; partial owner ack; confirmations; no order/plan side effects.

**Not used:** quote column repricing; live dry-run; frontend totals.

## Order authority — `CANONICAL_FROZEN_ORDER_PATH`

When `accepted_snapshot_v2_id` exists, `convert_v6_quote_to_order` delegates to frozen convert. Legacy workspace-rebuild path is `ACTIVE_RECONSTRUCTION_PATH` but **guarded** — cannot run when accepted snapshot is bound.

## OrderSnapshotV2 classification — `ORDER_SNAPSHOT_COMPLETE_WITH_EXECUTION_ADAPTER`

Sufficient frozen technical + commercial truth for ExecutionPlan V2 preview/persist without live rebuild. Planning minutes and rich production-release policy remain adapter/guard work.

## ExecutionPlan authority — `CANONICAL_ORDER_SNAPSHOT_CONSUMER`

**Chain:** `create_execution_plan_v2_from_order` → `build_execution_plan_v2_preview` → frozen `OrderSnapshotV2` → planned tasks/operations.

Legacy `execution_plan_service` (`snapshot_line_items`) blocked for V2 orders (`EXECUTION_PLAN_V2_REQUIRED`).

## Owner-decision production policy — `ORDER_AND_PLAN_ALLOWED_TASK_START_BLOCKED`

| Code | Classification |
|------|----------------|
| INTERNAL_SABLON_FOREX_COST | MUST_RESOLVE_BEFORE_PRODUCTION_RELEASE |
| INTERNAL_MONTAJ_RULE | MUST_RESOLVE_BEFORE_PRODUCTION_RELEASE |
| INTERNAL_CONSUMABLES_RULE | MUST_RESOLVE_BEFORE_PRODUCTION_RELEASE |
| INTERNAL_AMBALARE_RULE | INTERNAL_ANALYSIS_ONLY |
| OVERHEAD_ALLOCATION_PENDING | INTERNAL_ANALYSIS_ONLY |

Acceptance and Order convert allow partial snapshot with acknowledgement. ExecutionPlan creation does not yet enforce production-release blockers from owner codes.

## Live template immutability — `FULLY_FROZEN_EXECUTION_INPUT`

V2 preview/persist/materialize reads embedded snapshots only. Tests: deterministic preview, `snapshot_v2_json` unchanged after materialize, no Product System runtime imports in Step 9.3.1 code.

## Legacy path classification

| Path | Classification |
|------|----------------|
| `convert_accepted_quote_snapshot_v2_to_order` | CANONICAL_FROZEN_ORDER_PATH |
| `convert_v6_quote_to_order` (with `accepted_snapshot_v2_id`) | CANONICAL_FROZEN_ORDER_PATH |
| `convert_v6_quote_to_order` (without accepted snapshot) | ACTIVE_RECONSTRUCTION_PATH (isolated when snapshot accepted) |
| `execution_plan_v2_preview/persist` | CANONICAL_ORDER_SNAPSHOT_CONSUMER |
| `execution_plan_service` (legacy) | READ_ONLY_LEGACY_PROJECTION / blocked for V2 |
| `product_system_execution_output_service` | LEGACY_ISOLATED (not on V2 path) |

## Tests

| Category | Passed | Failed | Skipped | Collection errors |
|----------|--------|--------|---------|-------------------|
| Acceptance + accept gate | 18 | 0 | 0 | 0 |
| Order Snapshot V2 convert + scope | 28 | 0 | 0 | 0 |
| Step 9 Order→ExecutionPlan | 12 | 0 | 0 | 0 |
| ExecutionPlan V2 preview/persist | 48 | 0 | 0 | 0 |
| Wave 4 regression (offer/review) | 58 | 0 | 0 | 0 |
| **Total focused suite** | **164** | **0** | **0** | **0** |

## Runtime/DB mutation

**NO** — canonical quote `1` remains unaccepted; 0 orders; 0 execution plans.

## Wave 5 implementation spine (serialized)

1. **W5-T01** — Execution owner-decision production-release guard
2. **W5-T02** — Component/task identity enrichment from frozen graph nodes
3. **W5-T03** — Order→Execution adapter hardening (planning minutes policy)
4. **W5-INT-02** — Post-implementation Wave 5 integration gate

**Parallel-safe:** OrderSnapshotV2 schema/docs tests; readonly preview endpoint contract tests.

## First allowed Wave 5 task

**W5-T01 — Execution owner-decision production-release guard**

Wire frozen `owner_decisions_snapshot` codes into execution release / task-start policy for `MUST_RESOLVE_BEFORE_PRODUCTION_RELEASE` codes without reopening live Product System rebuild.

## Evidence

- `docs/qa/product-system-active-path-isolation-v1/w5_int_01_gate_evidence.json`
- `backend/scripts/w5_int_01_integration_gate_smoke.py`
