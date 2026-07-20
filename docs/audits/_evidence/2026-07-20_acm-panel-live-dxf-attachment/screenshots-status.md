# Screenshots status — live DXF attachment v1

| # | Shot | Status | Notes |
|---|------|--------|-------|
| 1–16 | Operator UI captures | **DEFERRED — stack capture** | UI shipped with `data-testid="intake-v6-acm-production-geometry"` and related ids. Full Playwright capture requires live :3000/:8000 + auth session. |
| — | Runtime JSON proof | **DONE** | `runtime-proof.json` — golden measure, QA bind, stale, IV6 uncontaminated |

## Capture recipe (owner / next session)

Route: `/intake-v6/{workspaceId}/operator` → Review → AcmPanel → Geometrie section open.

Testids:

- `intake-v6-acm-production-geometry`
- `intake-v6-acm-pg-status`
- `intake-v6-acm-pg-file`
- `intake-v6-acm-pg-metrics`
- `intake-v6-acm-pg-stale`
- live-calc: existing `AcmPanelProvisionalPricingBlock`

Do **not** upload golden 2000×300 onto IV6-DB2F86B7.
