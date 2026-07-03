# TPL-VOLUMETRIC-LETTERS — Template Dossier

**Template code:** `TPL-VOLUMETRIC-LETTERS`  
**Pilot:** litere volumetrice luminoase  
**Status:** documentation — Operation Catalog + adapters (conceptual)

---

## Ce este template-ul

ProductSystem template pentru **litere volumetrice luminoase**: față plexiglas, cant aluminiu, spate Forex, iluminare LED interioară, finisaje variabile (față/cant), variante cu/fără suport comun pe spate.

---

## Documente template

| # | Document | Rol |
|---|----------|-----|
| 01 | [01_TEMPLATE_SCOPE.md](./01_TEMPLATE_SCOPE.md) | Scope pilot și variante |
| 02 | [02_VECTOR_AND_LETTER_MODEL.md](./02_VECTOR_AND_LETTER_MODEL.md) | Raw vs Confirmed, 18/27/9 |
| 03 | [03_FINISH_MODEL.md](./03_FINISH_MODEL.md) | Față, cant, reguli ramificare |
| 04 | [04_MATERIAL_INTENT_MODEL.md](./04_MATERIAL_INTENT_MODEL.md) | Estimări materiale |
| 05 | [05_OPERATION_CATALOG.md](./05_OPERATION_CATALOG.md) | **Catalog operații condiționat** |
| 06 | [06_TASK_SEED_AND_EXECUTION_BOUNDARY.md](./06_TASK_SEED_AND_EXECUTION_BOUNDARY.md) | Seed vs plan real |
| 07 | [07_NO_SHARED_SUPPORT_TASK_LOGIC.md](./07_NO_SHARED_SUPPORT_TASK_LOGIC.md) | Index fără suport comun |
| 08 | [08_SHARED_SUPPORT_PENDING_MODEL.md](./08_SHARED_SUPPORT_PENDING_MODEL.md) | Suport comun — pending |
| 09 | [09_PRICING_INPUT_ADAPTER.md](./09_PRICING_INPUT_ADAPTER.md) | → quote_input |
| 10 | [10_PRODUCTION_HANDOFF_ADAPTER.md](./10_PRODUCTION_HANDOFF_ADAPTER.md) | Preview seed |
| 11 | [11_EMPLOYEE_MOBILE_PREVIEW_BOUNDARY.md](./11_EMPLOYEE_MOBILE_PREVIEW_BOUNDARY.md) | Mobile preview |
| 12 | [12_OPEN_QUESTIONS.md](./12_OPEN_QUESTIONS.md) | Întrebări rămase |

### Document sursă detaliat (păstrat)

[TASK_LOGIC_NO_SHARED_SUPPORT.md](./TASK_LOGIC_NO_SHARED_SUPPORT.md) — logică operațională detaliată fără suport comun.

---

## Relații

- **Work Intake general:** [../../01_WORK_INTAKE_GENERAL_MODEL.md](../../01_WORK_INTAKE_GENERAL_MODEL.md)
- **Architecture contracts:** [../../../architecture/INTAKE_V3_ARCHITECTURE_CONTRACTS.md](../../../architecture/INTAKE_V3_ARCHITECTURE_CONTRACTS.md)
- **Operation Catalog** alimentează ProductionHandoff seed; ExecutionPlanService creează taskuri reale după Order.

---

## Variante acoperite de dossier

| Variantă | Document principal |
|----------|-------------------|
| Fără suport comun | 07 + TASK_LOGIC detaliat |
| Cu suport comun | 08 — pending owner |
