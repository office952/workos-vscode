# Wave 4 gap closure — ProductDefinition UI home

**PRODUCT_DEFINITION_DEDICATED_ROUTE = NO**

No `/product-definition` or `/product-system/product-definition` in `App.tsx`.  
Honesty baseline: “Compile / previzualizare — fără pagină dedicată” (`truthPagesHonestyBaseline.ts`).

Backend is preview-only: `GET /api/v1/product-system/product-definition/{template_code}`  
(`product_system_product_definition.py` — no persist, no price, no order/task).

| Where humans inspect PD | Role |
|-------------------------|------|
| Intake V6 Review / composition | Primary operator/sales proxy (`verifyRoute` = `/intake-v6`) |
| Product System V2 chips + runtime preview panels | Admin/catalog proxy (“PREVIEW ONLY”) |
| `/modules` Product Compiler · Definiție | Audit nav to Intake, not a PD page |
| API GET preview | Diagnostic |
| Docs / architecture map | Claimed compose vs actual preview |

**PRODUCT_DEFINITION_UI_HOME = MULTIPLE_PROXIES**

Primary human surface = **Intake V6**. Product System is a contract/preview proxy. `/modules` is an audit pointer.

Owner compass (accepted): do **not** create a ProductDefinition page only because the compiler is architecturally important. A compiler without a page is a valid current truth.
