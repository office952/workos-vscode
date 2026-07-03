# Step 8 Dev Pricing Registry Readiness Unblock — 2026-06-30

## Status

**PASS_WITH_GUARDS**

Readiness unblocked from `blocked_snapshot_conflict` → `partial_with_owner_decisions` on Step 8 QA payload (paper sablon). **122 pytest PASS.** Live HTTP freeze on `:8000` still returned old behavior until backend reload; in-process freeze on `dev.db` confirms new readiness. Persist requires `quote_id` or `workspace_id` (unchanged guard).

## Scope

Controlled implementation: dev material bridge + BOM `finish_setup` flatten fix + internal operation dev bridge costs. No Step 9, no accept/convert, no order/plan/task, no `/price`/CE/QO/UI.

## Architecture readback

Aligned: commercial/internal separate; non-hourly; 7G/7H dev bridge only; 7I deferred; freeze does not create order/plan/task.

## Git preflight

| Check | Result |
|-------|--------|
| Branch | `feature/step-7g-commercial-price-proposal` |
| HEAD before | `1ee3cd7` |
| Unexpected changes at start | None (untracked worklogs only) |

## Root cause

| Layer | Finding |
|-------|---------|
| `blocked_snapshot_conflict` | `compute_readiness` when **both** 7G and 7H `status=blocked` |
| 7G blocked | `COMMERCIAL_BASIS_UNKNOWN` (debitare_spate); critical owners `DEBITARE_SPATE_BASIS_ML_VS_M2`, `SABLON_FOREX_COMMERCIAL_PRICE` (forex payload) |
| 7H blocked | `INTERNAL_MATERIAL_COST_MISSING` — BOM did not flatten `finish_setup.return_depth_mm` → profile variants `variant_required`; missing dev material rates; internal ops lacked dev bridge costs; debitare_spate internal basis unknown |
| Nature | **Data/config gap** + **code mapping bug** (BOM flatten) |

## Decision: **Option A + D**

| Option | Action |
|--------|--------|
| **A** | `dev_volumetric_v2_registry_bridge.py` — merge missing material `unit_cost` in local/dev/test |
| **A** | Internal operation dev bridge RON costs in `internal_cost_rules_volumetric_v2.py`; debitare_spate interim m² |
| **D** | `aggregate_cost_bom_adapter._canonical_and_quote_input` — flatten `finish_setup` / `quote_geometry` / `client` |
| **C** | Step 8 QA payload uses **paper** sablon (`_step8_qa_quote_input`) to avoid forex critical owners |

7G remains **blocked** by design (commercial debitare_spate owner pending); 7H **partial** → readiness `partial_with_owner_decisions`.

## Files changed

| Path | Change |
|------|--------|
| `backend/data/dev_volumetric_v2_registry_bridge.py` | New dev material rate bridge |
| `backend/data/internal_cost_rules_volumetric_v2.py` | Dev bridge operation unit costs; debitare_spate m² |
| `backend/services/estimated_internal_cost_service.py` | Merge dev bridge in `_load_pricing_context` |
| `backend/services/aggregate_cost_bom_adapter.py` | Flatten nested IV6 quote_input for BOM variant resolution |
| `backend/tests/test_dev_volumetric_v2_registry_bridge.py` | Bridge + unpatched EIC partial tests |
| `backend/tests/test_quote_snapshot_v2.py` | `test_dev_bridge_readiness_not_dual_blocked` |
| `backend/tests/test_estimated_internal_cost_preview.py` | Updated debitare_spate dev bridge test |
| `backend/tests/test_aggregate_cost_bom_adapter.py` | Nested finish_setup profile variant test |

## Tests

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_commercial_price_proposal_preview.py tests/test_estimated_internal_cost_preview.py tests/test_quote_snapshot_v2.py tests/test_quote_snapshot_v2_accept_gate.py tests/test_order_snapshot_v2_convert.py tests/test_dev_volumetric_v2_registry_bridge.py tests/test_aggregate_cost_bom_adapter.py::test_nested_finish_setup_flattens_return_depth_for_profile_variant -q
```

**122 passed**

## Runtime freeze result

| Probe | Result |
|-------|--------|
| Payload | `_step8_qa_quote_input()` — paper sablon, `_full_quote_input()` geometry |
| In-process `QuoteSnapshotV2Service.freeze` on `dev.db` | `readiness=partial_with_owner_decisions`; `persist_status=blocked` (no `quote_id`/`workspace_id`) |
| HTTP `POST .../freeze/TPL-VOLUMETRIC-LETTERS_v2` on `:8000` | Still `blocked_snapshot_conflict` — **stale server process** (code not reloaded) |
| DB counts | `quote_snapshots_v2` 1→1; orders 2→2; execution_plan 1→1 |

## Owner decisions remaining

- Formal owner decision: debitare_spate commercial basis (ml vs m²) — 7G still blocked
- Replace dev bridge costs with owner-confirmed registry (7I)
- Dedicated IV6 `workspace_id` / `quote_id` for freeze persist + live accept/convert QA
- Restart dev backend to pick up fixes before HTTP freeze re-check

## No-side-effects confirmation

No `/price`, CostEngine, QuoteOrchestrator, Pricing UI, 7I, migrations, seed global, order/plan/task creation, push, work in `C:\Users\offic\workos`.

## Next recommended step

**Re-run Step 8 live accept/convert QA** on a dedicated IV6 quote with `workspace_id`/`quote_id`, after **backend restart**, using paper QA payload — freeze should persist, then accept → convert.

## Roadmap awareness

**Cât sunt în direcția stabilită: 87/100%**

Step 8 readiness path unblocked in code; live HTTP + persist identity + accept/convert chain still pending.
