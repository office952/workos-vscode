# Step 8 Order Conversion Boundary Audit — 2026-06-30

## Status

**PASS_WITH_GUARDS**

Order conversion boundary is **TEST-VALIDATED** (97 pytest) and **code-aligned** with architecture. Live accept/convert API **not run** on dev DB (writes). Dev DB has **0** quotes with `accepted_snapshot_v2_id`; fixture order `88001` has V2 snapshot via QA seed, not accept→convert flow.

## Scope

AUDIT ONLY — read code/docs/tests, DB read-only, pytest. No code, DB writes, live accept/convert API, order/plan/task creation, push.

## Architecture readback

| Contract point | Confirmed |
|----------------|-----------|
| Canonical flow | Intake V6 → preview/freeze Quote Snapshot V2 → accept → convert → Order (frozen) → ExecutionPlan **later** |
| Step 8 boundary | Accept sets `quotes.accepted_snapshot_v2_id`; convert copies to `orders.snapshot_v2_json` + `orders.quote_snapshot_v2_id` |
| Step 8 forbidden | No `/price`, CostEngine, QuoteOrchestrator on accept/convert; **no** execution_plan or tasks at accept or convert |
| Step 9 | **BLOCKED** until accept + convert validated on safe real data |
| `blocked_snapshot_conflict` | Both 7G + 7H blocked simultaneously — freeze/accept fail-closed |
| `allow_freeze_readiness` | Pytest monkeypatch only — not production |

**Alignment:** **ALIGNED**

## Git preflight

| Check | Result |
|-------|--------|
| Branch | `feature/step-7g-commercial-price-proposal` |
| HEAD | `1d4cb83` (`docs(step8): sync accept gate qa status`) |
| Unexpected code changes | **None** — only pre-existing untracked worklogs |

## Files audited

| Path | Role |
|------|------|
| `services/quote_snapshot_v2_service.py` | Preview/freeze; forbidden paths guard |
| `services/quote_snapshot_v2_accept_gate_service.py` | Accept gate; `HARD_BLOCKED_READINESS` |
| `services/order_snapshot_v2_convert_service.py` | V2 convert — order only, no plan |
| `services/intake_v6_quote_to_order_service.py` | `accept_v6_quote`, `convert_v6_quote_to_order` (V2 delegate) |
| `routers/intake_v6_workspaces.py` | Accept + convert-to-order endpoints |
| `routers/quote_snapshot_v2.py` | Preview/freeze endpoints |
| `models/quotes.py` | `accepted_snapshot_v2_id` FK |
| `models/orders.py` | `quote_snapshot_v2_id`, `snapshot_v2_json` |
| `models/quote_snapshot_v2.py` | `quote_snapshots_v2` table |
| `schemas/order_snapshot_v2.py` | Frozen order snapshot schema |
| `tests/test_quote_snapshot_v2.py` | Preview/freeze persist |
| `tests/test_quote_snapshot_v2_accept_gate.py` | Accept gate contract |
| `tests/test_order_snapshot_v2_convert.py` | Convert boundary contract |
| `tests/test_orders_update_immutability.py` | Slice 10.1 guard regression |

## Convert boundary findings (17 questions)

### 1. Exact flow quote snapshot → accept → order

1. **Preview** — `POST /api/v1/product-system/quote-snapshot-v2/preview/{template}` — no persist.
2. **Freeze** — `POST .../freeze/{template}` — persists `quote_snapshots_v2` when readiness permits (live dev often `blocked_snapshot_conflict`).
3. **Accept** — `POST /api/v1/intake-v6/quotes/{quote_id}/accept` → `resolve_snapshot_for_accept` + `validate_snapshot_for_accept` → sets `quotes.status=accepted`, `quotes.accepted_snapshot_v2_id=snapshot_record.id`, accept metadata in linkage JSON. **No order/plan/task.**
4. **Convert** — `POST /api/v1/intake-v6/quotes/{quote_id}/convert-to-order` → if `accepted_snapshot_v2_id` set, delegates to `convert_accepted_quote_snapshot_v2_to_order` → creates locked `orders` row with `snapshot_v2_json`, `quote_snapshot_v2_id`, `total_amount` from snapshot commercial total. **No execution_plan/tasks/inventory.**

