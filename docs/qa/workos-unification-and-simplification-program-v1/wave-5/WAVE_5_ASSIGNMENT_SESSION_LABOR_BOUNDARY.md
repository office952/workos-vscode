# Wave 5 — assignment / session / labor

Map:

```
EMPLOYEE (master)
  → ATTENDANCE (exceptions)
  → ASSIGNMENT (Execution / is_assignable only)
  → SESSION (Atelier/operator — not HR)
  → LABOR ACTUAL (Execution reality minutes)
  → LABOR COST PLAN (employee CostEngine fields)
  → PAYROLL/PAYMENT (payments page)
```

Wave 3 invariant **held** on HR surfaces: they do not write session or task complete.

**ASSIGNMENT_WORKING_SEPARATION = CLEAR**
