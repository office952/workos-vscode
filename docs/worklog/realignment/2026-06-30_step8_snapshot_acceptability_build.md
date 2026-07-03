# Step 8.3 Snapshot Acceptability Build — 2026-06-30

## Status

**PASS**

Narrow code build aligns live freeze persist status with accept/convert gates and allows IV6 pricing review from frozen Quote Snapshot V2 commercial total. **126 pytest passed.** Live runtime chain on quote 1 **PASS** (freeze → pricing review → owner approval → accept → convert).

## Architecture readback

| Contract | Confirmed |
|----------|-----------|
| Step 8 stops at accepted quote / order snapshot V2 | Yes |
| Step 9 out of scope | Yes |
| Order snapshot V2 copies accepted snapshot — no recalc | Yes |
| Commercial/internal snapshots remain separate | Yes |
| IV6 pricing review may use snapshot V2 total without `/price`/CE/QO | **Implemented (narrow)** |
| `partial_with_owner_decisions` still requires owner ack on accept | Yes — unchanged |

## Git preflight

| Check | Result |
|-------|--------|
| Branch | `feature/step-7g-commercial-price-proposal` |
| HEAD before | `8f66093` |
| Unexpected changes | None |

## Root cause

| Issue | Cause |
|-------|--------|
| Snapshot `status=draft` after live freeze | `_status_for_readiness()` returned `draft` for all readiness except `ready_for_owner_review` |
| Accept/convert blocked | `resolve_snapshot_for_accept` + accept gate require `status=frozen` |
| Pricing review blocked on quote 1 | `_extract_commercial_totals_from_quote()` requires `quotes.grand_total>0`; IV6 handoff quotes start at 0 |
| Snapshot total unused | `commercial_total=12.5` present in snapshot JSON but not read by pricing review |

## Files changed

| File | Change |
|------|--------|
| `backend/services/quote_snapshot_v2_service.py` | Persist `status=frozen` for all `FREEZE_ALLOWED_READINESS` values |
| `backend/services/intake_v6_quote_to_order_service.py` | `_extract_v6_pricing_review_totals()` reads frozen snapshot V2 when quote unpriced |
| `backend/tests/test_quote_snapshot_v2.py` | `test_freeze_partial_persists_status_frozen` |
| `backend/tests/test_step8_snapshot_acceptability.py` | New — pricing review, accept gate, full chain tests |

## Build A — snapshot status on freeze

**Before:** `partial_with_owner_decisions` → persisted `status=draft`.

**After:** any readiness in `FREEZE_ALLOWED_READINESS` → persisted `status=frozen`; readiness unchanged.

## Build B — pricing review from snapshot V2

**Before:** quote columns only → `QUOTE_NOT_PRICED` when `grand_total=0`.

**After:** if quote columns empty, resolve latest **frozen** snapshot by `quote_id` (workspace fallback) and read `commercial_price_proposal_snapshot.commercial_total`. Sets `pricing_totals_source=quote_snapshot_v2`. No `/price`, CE, or QO.

## Tests

Added/updated:

* `test_freeze_partial_persists_status_frozen`
* `test_v6_pricing_review_uses_snapshot_v2_when_quote_unpriced`
* `test_partial_frozen_snapshot_accept_gate_still_requires_owner_ack`
* `test_v6_step8_chain_freeze_prereq_accept_convert`

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_commercial_price_proposal_preview.py tests/test_estimated_internal_cost_preview.py tests/test_quote_snapshot_v2.py tests/test_quote_snapshot_v2_accept_gate.py tests/test_order_snapshot_v2_convert.py tests/test_dev_volumetric_v2_registry_bridge.py tests/test_step8_snapshot_acceptability.py tests/test_aggregate_cost_bom_adapter.py::test_nested_finish_setup_flattens_return_depth_for_profile_variant -q
```

**Result:** **126 passed** (~7s)

## Runtime QA (live, backend already running)

Backup: `backend/dev.backup-before-step8-3-runtime-20260630-133442.db` (9,236,480 bytes)

| Step | Result |
|------|--------|
| Health | 200 |
| Preview paper QA | `partial_with_owner_decisions` |
| Freeze quote 1 | **persisted** snapshot **3** `QSN2-2026-0003`, **`status=frozen`** |
| Pricing review | **200**, `pricing_totals_source=quote_snapshot_v2` |
| Owner approval | **200** |
| Accept quote 1 | **200**, `accepted_snapshot_v2_id=3` |
| Convert | **200**, order **88002** `ORD-IV6-V2-1782815703-1` |
| `orders.quote_snapshot_v2_id` | **3** |
| `snapshot_v2_json` | has commercial + internal snapshots |
| `execution_plan` | **1 → 1** |
| New execution_tasks | none (table absent) |

**Note:** Pre-build snapshot 2 remains `status=draft`; live chain used new freeze snapshot 3.

## No forbidden paths

Confirmed: no `/price`, CostEngine, QuoteOrchestrator, Pricing Registry rewrite, UI, migration, Alembic, seed, execution_plan/tasks, Step 9.

## Rollback

```powershell
cd C:\Users\offic\Desktop\workos-active\backend
Copy-Item .\dev.backup-before-step8-3-runtime-20260630-133442.db .\dev.db -Force
git revert HEAD  # code rollback if needed
```

## Next recommended step

Docs sync: update Step 8 status in realignment docs to reflect **live accept/convert VALIDATED** on safe IV6 path; Step 9 remains separate GO.

## Roadmap

| Item | Status |
|------|--------|
| Step 8 live freeze → accept → convert | **VALIDATED** (runtime + pytest) |
| Step 8 overall | Can move toward **VALIDATED_WITH_GUARDS** (owner decisions on partial snapshot remain explicit) |
| Step 9 | Still **BLOCKED** until owner GO — convert did not create execution_plan |
| 7I / 10 / 11 | Unchanged |

**Cat sunt in directia stabilita: 95/100%**
