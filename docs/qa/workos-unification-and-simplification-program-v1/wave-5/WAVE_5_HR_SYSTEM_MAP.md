# Wave 5 — HR system map

| Concept | Surface | SoT | Writes |
|---------|---------|-----|--------|
| EMPLOYEE MASTER | `/employees` | entities/employees | CRUD |
| ATTENDANCE | `/attendance` | employee-attendance | events |
| ATTENDANCE EFFECTS | `/attendance/effects` | effects API | generate/apply |
| ASSIGNMENT / ELIGIBILITY | `/employees` hints | is_assignable + operational-registry | authorizations |
| SESSION / WORKING | **not HR** | Execution / operator | Wave 3 |
| LABOR COST | `/employees` Cost Intern fields | employee entity | PUT |
| INTERNAL PAY BASE | `/employees` | employee entity | PUT |
| PAYMENT | `/employee-payments` | employee-payments | record/cancel |
| ADVANCE | `/employee-advances` | employee-balances | transactions |
| HR FILE | `/employees-records` + `/:id` | live names + demo dossier | none (add/view file disabled) |

**HR_MODEL = PARTIAL** — live master/pontaj/payments/advances are real; Evidență HR is `DEMO_DOSSIER_ON_REAL_EMPLOYEE` (detail proven `/employees-records/7`). Assignment/session live on Execution. Profile “avans” is demo, not `/employee-advances`.
