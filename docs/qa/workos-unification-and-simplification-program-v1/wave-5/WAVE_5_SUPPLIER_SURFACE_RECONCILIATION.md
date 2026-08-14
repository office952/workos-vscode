# Wave 5 — Colaboratori vs Inventory Furnizori

```text
SUPPLIER_SURFACE_RELATION = SAME_TRUTH_DIFFERENT_PROJECTION
COLABORATORI_API = GET /api/v1/entities/suppliers/all
INVENTORY_SUPPLIERS_API = GET /api/v1/entities/suppliers/all
ENTITY_SCHEMA = suppliers (id, code, name, category, lead_time_days, rating, active_orders, last_delivery)
WRITE_PATH = POST/PUT/DELETE /api/v1/entities/suppliers (permission supplier.create / update / delete)
CONSUMERS = Colaboratori.tsx via useColaboratoriData; Inventory Furnizori via useInventoryData
```

## Not a second supplier registry

Both pages read the **same** entity list. Inventory does **not** write suppliers. Colaboratori UI has `Adaugă colaborator` → `suppliersApi.create` (not clicked this GO).

## Projection difference (why not TRUE_DUPLICATE_UI)

| | Colaboratori | Inventory Furnizori |
|--|--------------|---------------------|
| PURPOSE_LABELS | Relații / colaboratori | Resurse / inventar / furnizori |
| VISIBLE_FIELDS | companyName, CUI←code, contact/phone/email (mapped `"—"`), city `"România"`, derived `totalValueRON`, status from rating/orders | name, rating stars, category, lead days, active orders |
| Extra invented UI | contact, phone, email, city, order value | none |
| Write CTA | create form exists | none |

Same rows, different job: relationship CRM-shaped projection vs procurement context card. Collapsing the UIs is **not** authorized here.

W5-C3 stays ACTIVE as duplicate **entry**, reclassified from “true duplicate UI” to **same truth / different projection**.
