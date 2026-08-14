# Global source-of-truth matrix

| CONCEPT | CANONICAL_OWNER | RUNTIME_SOURCE | UI_PROJECTION | DOWNSTREAM | MUTATION_OWNER | FROZEN/LIVE | PARALLEL_TRUTH | STATUS |
|---------|-----------------|----------------|---------------|------------|----------------|-------------|----------------|--------|
| REQUEST | Commercial | intakes / cereri list | `/intake` | IV6 workspace | Intake create (SNR) | LIVE | IR vs IV6 id | PARTIAL |
| WORKSPACE | Commercial | Intake V6 workspace | `/intake-v6/:id/operator` | Quote handoff | Operator confirm | LIVE until handoff | header IV6 ≠ URL IR | PARTIAL |
| PRODUCT TEMPLATE | Compiler | Product System catalog | `/product-system/products` | PD / PA | Admin catalog (frozen) | LIVE catalog | FLUX Produse | COHERENT |
| COMPONENT DEFINITION | Compiler | template graph | PS structure steps | PA nodes | Admin | LIVE | planned shells | PARTIAL |
| PRODUCT DEFINITION | Compiler | `GET …/product-definition` | **no page** — V6 + PS proxies | PA / pricing input | none (preview) | LIVE preview | /modules verifyRoute | COHERENT |
| PRODUCT AGGREGATE | Compiler | workspace composition + task_contract | V6 / API | ExecutionPlan | Intake bind | LIVE then snapshotted | hidden in shop UI | COHERENT |
| COMMERCIAL MEASUREMENT | Commercial | V6 CPP / quote input | V6 rail | Quote | Confirm | LIVE preview | labeled “OFERTĂ CLIENT” | CONFLICTED |
| PRICING REGISTRY | Resources | pricing registry API | `/inventory/pricing` | compile support | Admin | LIVE | ≠ snapshot | COHERENT |
| QUOTE | Commercial | quotes + snapshot at accept | `/quotes` | Order | Sales (SNR convert) | LIVE then freeze | EUR display | PARTIAL |
| ORDER SNAPSHOT | Commercial | OrderSnapshotV2 | `/orders` | Execution | lock (done) | **FROZEN** | reports live totals | COHERENT |
| EXECUTION PLAN | Execution | execution_plan persist | `/execution/:id` | tasks | generate (SNR) | FROZEN graph | — | COHERENT |
| EXECUTION TASK | Execution | operator/tasks | `/operator` `/tablet` mobile | sessions | start/complete (SNR) | LIVE | WC enum leak | PARTIAL |
| MACHINE RUN | Execution | machine-runs | `/execution/machine-runs` | occupancy | create (SNR) | LIVE | utilaje util% | PARTIAL |
| EMPLOYEE SESSION | Execution | task sessions | operator / mobile | labor actual | start (SNR) | LIVE | ≠ pontaj | COHERENT |
| ATTENDANCE | People | employee-attendance | `/attendance` | payments compose | events (SNR) | LIVE | FE/BE RBAC MIXED | CONFLICTED |
| LABOR ACTUAL | Execution / People | session minutes + employee cost | employees / execution | CostEngine | employee PUT / session | LIVE | three labor languages | PARTIAL |
| EMPLOYEE MASTER | People | entities/employees | `/employees` | HR/pontaj/pay/eligibility | CRUD (SNR) | LIVE | records names | COHERENT |
| PAYMENT | People | employee-payments | `/employee-payments` | — | record/cancel (SNR) | LIVE | ≠ advance ≠ cost | COHERENT |
| ADVANCE | People | employee-balances | `/employee-advances` | payments | admin tx (SNR) | LIVE | demo debts on profile | PARTIAL |
| INVENTORY ITEM | Resources | inventory_materials | `/inventory` | stock / compile | deduct (SNR) | LIVE | unit_cost vs registry | PARTIAL |
| SUPPLIER | Resources | entities/suppliers | Colaboratori + Inventory Furnizori | — | Colaboratori create (SNR) | LIVE | SAME_TRUTH_DIFFERENT_PROJECTION | COHERENT |
| SETTINGS | Settings | company + CostEngine | `/settings` | VAT/FX stamp | save (SNR) | LIVE | Societate mock | PARTIAL |
| REPORT PROJECTION | Management | reports-summary | `/reports` | none | none | LIVE rollup | ≠ snapshot | PARTIAL |
| DOCUMENTS | none | FE `generateMockDocuments` | `/documents` | none | none | MOCK | looks like registry | PLACEHOLDER |
