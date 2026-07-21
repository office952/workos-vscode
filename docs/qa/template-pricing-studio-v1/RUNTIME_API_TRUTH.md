# TEMPLATE_PRICING_STUDIO_V1 — Runtime API Truth (gate)

| Field | Value |
|-------|--------|
| Date | 2026-07-22 |
| Branch | `feature/product-system-active-path-isolation-v1` |
| Kickoff HEAD | `585115da` (accepted Pricing Foundation final) |
| Backend restart | Required — stale uvicorn lacked `typed_catalog` |
| Restart method | Stop PIDs on `:8000`, then `npm run dev:backend` |
| Backend git_commit (boot) | `585115da` |

## Before restart

```text
GET http://127.0.0.1:8000/api/v1/pricing/registry
item_count=50
typed_catalog_populated=0/50
sample keys lacked typed_catalog / cost_label_ro / data_quality_flags
```

Cause: long-lived uvicorn worker started before Pricing Foundation land; no reload of enrich path.

## After clean restart

```text
GET http://127.0.0.1:8000/api/v1/pricing/registry
item_count=50
typed_catalog_populated=50/50
typed=material:33
typed=labor:9
typed=machine_operation:5
typed=service:3
mismatch_flagged=8 (subset visible in default registry slice)
sample:
  pricing_code=MAT-ACM-BOND-3MM
  typed_catalog=material
  cost_meaning=purchase_cost
  cost_label_ro=Cost achiziție
```

## Gate decision

**GO** — canonical backend typed catalog metadata is available.  
Frontend fallback is no longer the permanent source of truth for Studio planning.
