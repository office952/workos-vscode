# Step 8 Quote Prerequisites → Accept → Convert QA — 2026-06-30

## Status

**BLOCKED_PRICE_SOURCE_UNCLEAR** (pricing review requires quote column totals; quote 1 unpriced; snapshot 2 `commercial_total=12.5` not an allowed source per contract)

Secondary blockers documented for follow-up even after pricing:

1. Snapshot 2 persisted with `status=draft` (partial readiness) — accept/convert gates require `status=frozen`.
2. `resolve_snapshot_for_accept` filters `status=frozen` only — snapshot 2 invisible to accept path today.

Owner approval, accept, and convert **NOT RUN** (stopped at pricing review gate).

## Scope

Controlled live QA — Intake V6 prerequisite endpoints + accept/convert. No code, UI, migration, Alembic, seed, `/price`, CostEngine, QuoteOrchestrator, execution_plan/tasks, Step 9, push. Agent did not start backend/frontend.

## Architecture readback

| Contract | Confirmed |
|----------|-----------|
| Step 8 ends at quote/order snapshot boundary | Yes — `09_QUOTE_ORDER_SNAPSHOT_CONTRACT.md` |
| Step 9 out of scope | Yes — `10_EXECUTION_PLAN_TASK_GRAPH.md` |
| Accept/convert must not create execution_plan/tasks | Yes — services count before/after |
| Order snapshot V2 copies dual snapshots | Yes — `order_snapshot_v2_convert_service.py` |
| Commercial/internal remain separate | Yes |
| `partial_with_owner_decisions` needs explicit owner ack on accept | Yes — `confirm_owner_decisions_acknowledged` |

**Alignment:** **ALIGNED** with documented target; **live gap** between freeze persist status and accept gate for partial readiness.

## Git preflight

| Check | Result |
|-------|--------|
| Branch | `feature/step-7g-commercial-price-proposal` |
| HEAD | `7527224` — `docs(step8): record live freeze accept convert qa` |
| Unexpected code changes | None |

## Health

| Probe | Result |
|-------|--------|
| `GET /health` | **200** `{"status":"healthy"}` |

## Backup

| Item | Value |
|------|-------|
| Path | `backend/dev.backup-before-step8-prereq-accept-convert-20260630-132826.db` |
| Size | 9,236,480 bytes |

**Rollback:**

```powershell
cd C:\Users\offic\Desktop\workos-active\backend
Copy-Item .\dev.backup-before-step8-prereq-accept-convert-20260630-132826.db .\dev.db -Force
```

## Baseline (read-only)

| Table / metric | Count / value |
|----------------|---------------|
| `quote_snapshots_v2` | 2 |
| `quotes` | 4 |
| `orders` | 2 |
| `execution_plan` | 1 |
| `execution_tasks` | table absent |
| Quote 1 | `draft`, `grand_total=0`, `accepted_snapshot_v2_id=null` |
| Snapshot 2 | `QSN2-2026-0002`, `quote_id=1`, `readiness=partial_with_owner_decisions`, **`status=draft`** |
| Snapshot 2 JSON | `commercial_total=12.5` (RON), `estimated_total_internal_cost=866.6706`, cpp `status=blocked` |

## Endpoint audit (before writes)

| # | Question | Answer |
|---|----------|--------|
| 1 | Pricing review endpoint | `POST /api/v1/intake-v6/quotes/{quote_id}/complete-pricing-review` (`intake_v6_workspaces.py`) |
| 2 | Owner approval endpoint | `POST /api/v1/intake-v6/quotes/{quote_id}/owner-approval` |
| 3 | Accept endpoint | `POST /api/v1/intake-v6/quotes/{quote_id}/accept` |
| 4 | Convert endpoint | `POST /api/v1/intake-v6/quotes/{quote_id}/convert-to-order` → `convert_accepted_quote_snapshot_v2_to_order` when `accepted_snapshot_v2_id` set |
| 5 | Pricing review payload | `reviewer_confirmation`, `confirm_quote_stays_draft`, `confirm_no_order`, `confirm_no_execution`, `confirm_no_inventory`, `pricing_review_reason`; optional `expected_quote_id`, `client_analysis_hash` |
| 6 | Owner approval payload | `decision_reason`, `acknowledged_no_execution_tasks`, `acknowledged_no_stock_consumption`; optional `client_analysis_hash`, `expected_quote_id` |
| 7 | Accept payload | `_valid_accept_body()` + `confirm_owner_decisions_acknowledged=true` for partial snapshot |
| 8 | Writes only quote fields? | Pricing review / owner approval update `quotes.notes` linkage; no order/plan |
| 9 | Calls `/price`, CE, QO? | **No** — grep clean on `intake_v6_quote_to_order_service.py` / convert service forbidden imports |
| 10 | Creates order/plan/task? | **No** — explicit before/after counts in service |
| 11 | `grand_total > 0` required? | **Yes** — `_extract_commercial_totals_from_quote()` reads **quote columns only**; rejects `grand_total<=0` with `QUOTE_NOT_PRICED` |
| 12 | Snapshot 2 for accept? | Row exists but **`status=draft`**; `resolve_snapshot_for_accept` + accept gate require **`status=frozen`**; partial live freeze sets draft via `_status_for_readiness()` |

