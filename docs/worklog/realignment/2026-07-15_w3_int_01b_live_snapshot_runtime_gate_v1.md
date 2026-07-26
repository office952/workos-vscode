# W3-INT-01B — WAVE_3_LIVE_SNAPSHOT_PERSISTENCE_AND_RUNTIME_OWNERSHIP_GATE_V1

**Date:** 2026-07-15  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Starting HEAD:** `56f1ecf`  
**Verdict:** `W3_INT_01B_PASS_WITH_NONBLOCKING_RUNTIME_DEBT_OPEN_WAVE_4_GATE`

## Runtime ownership classification

**`ISOLATED_TRUSTED_BACKEND_8001_GHOST_8000_NONAUTHORITATIVE`**

| Port | PID | Process owner | Command line | Worktree | Action | Final state |
|------|-----|---------------|--------------|----------|--------|-------------|
| 8000 | 4392 | **NOT_PROVEN** (no `tasklist` / Win32 process) | — | — | Cannot kill — orphan LISTENING | Still LISTENING; treated as non-WorkOS |
| 8001 | 17020 | `python.exe` (user) | `uvicorn main:app --host 127.0.0.1 --port 8001` | `C:\w\psiso\backend` | Started fresh for gate | **Trusted gate backend** |

Frontend dev config already targets `http://127.0.0.1:8001` (`frontend/src/lib/config.ts`).

## Accepted behavior proof (HTTP fingerprints on :8001)

| Check | Endpoint / field | Result |
|-------|------------------|--------|
| 7G authority | `GET .../priced-quote-dry-run` → `pricing_authority` | `commercial_price_proposal_7g` |
| Cost-plus diagnostic | same → `diagnostic_cost_plus` / TD ref | Diagnostic only (`TD-W3-V6-DIAG-COST-PLUS-001`) |
| Dry-run ready | `pricing_status` | `V6_PRICED_DRY_RUN_READY` |
| ACM bond mapping | `internal_cost_trace` / snapshot 7H blockers | No `INTERNAL_MATERIAL_COST_MISSING` for `MAT-ACM-BOND-PANEL` |
| Synthetic CPP | snapshot `commercial_price_proposal_snapshot` lines | No `V6_BACKEND_PRICED_QUOTE_LINE` rule |
| Composition graph | snapshot `product_aggregate_snapshot.composition_graph` | Present (`single_child`, 2 edges) |
| Volum (Case B) | workspace payload | `TPL-VOLUM-ALUMINIU_v1` persisted; not forced into ACM-only path |

## Priced quote path (public API)

1. `PUT /api/v1/intake-v6/workspaces/{id}/internal-draft-quote-confirmation` (`confirmed: true`)
2. `POST /api/v1/intake-v6/workspaces/{id}/create-draft-quote` (explicit no-order confirmations + SVG hash)
3. `POST /api/v1/intake-v6/workspaces/{id}/priced-quote/write` (expected gross + pricing hash)
4. No Offer/Order created

## Snapshot POST / read-back / idempotency

| Step | Result |
|------|--------|
| `POST .../quotes/1/snapshot-v2` | **200** — `V6_QUOTE_SNAPSHOT_V2_CREATED` |
| Snapshot code | `QSN2-2026-0001` |
| Readiness | `partial_with_owner_decisions` |
| 7G gross frozen | **2649.99 RON** |
| 7H status frozen | **blocked** (5 owner decisions; 0 material blockers) |
| `GET /api/v1/product-system/quote-snapshot-v2/QSN2-2026-0001` | **200** — stored JSON |
| Read hash stability | `hash_read_1 == hash_read_2` (**stable**) |
| Second POST | **200 blocked** — `V6_SNAPSHOT_ALREADY_EXISTS` |
| Snapshot count delta | **+1** (no duplicate row) |

Full machine evidence: `docs/qa/product-system-active-path-isolation-v1/w3_int_01b_gate_evidence.json`  
Repro script: `backend/scripts/w3_int_01b_live_gate_smoke.py`

## Graph-cost projection freeze (live persisted snapshot)

| Field | Location in persisted JSON |
|-------|---------------------------|
| Composition graph | `product_aggregate_snapshot.composition_graph` — **DIRECTLY_FROZEN** |
| Active modules | `estimated_internal_cost_snapshot.input_summary.active_modules` |
| BOM provenance | `estimated_internal_cost_snapshot.provenance[key=aggregate_cost_bom]` |

**Classification:** `FROZEN_INSIDE_7H_PROVENANCE_SUFFICIENT` — Wave 4 can read frozen modules + graph + 7G/7H without repricing; full `graph_cost_projection` object is not a top-level snapshot field but active module set and BOM provenance are persisted.

## Remaining owner decisions (exact five)

| Code | Downstream classification |
|------|---------------------------|
| `INTERNAL_SABLON_FOREX_COST` | **OWNER_DECISION_REQUIRED** (internal finish rule; commercial 7G already ready) |
| `INTERNAL_AMBALARE_RULE` | **INTERNAL_ANALYSIS_ONLY** |
| `INTERNAL_MONTAJ_RULE` | **REQUIRED_BEFORE_EXECUTION** (future/optional site mounting) |
| `INTERNAL_CONSUMABLES_RULE` | **OWNER_DECISION_REQUIRED** |
| `OVERHEAD_ALLOCATION_PENDING` | **INTERNAL_ANALYSIS_ONLY** |

## Fixture mutation report

| Item | Before | After |
|------|--------|-------|
| Workspace | `80570a4a-a806-4305-a39c-b34a72092694` | `finish_setup.internal_draft_quote_confirmed=true` |
| Quotes | 0 | 1 (`quote_id=1`, gate draft) |
| Snapshots | 0 | 1 (`QSN2-2026-0001`) |
| Offers / Orders | 0 | 0 |

**Cleanup:** NOT_REQUIRED — gate artifacts retained as live proof (`QSN2-2026-0001`, quote `1`).

## Focused tests

| Category | Passed | Failed | Skipped | Collection errors |
|----------|--------|--------|---------|-------------------|
| W3 focused scope | 54 | 2 | 0 | 0 |

Failures: `test_output_composition_*` — **PREEXISTING_FIXTURE_DEBT** (`_latest_quote_snapshot_v2` missing).

## Wave 3 / Wave 4

- **Wave 3:** COMPLETE (live snapshot proof satisfied via controlled :8001 gate)
- **Wave 4:** `OPEN_WAVE_4_INTEGRATION_GATE` (clear ghost :8000 when convenient; not blocking code authority)

## Temporary debt

- Ghost `:8000` PID 4392 — **KEEP** until OS-level socket cleanup / reboot
- Gate quote + snapshot rows in dev.db — **residual proof data**
