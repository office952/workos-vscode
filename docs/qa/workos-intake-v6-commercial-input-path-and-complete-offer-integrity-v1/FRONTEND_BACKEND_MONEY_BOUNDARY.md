# FRONTEND_BACKEND_MONEY_BOUNDARY

| Surface | Before | After |
|---------|--------|-------|
| Live offer rail | FE `applyIntakeV6CommercialAdjustments` on base | Backend `commercial_totals` only |
| Pricing slider panel | Same FE recompute | Backend totals only |
| Confirm offer card | Prefer CPP `complete_offer_total` | Prefer `commercial_totals.total_gross` (adjusted) |
| `applyIntakeV6CommercialAdjustments` | Official display authority | Non-authoritative helper (tests/legacy) |
| Manual RON FX | FE could mix RON into EUR | Backend Policy A conversion only |

Official displayed money originates from backend CPP base + dry-run adjustments.
