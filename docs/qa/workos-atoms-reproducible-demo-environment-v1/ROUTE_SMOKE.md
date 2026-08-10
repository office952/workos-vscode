# Route smoke — Atoms demo §23

**Date:** 2026-08-10  
**Frontend base:** `http://127.0.0.1:3010`  
**Backend base:** `http://127.0.0.1:8010` → `backend/demo/workos_demo.db`  
**Owner stack:** left on `:8000`/`:3000` (`dev.db`) — untouched  

## Identities

| Entity | Code / id |
|--------|-----------|
| Intake Letters | `DEMO-INTAKE-LETTERS-001` / `d0e10001-0000-4000-8000-000000000001` |
| Intake draft | `DEMO-INTAKE-DRAFT-001` / `d0e10002-0000-4000-8000-000000000002` |
| Quote | `DEMO-QUOTE-EUR-001` / id `1` |
| Order | `DEMO-ORDER-001` / id `1` |

## Matrix

| Route | HTTP | DEMO signal in body | Screenshot |
|-------|------|---------------------|------------|
| `/dashboard` | 200 | list chrome (KPIs from demo DB) | `screenshots/01-dashboard.png` |
| `/intake` | 200 | list loads | `screenshots/02-intake.png` |
| `/intake-v6/...0001/operator` | 200 | YES | `screenshots/03-intake-v6-letters.png` |
| `/intake-v6/...0002/operator` | 200 | YES | `screenshots/04-intake-v6-draft.png` |
| `/product-system/products` | 200 | Letters templates | `screenshots/05-product-system-products.png` |
| `/inventory/pricing` | 200 | registry | `screenshots/06-inventory-pricing.png` |
| `/quotes` | 200 | YES | `screenshots/07-quotes.png` |
| `/quotes/1` | 200 | YES | `screenshots/08-quotes-1.png` |
| `/orders` | 200 | YES | `screenshots/09-orders.png` |
| `/orders/1` | 200 | YES | `screenshots/10-orders-1.png` |
| `/execution` | 200 | YES | `screenshots/11-execution.png` |
| `/execution/1` | 200 | YES | `screenshots/12-execution-1.png` |
| `/execution/machine-runs` | 200 | empty/list OK | `screenshots/13-machine-runs.png` |
| `/modules` | 200 | natural | `screenshots/14-modules.png` |
| `/governance` | 200 | natural | `screenshots/15-governance.png` |

API companion: `backend/demo/smoke_demo_api.py` → all listed API paths **200** (copy: `api_smoke_results.json`).

```text
ROUTE_SMOKE = PASS
```
