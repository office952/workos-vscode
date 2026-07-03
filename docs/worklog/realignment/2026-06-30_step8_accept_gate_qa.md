# Step 8 Accept Gate QA — 2026-06-30

## Status

**PASS_WITH_GUARDS**

Accept gate logic **TEST-VALIDATED** (97 pytest). Accept endpoint exists but **not** invoked on live dev DB (would write `quotes`). DB read-only confirms schema + one frozen snapshot row.

## Scope

QA / AUDIT ONLY — code/tests/docs read, DB read-only, pytest. No code, DB writes, migration, accept API on live dev, order/plan/task creation.

## Architecture readback

- Accept gate is Step 8.3 (`quote_snapshot_v2_accept_gate_service.py`).
- Order conversion is separate (`order_snapshot_v2_convert_service.py`) — requires `quotes.accepted_snapshot_v2_id`.
- Freeze does not create order/plan/task.
- `/price`, CostEngine, QuoteOrchestrator forbidden on accept path.

**Alignment:** **ALIGNED**

## Git preflight

| Check | Result |
|-------|--------|
| Branch | `feature/step-7g-commercial-price-proposal` |
| HEAD before | `71e0cdc` |
| Working tree | Clean except older untracked worklogs |

## Code / tests audited

| Path | Role |
|------|------|
| `services/quote_snapshot_v2_accept_gate_service.py` | `validate_snapshot_for_accept`, `resolve_snapshot_for_accept` |
| `services/quote_snapshot_v2_service.py` | `compute_readiness`, freeze readiness sets |
| `services/intake_v6_quote_to_order_service.py` | `accept_v6_quote` — sets `accepted_snapshot_v2_id` |
| `services/order_snapshot_v2_convert_service.py` | `convert_accepted_quote_snapshot_v2_to_order` |
| `routers/intake_v6_workspaces.py` | `POST /quotes/{quote_id}/accept` |
| `tests/test_quote_snapshot_v2_accept_gate.py` | Accept gate contract |
| `tests/test_order_snapshot_v2_convert.py` | Convert requires accepted snapshot |

## Accept gate findings

### 1. Snapshot acceptabil?

Persisted `quote_snapshots_v2` row with:

- `status == "frozen"`
- `content_hash` matches `snapshot_json`
- `readiness` in `{ready_for_owner_review, partial_with_owner_decisions}` (with ack)
- `commercial_total > 0` in embedded snapshots
- `quote_id` / `workspace_id` match linkage

### 2. Readiness permite accept

| Readiness | Accept |
|-----------|--------|
| `ready_for_owner_review` | **Yes** — `snapshot_ready_for_acceptance` |
| `partial_with_owner_decisions` | **Yes** if `confirm_owner_decisions_acknowledged=true` |
| `blocked_snapshot_conflict` | **No** — `SNAPSHOT_READINESS_BLOCKED` |
| `blocked_missing_commercial` / `blocked_missing_internal` | **No** |
| `blocked_forbidden_path` | **No** |
| `blocked_schema_missing` | **No** |

### 3. `blocked_snapshot_conflict`

From `compute_readiness`: **both** 7G CommercialPriceProposal **and** 7H EstimatedInternalCost return `status == "blocked"` simultaneously. Typical on live dev with test `_full_quote_input()` — explains freeze QA `persist_status=blocked`.

### 4. `allow_freeze_readiness` (pytest fixture)

Monkeypatches `compute_readiness` to return `partial_with_owner_decisions` (unless forbidden path) so freeze persist tests can run without live 7G/7H both blocked. **Not** production behavior.

### 5. Accept endpoint

**Yes:** `POST /api/v1/intake-v6/quotes/{quote_id}/accept` → `accept_v6_quote`.

**Not runtime-tested** — mutates `quotes` (status, `accepted_snapshot_v2_id`, linkage JSON). Out of scope (DB write).

### 6. `quotes.accepted_snapshot_v2_id`

**Yes** — FK to `quote_snapshots_v2` (migration s54).

### 7. When set

On successful `accept_v6_quote` after gate passes — `QuotesService.update(..., accepted_snapshot_v2_id=snapshot_record.id)`.

### 8. Order conversion requires it?

**Yes** — `convert_accepted_quote_snapshot_v2_to_order` raises `MISSING_ACCEPTED_SNAPSHOT_V2` without FK.

### 9. Convert without accepted snapshot

**Blocked** — HTTP-style blocked error; tests in `test_order_snapshot_v2_convert.py`.

### 10. Test-only vs runtime

| Area | Status |
|------|--------|
| Accept gate rules | **TEST-VALIDATED** |
| Accept API on live dev | **Not run** (quote write) |
| Freeze on live dev with test payload | **GUARDED** (`blocked_snapshot_conflict`) |
| Dev DB snapshot `QSN2-PREV-88001` | `ready_for_owner_review` but `quote_id=null` — not wired to accept flow |

### 11. Owner decisions

- Acknowledge partial owner decisions before accept
- Pricing review + owner approval linkage required (V6 flow)
- When live 7G/7H both blocked → freeze/accept blocked until commercial/internal rules resolved
- Production readiness policy vs test monkeypatch

## DB read-only summary

| Table | Count |
|-------|-------|
| `quote_snapshots_v2` | 1 |
| `quotes` | 4 |
| `orders` | 2 |
| `execution_plan` | 1 |

Latest snapshot: `QSN2-PREV-88001`, `readiness=ready_for_owner_review`, `status=frozen`, `quote_id=null`.

`quotes.accepted_snapshot_v2_id`: column **exists**; **0** quotes with value set.

`orders.quote_snapshot_v2_id`: column **exists**.

## Runtime / API

| Check | Result |
|-------|--------|
| Health | **200** |
| Accept endpoint tested | **No** — would write quote |
| Freeze re-tested | **No** — covered by prior worklog |

## Tests

```powershell
pytest tests/test_quote_snapshot_v2_accept_gate.py tests/test_quote_snapshot_v2.py tests/test_order_snapshot_v2_convert.py tests/test_orders_update_immutability.py -q
```

**Result:** **97 passed**

Key accept tests: `test_can_accept_ready_for_owner_review_snapshot`, `test_partial_snapshot_requires_owner_decision_acknowledgement`, `test_cannot_accept_hard_blocked_readiness`, `test_accept_does_not_create_order_or_execution_plan`, `test_v2_accepted_quote_converts_via_snapshot_v2`.

## What was not changed

Code, DB, migration, Alembic, UI, pricing surfaces, orders, plans, tasks.

## No-side-effects confirmation

Confirmed.

## Owner verification

No browser UI.

| Surface | Detail |
|---------|--------|
| Tests | `backend/tests/test_quote_snapshot_v2_accept_gate.py` |
| Accept API (reference) | `POST /api/v1/intake-v6/quotes/{quote_id}/accept` |
| DB | `quote_snapshots_v2`, `quotes.accepted_snapshot_v2_id` |
| Convert guard | `test_order_snapshot_v2_convert.py` — missing FK blocked |

## Next recommended step

**Docs sync** — document accept gate rules + `blocked_snapshot_conflict` + test-only vs live dev in roadmap/09 contract.

## Roadmap awareness

| Item | Status |
|------|--------|
| Step 8 accept gate | **TEST-VALIDATED**; live accept **not runtime QA'd** |
| Step 9 | **Blocked** until accept + convert boundary clear on production payloads |
| **Cât sunt în direcția stabilită** | **79/100%** |

## Commit

Message: `docs(step8): record accept gate qa`

HEAD before: `71e0cdc`
