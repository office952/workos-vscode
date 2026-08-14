# Wave 5 — payments / advances / labor cost

| Domain | Owner page | Writes | ≠ |
|--------|------------|--------|---|
| LABOR COST | `/employees` | cost_lunar_firma / cost_ora | not client price |
| PAY BASE | `/employees` | monthly_internal_pay_amount | not payment record |
| ADVANCE | `/employee-advances` | balance transactions | not payment |
| PAYMENT | `/employee-payments` | payment records | does not settle advances automatically |

Payments **reads** pontaj + advances for breakdown. Copy is honest.

**PAYMENT_LABOR_COST_SEPARATION = CLEAR** (with intentional read-compose on payments).
