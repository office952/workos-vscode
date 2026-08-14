# Global route classification

One **PRIMARY_CLASS** per audited route family. Allowed: CORE_WORKFLOW · CORE_PROJECTION · ADMIN_CONFIGURATION · REFERENCE_REGISTRY · MANAGEMENT · REPORTING · AUDIT_ONLY · COMPATIBILITY · DEMO · PLACEHOLDER · FUTURE · UNKNOWN.

| ROUTE | PRIMARY_CLASS | PRIMARY_USER | PURPOSE | SoT | MUTATION_RUNTIME | KEEP | MOVE | MERGE | DEMOTE | HIDE | REMOVE | OWNER_DEC |
|-------|---------------|--------------|---------|-----|------------------|------|------|-------|--------|------|--------|-----------|
| `/dashboard` | CORE_PROJECTION | admin | Audit/KPI home | mixed chips | no | YES | — | — | YES (not work entry) | — | NO | YES — home vs work |
| `/intake` | CORE_WORKFLOW | sales/admin | Select cerere | intakes | list only | YES | — | — | — | — | NO | NO |
| `/intake/:id` | COMPATIBILITY | — | Redirect V6 | — | no | YES | — | — | — | — | NO | NO |
| `/intake-v6/:id/operator` | CORE_WORKFLOW | sales/admin | Confirm Product Truth | V6 workspace | confirm/handoff SNR | YES | — | — | — | — | NO | NO |
| `/quotes` · `/:id` | CORE_WORKFLOW | sales | Offer lifecycle | quotes | convert SNR | YES | — | — | — | — | NO | NO |
| `/orders` · `/:id` | CORE_WORKFLOW | sales/manager | Frozen sold work | order snapshot | no reprice | YES | — | — | — | — | NO | NO |
| `/clients` · `/:name` | MANAGEMENT | sales | Counterparty 360 | clients + activity | no | YES | into Lucrări? | — | — | — | NO | YES |
| `/shop-floor` | CORE_PROJECTION | operator/manager | Canonical monitor | operator poll | no | YES | — | — | — | — | NO | YES — vs action |
| `/execution` | CORE_PROJECTION | manager | Plan list | execution plans | no | YES | — | — | — | — | NO | NO |
| `/execution/:id` | CORE_PROJECTION | manager | Plan/reality | plan + reality | writes SNR | YES | — | — | — | — | NO | NO |
| `/execution/machine-runs` | REFERENCE_REGISTRY | operator/manager | MachineRun | machine-runs | create SNR | YES | — | — | — | — | NO | NO |
| `/execution/ops-graph` | AUDIT_ONLY | manager/admin | Graph audit | materialized graph | assign SNR | YES | Sistem | — | YES | everyday nav | NO | YES |
| `/execution/reality-review` | AUDIT_ONLY | admin | Diagnostic | reality | no | YES | Sistem | — | YES | everyday nav | NO | YES |
| `/operator` | COMPATIBILITY | operator | De-facto action | /operator/tasks | start SNR | YES | — | not into Atelier | — | after canonical action | NO | YES |
| `/tablet` · children | COMPATIBILITY | operator | Station action | same API | start SNR | YES | — | — | — | after canonical | NO | YES |
| `/employee-app-v2/*` | CORE_WORKFLOW | employee | Specialized mobile | mobile APIs | start SNR | YES | — | — | — | — | NO | NO |
| `/employee-app/*` | COMPATIBILITY | employee | v1 sibling | mobile v1 | SNR | YES | — | — | YES | after v2 | NO | YES |
| `/product-system/products` | ADMIN_CONFIGURATION | admin | Design-time language | catalog | frozen | YES | out of Lucrări | — | from FLUX | — | NO | YES |
| `/product-system/…/structure/*` | ADMIN_CONFIGURATION | admin | Template workshops | catalog | no | YES | — | — | chrome | — | NO | NO |
| `/product-system/{components,operations,dependencies,validation,advanced}` | FUTURE | admin | Planned shells | none | no | — | — | — | — | YES | NO | NO |
| `/product-system/blueprint-dossier` | AUDIT_ONLY | admin | DEV dossier | — | no | YES | Sistem | — | — | YES | NO | NO |
| `/product-system/output-blocks-preview` | AUDIT_ONLY | admin | Lab preview | — | no | YES | Sistem | — | — | YES | NO | NO |
| `/modules` | ADMIN_CONFIGURATION | admin | System map | static+live mix | no | YES | — | — | — | — | NO | YES — freeze banner |
| `/governance` | ADMIN_CONFIGURATION | admin | Ownership/gates | stale+live | no | YES | — | — | stale tab | — | NO | YES |
| `/employees` | REFERENCE_REGISTRY | manager/admin | Employee master | entities/employees | CRUD SNR | YES | — | — | — | — | NO | NO |
| `/attendance` | MANAGEMENT | manager/admin | Pontaj | attendance API | events SNR | YES | — | — | — | — | NO | YES — RBAC |
| `/attendance/effects` | MANAGEMENT | admin | Effect pipeline | effects API | generate SNR | YES | — | — | — | — | NO | NO |
| `/employees-records` · `/:id` | DEMO | manager/admin | Demo dossier | master names + FE demo | no | YES | — | — | — | until real | NO | YES |
| `/employee-payments` | MANAGEMENT | manager/admin | Pay tranches | payments | record SNR | YES | Oameni | — | — | — | NO | YES |
| `/employee-advances` | MANAGEMENT | admin | Debt ledger | balances | create SNR | YES | Oameni | — | — | — | NO | YES |
| `/utilaje` | REFERENCE_REGISTRY | operator/manager | Machine catalog | /machines | no occupancy | YES | — | ≠ MachineRun | — | — | NO | NO |
| `/inventory` | REFERENCE_REGISTRY | ops | Stock | inventory_materials | deduct SNR | YES | — | — | Automatizare | — | NO | NO |
| `/inventory/pricing` | ADMIN_CONFIGURATION | admin | Rate registry | pricing registry | admin | YES | — | — | — | — | NO | NO |
| `/colaboratori` | MANAGEMENT | manager/admin | Supplier CRM projection | suppliers | create SNR | YES | — | not Inventory | — | — | NO | YES |
| `/documents` | PLACEHOLDER | sales/manager | Mock hub | none | disabled | — | — | — | — | YES | NO | YES |
| `/reports` | REPORTING | sales/manager | Live ops KPIs | orders.total_amount | no | YES | — | — | — | — | NO | YES — money label |
| `/reports/operational` | AUDIT_ONLY | admin/DEV | Completeness | plans/reality | no | YES | Sistem | — | — | YES | NO | NO |
| `/settings` | ADMIN_CONFIGURATION | admin | VAT/FX + CostEngine | settings | save SNR | YES | — | — | Societate mock | — | NO | NO |
| `/demo/*` | DEMO | admin/DEV | Lab demos | — | no | — | — | — | — | YES | later | NO |

**Counts (families, not every nested id):**

| Class | Count |
|-------|------:|
| CORE_WORKFLOW | 5 |
| CORE_PROJECTION | 4 |
| ADMIN_CONFIGURATION | 6 |
| REFERENCE_REGISTRY | 4 |
| MANAGEMENT | 6 |
| REPORTING | 1 |
| AUDIT_ONLY | 5 |
| COMPATIBILITY | 4 |
| DEMO | 2 |
| PLACEHOLDER | 1 |
| FUTURE | 1 |
| REMOVE_CANDIDATE (routes) | 0 |
