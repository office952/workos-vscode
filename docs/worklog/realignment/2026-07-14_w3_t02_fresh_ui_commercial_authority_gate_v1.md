# W3-T02-UI-GATE — Fresh UI Commercial Authority Gate

**Date:** 2026-07-14  
**Accepted HEAD:** `2c3d538`  
**Verdict:** `W3_T02_UI_LIVE_PASS_WITH_NONBLOCKING_UX_DEBT`

## Runtime ownership

| Service | PID | Port | Worktree | Code | Notes |
|---------|-----|------|----------|------|-------|
| Backend uvicorn (reload) | 4392 | 8000 | C:\w\psiso | 2c3d538 | Serves dry-run 1888.68 / diag 5926.91 |
| Backend uvicorn (extra) | 21732 | 8000 | C:\w\psiso | unknown | Duplicate listener — env debt |
| Frontend Vite | 6264 | 3000 | C:\w\psiso | 2c3d538 | Required `VITE_API_BASE_URL=http://127.0.0.1:8000` |

## Live cases

### Case A — IR-MRJS4VIK (7G ready)
- Official gross UI: **1.888,68 RON** (`intake-v6-live-offer-gross`, `intake-v6-offer-final-price`)
- Official net: **1.560,89 RON**
- Internal reference: **725,67 EUR** (`intake-v6-live-material-total`) — separate label
- **5926,91 not shown** anywhere in DOM
- Handoff CTA card: **1.888,68 RON** (`intake-v6-priced-quote-total`) — matches backend
- Refresh/reopen: stable 1888.68 after async dry-run fetch

### Case B — fail-closed loading
- No safe blocked-7G runtime fixture in dev.db
- During async load: official total absent, message **"Prețul comercial oficial nu este disponibil."** — no cost-plus leak
- Unit tests: `intakeV6OfficialPricing.test.ts`, `test_dry_run_does_not_use_cost_plus_when_7g_blocked`

### Case C — incomplete authority
- `intakeV6HasOfficialCommercialTotals` rejects totals without `pricing_authority` (vitest)

## Screenshots

`docs/qa/product-system-active-path-isolation-v1/w3-t02-ui-gate-evidence/`

1. `w3-t02-ui-01-review-official-1888.png` — review sidebar official + internal separation
2. `w3-t02-ui-02-confirm-handoff-1888.png` — confirm handoff priced total
3. `w3-t02-ui-04-refresh-stable-1888.png` — post-refresh stable official total

## Temporary debt

**TD-W3-V6-DIAG-COST-PLUS-001:** `KEEP_UNTIL_W3_T03` — no frontend consumer; API-only diagnostic field.

## Nonblocking UX debt

- Transient fail-closed message while dry-run fetch in flight (~2–8s)
- Default Vite dev API base `8001` vs backend `8000` (requires env override for live UI gate)
