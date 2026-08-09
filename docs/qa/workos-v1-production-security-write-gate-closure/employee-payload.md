# Employee payload — before / after (no private values)

## Before (any authenticated role)

List/detail JSON could include:

- `cost_lunar_firma`
- `salary_amount`
- `monthly_internal_pay_amount`
- `cost_ora_calculat`
- `ore_productive_luna` (+ source)
- `observatii`

Operational registry also returned `salary_amount` / currency / period.

## After

### Operator / sales / viewer / mobile (`include_hr_cost=false`)

HR-restricted keys present as `null` / omitted meaning (schema may still declare optional keys) — **values never populated** from DB for unauthorized roles.

Asserted in `tests/test_v1_production_security_write_gate.py`:

- `salary_amount is None`
- `cost_lunar_firma is None`
- `monthly_internal_pay_amount is None`
- `cost_ora_calculat is None`
- `observatii is None`

Operational identity retained: `name`, `status`, skills/machines, assignable flags.

### Admin / manager (`employee.view_hr_cost`)

Full HR projection retained for Cost Intern / Employees UI / payments.

### Payments

`/api/v1/employee-payments/*` requires `employee_payments.read` / `.write` (admin/manager only).