### 2. Accept endpoint

`POST /api/v1/intake-v6/quotes/{quote_id}/accept` → `accept_v6_quote` (`intake_v6_workspaces.py`).

### 3. Order conversion endpoint

`POST /api/v1/intake-v6/quotes/{quote_id}/convert-to-order` → `convert_v6_quote_to_order` → V2 branch when `accepted_snapshot_v2_id` present.

### 4. Field linking accepted quote to snapshot

`quotes.accepted_snapshot_v2_id` → FK `quote_snapshots_v2.id`. Set on successful accept. Linkage JSON `accept_decision.snapshot_v2` stores metadata (`build_accept_snapshot_metadata`).

### 5. Field linking order to snapshot

`orders.quote_snapshot_v2_id` → FK `quote_snapshots_v2.id` (same accepted snapshot). `orders.quote_id` → source quote.

### 6. What goes in `orders.snapshot_v2_json`

JSON serialization of `OrderSnapshotV2`: dual commercial/internal snapshots copied from quote snapshot, `accepted_commercial_total`, `estimated_internal_total`, `accepted_currency`, product_definition/aggregate snapshots, owner_decisions/warnings/blockers, provenance, accept/convert timestamps, `no_reprice_policy=true`, `execution_plan_created=false`, `execution_plan_source=order_snapshot_v2`. **Not** legacy `snapshot_line_items` (null on V2 path).

### 7. What goes in `orders.quote_snapshot_v2_id`

Integer FK to the accepted frozen `quote_snapshots_v2.id` — same row referenced by `quotes.accepted_snapshot_v2_id`.

### 8. Missing `accepted_snapshot_v2_id` behavior

V2 convert service raises **422** `MISSING_ACCEPTED_SNAPSHOT_V2` — "use legacy convert path." If quote accepted without V2 FK, `convert_v6_quote_to_order` falls through to legacy path (requires priced `line_items` / `FINAL_PRICE_MISSING` etc.).

### 9. Blocked snapshot behavior

Convert re-checks `HARD_BLOCKED_READINESS` (`blocked_snapshot_conflict`, `blocked_missing_commercial`, `blocked_missing_internal`, `blocked_forbidden_path`, `blocked_schema_missing`) → **422** `SNAPSHOT_READINESS_BLOCKED`. Also requires `status=frozen`, hash match, commercial/internal present, commercial total > 0, RON currency.

### 10. Partial with owner decisions behavior

Accept: requires `confirm_owner_decisions_acknowledged=true`. Convert: requires accept-time gate metadata in linkage (`accept_decision.snapshot_v2.gate_status == snapshot_ready_for_acceptance`); without it → **422** `PARTIAL_SNAPSHOT_ACCEPT_GATE_MISSING`. With proper accept → convert succeeds (`test_partial_snapshot_with_accept_gate_converts`).

### 11. Tests confirming convert guard

`test_order_snapshot_v2_convert.py`: success locked order, no execution_plan, duplicate blocked, `MISSING_ACCEPTED_SNAPSHOT_V2`, `SNAPSHOT_V2_NOT_FOUND`, `QUOTE_NOT_ACCEPTED`, hard-blocked readiness, hash/quote mismatch, commercial zero, partial gate, forbidden imports, confirmations, dual totals in `snapshot_v2_json`, V2 delegate before legacy create. Plus accept gate + immutability regression in shared 97-test run.

### 12. `/price` risk?

**None on V2 convert path** — `order_snapshot_v2_convert_service.py` does not import or call pricing endpoints. Legacy convert branch (no V2 FK) still uses quote `line_items` from historical `/price` path — out of Step 8 V2 boundary.

### 13. QuoteOrchestrator risk?

**None on V2 convert path** — AST import guard tests; `FORBIDDEN_IMPORT_SUBSTRINGS` includes `quote_orchestrator`.

### 14. CostEngine risk?

