# LABOR_RECIPE_CONTRACT_V1 — Runtime / Repo Truth

| Field | Value |
|-------|--------|
| Date | 2026-07-22 |
| Branch | `feature/product-system-active-path-isolation-v1` |
| Kickoff HEAD | `212654a2` |
| Dirty tree | ~368 pre-existing paths (protected; allowlist-only writes) |
| Proof port | `127.0.0.1:8020` |

## Ports

| Port | State | Notes |
|------|-------|-------|
| `127.0.0.1:8000` | **Ghost LISTENING** (multiple dead PIDs via `netstat`) | New uvicorn cannot bind reliably; environment-only |
| `127.0.0.1:8020` | **Alive** — uvicorn no-reload, post-labor checkout | Canonical proof port this session |
| FE proxy | `BACKEND_PORT=8020` | Screenshots use this override |

**Classification:** environment-only warning (Windows listener ghost). Not a Labor Recipe Contract defect. Next build must reconfirm canonical `:8000` or keep documenting the alternate proof port.

## API probes (8020)

| Endpoint | Result |
|----------|--------|
| `GET /api/v1/pricing/registry` | 50 items; `typed_catalog` 50/50 |
| ACM pricing | `schema_version=1.1.0`; labor_summary `{total:3, technical_ready:3, commercial_ready:0, missing_rate:2, warnings:1}`; ACM 5/0; treatment=false |
| VL pricing | labor_summary `{total:12, technical_ready:1, commercial_ready:4, missing_rate:0, warnings:12}` (registry-linked + commercial refs) |
| Logo pricing | labor_summary `{total:3}` via commercial_line catalog refs |
| Volum Aluminiu pricing | labor_summary `{total:2}` from ops (bonding + painting); forming classified machine → excluded |

## CPP / EIC regression

Compared to Studio V1 runtime dumps:

| Template | cpp_preview | eic_preview | acm_acceptance | recipe len/status |
|----------|-------------|----------------|----------------|-------------------|
| ACM | **unchanged** | **unchanged** | **unchanged** | 11 / same |
| VL | **unchanged** | **unchanged** | **unchanged** | 59 / same |

Labor fields are additive only.

## Boundary

No rate/seed edits. No HR. No ACM unblock. No DB migration. No push / no PR.