**Forbidden path check:** endpoints audited **SAFE** (no CE/QO/`/price`/execution). **Price source for pricing review:** **NOT SAFE to proceed** without quote column pricing.

## Pricing review result

| Field | Value |
|-------|--------|
| Endpoint | `POST /api/v1/intake-v6/quotes/1/complete-pricing-review` |
| HTTP | **422** |
| Error | `QUOTE_NOT_PRICED` |
| Message | Quote has no commercial totals — price the quote in QuoteWizard before completing pricing review. |
| `pricing_review_v1` after | **null** (unchanged) |
| Orders / execution_plan | unchanged |

**Price source analysis:**

| Source | Value | Allowed by contract? |
|--------|-------|----------------------|
| `quotes.grand_total` | 0.0 | Required source — **missing** |
| Snapshot 2 `commercial_total` | 12.5 RON | Present in JSON — **not read** by `complete_v6_pricing_review` |
| Snapshot 2 internal total | 866.67 | **not read** for pricing review |

Using snapshot total without quote column pricing would violate `_extract_commercial_totals_from_quote` contract → **BLOCKED_PRICE_SOURCE_UNCLEAR** for this QA task (no `/price`, no legacy reprice, no manual DB).

## Owner approval result

**NOT RUN** — blocked after pricing review failure.

## Accept result

**NOT RUN** — would additionally fail on:

- missing pricing review / owner approval;
- snapshot 2 `status=draft` → `SNAPSHOT_NOT_FROZEN` / `MISSING_SNAPSHOT_V2` via resolver.

## Convert result

**NOT RUN**

## DB verification (after pricing review attempt)

| Metric | Value |
|--------|-------|
| `quote_snapshots_v2` | 2 |
| `quotes` | 4 |
| `orders` | 2 |
| `execution_plan` | 1 |
| Quote 1 `accepted_snapshot_v2_id` | null |
| New order | none |

## No execution side effects

Confirmed: no change to orders (2) or execution_plan (1).

## Tests

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_commercial_price_proposal_preview.py tests/test_estimated_internal_cost_preview.py tests/test_quote_snapshot_v2.py tests/test_quote_snapshot_v2_accept_gate.py tests/test_order_snapshot_v2_convert.py tests/test_dev_volumetric_v2_registry_bridge.py tests/test_aggregate_cost_bom_adapter.py::test_nested_finish_setup_flattens_return_depth_for_profile_variant -q
```

**Result:** **122 passed** (~5s)

## Owner verification checklist

| Item | Where |
|------|-------|
| Quote 1 | `quotes.id=1`, still unpriced draft |
| Snapshot 2 | `quote_snapshots_v2.id=2`, `status=draft` |
| Pricing review attempt | 422 `QUOTE_NOT_PRICED` |
| Backup | `backend/dev.backup-before-step8-prereq-accept-convert-20260630-132826.db` |
| Worklog | this file |

## Next recommended step

**Owner GO for a narrow Step 8.3 build** (code, not QA-only):

1. Align live partial freeze persist status with accept gate (`partial_with_owner_decisions` → persist `status=frozen`, or relax gate consistently with tests).
2. Allow pricing review completion from frozen snapshot V2 commercial total when quote columns are intentionally zero (Intake V6 handoff path) — **without** `/price`/QO/CE.

Until then: price quote 1 in QuoteWizard (sets `grand_total>0` on quote columns), then re-run this QA — **accept may still fail on snapshot `draft` status** until (1) is fixed.

## Roadmap

| Item | Status |
|------|--------|
| Live freeze | **VALIDATED** |
| Live pricing review → accept → convert | **BLOCKED** |
| Step 8 overall | **PARTIAL_WITH_GUARDS** (unchanged) |
| Step 9 | **BLOCKED** |
| 7I / 10 / 11 | Unchanged |

**Cat sunt in directia stabilita: 92/100%**