**None on V2 convert path** — same forbidden import guard; no CE calls in convert service.

### 15. Does convert create execution_plan or only order snapshot?

**Order snapshot only.** Convert counts `ExecutionPlan` before/after; mismatch → `SAFETY_VIOLATION` rollback. Response flags: `execution_plan_created=false`, `writes_execution_plan=false`, `creates_execution_tasks=false`. `readiness_snapshot.execution_plan_created=false`.

### 16. What remains for Step 9?

Live accept + convert QA on safe real workspace/quote; wire freeze persist on non-blocked readiness payloads; ExecutionPlan materialization from `order.snapshot_v2_json.product_definition_snapshot` (separate `POST /execution/plan/from-order/{id}`); session/reality hardening; owner GO for full Step 9.

### 17. What owner decisions remain?

- Live accept/convert GO on safe dev data (writes quotes/orders)
- Resolve `blocked_snapshot_conflict` for production volumetric payloads (7G/7H both blocked)
- Partial owner decision codes (e.g. debitare spate ml vs m²) — ack at accept
- Alembic stamp vs `create_all` strategy for `quote_snapshots_v2`
- When to retire legacy convert path for new V6 quotes
- Step 9 GO after live boundary validated

## DB read-only summary

| Table | Count | Notes |
|-------|-------|-------|
| `quote_snapshots_v2` | 1 | `QSN2-PREV-88001`, frozen, `ready_for_owner_review`, `quote_id=null` |
| `quotes` | 4 | **0** with `accepted_snapshot_v2_id` |
| `orders` | 2 | **1** with V2 (`88001` — QA fixture); **1** legacy E2E |
| `execution_plan` | 1 | `order_id=88001`, `source_quote_snapshot_v2_id=1` — created separately, not by convert |

Columns confirmed: `quotes.accepted_snapshot_v2_id`, `orders.quote_snapshot_v2_id`, `orders.snapshot_v2_json`.

## Tests run

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_order_snapshot_v2_convert.py tests/test_quote_snapshot_v2_accept_gate.py tests/test_quote_snapshot_v2.py tests/test_orders_update_immutability.py -q
```

**Result:** **97 passed** in 6.50s

## Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| Live accept/convert never QA'd on dev DB | Medium | Next: safe live QA with non-production quote |
| Dev snapshot `quote_id=null` | Low | Accept resolves by quote_id first; workspace fallback exists |
| Legacy convert path still reachable without V2 FK | Medium | Document + eventual deprecation after Step 8 live validated |
| Fixture order 88001 not proof of accept→convert chain | Low | Pytest covers full chain; live gap explicit |

## What was not changed

Code, DB, migration, Alembic, UI, pricing surfaces, live API calls, orders/plans/tasks beyond read-only SELECT.

## No-side-effects confirmation

Confirmed. Temp audit script removed; no code artifacts left.

## Owner verification

No browser UI — API/tests/DB only.

| Surface | Detail |
|---------|--------|
| Convert API (reference) | `POST /api/v1/intake-v6/quotes/{quote_id}/convert-to-order` |
| Accept API (reference) | `POST /api/v1/intake-v6/quotes/{quote_id}/accept` |
| Tests | `test_order_snapshot_v2_convert.py`, `test_quote_snapshot_v2_accept_gate.py` |
| DB | `quotes.accepted_snapshot_v2_id`, `orders.quote_snapshot_v2_id`, `orders.snapshot_v2_json` |

## Next recommended step

**Live accept/convert QA on safe data** — freeze with non-blocked readiness payload (or test workspace clone), accept one quote, convert to order, verify FK linkage + `snapshot_v2_json` totals + no execution_plan row created by convert.

## Roadmap awareness

| Item | Status |
|------|--------|
| Step 8 convert boundary | **TEST-VALIDATED**; live convert **not runtime QA'd** |
| Step 9 | **BLOCKED** until live accept + convert on safe real data |
| **Direction score** | **84/100%** |

## Commit

Message: `docs(step8): record order conversion boundary audit`

HEAD before: `1d4cb83`
