"""Tests for CostEngine config + employees + recurring payments services.

These tests anchor the canonical rules described in
`/workspace/workos_foundation_log.md` and the newly extended config spec:

- Only ACTIVE PRODUCTIVE employees with both `cost_lunar_firma` and
  `ore_productive_luna` contribute to `average_labour_hour_cost`.
- Invalid rows (productive + active, missing data) MUST produce warnings
  and be excluded from the aggregate — never treated as 0.
- Only ACTIVE recurring payments with `include_in_overhead=True` (and NOT
  also machine-cost-linked) contribute to `monthly_overhead_cost`.
- `anual` payments are normalized as `amount / 12`.
- `overhead_hour_cost` is strictly `monthly_overhead_cost / total_productive_hours_month`.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Register ORM models BEFORE fixture creates tables.
from models import (  # noqa: E402,F401
    cost_engine_config,
    employees,
    recurring_payments,
)
from services.cost_engine_config import CostEngineConfigService  # noqa: E402
from services.employees import (  # noqa: E402
    EmployeesService,
    compute_cost_ora_calculat,
    is_valid_for_cost_engine,
)
from services.recurring_payments import (  # noqa: E402
    RecurringPaymentsService,
    monthly_equivalent,
)
from tests._db_fixture import IsolatedDBFixture  # noqa: E402


class TestPureHelpers(unittest.TestCase):
    def test_compute_cost_ora_calculat(self):
        self.assertAlmostEqual(compute_cost_ora_calculat(8000, 160), 50.0)
        self.assertIsNone(compute_cost_ora_calculat(None, 160))
        self.assertIsNone(compute_cost_ora_calculat(8000, None))
        self.assertIsNone(compute_cost_ora_calculat(8000, 0))
        self.assertIsNone(compute_cost_ora_calculat(8000, -3))

    def test_is_valid_for_cost_engine(self):
        self.assertTrue(is_valid_for_cost_engine({
            "employee_type": "productive", "status": "active",
            "cost_lunar_firma": 7000, "ore_productive_luna": 140,
        }))
        self.assertFalse(is_valid_for_cost_engine({
            "employee_type": "productive", "status": "active",
            "cost_lunar_firma": None, "ore_productive_luna": 140,
        }))
        self.assertFalse(is_valid_for_cost_engine({
            "employee_type": "productive", "status": "active",
            "cost_lunar_firma": 7000, "ore_productive_luna": None,
        }))
        self.assertTrue(is_valid_for_cost_engine({
            "employee_type": "productive", "status": "inactive",
            "cost_lunar_firma": None, "ore_productive_luna": None,
        }))
        self.assertTrue(is_valid_for_cost_engine({
            "employee_type": "management", "status": "active",
            "cost_lunar_firma": None, "ore_productive_luna": None,
        }))

    def test_monthly_equivalent(self):
        self.assertAlmostEqual(monthly_equivalent({"amount": 1000, "periodicity": "lunar"}), 1000.0)
        self.assertAlmostEqual(monthly_equivalent({"amount": 12000, "periodicity": "anual"}), 1000.0)
        self.assertEqual(monthly_equivalent({"amount": None, "periodicity": "lunar"}), 0.0)
        self.assertEqual(monthly_equivalent({"amount": 500, "periodicity": "unknown"}), 0.0)


class TestBaseConfigAggregation(unittest.TestCase):
    """Aggregation tests backed by a per-suite isolated SQLite DB."""

    @classmethod
    def setUpClass(cls):
        cls.db = IsolatedDBFixture(prefix="mgx_costengine_")
        cls.db.setup()

    @classmethod
    def tearDownClass(cls):
        cls.db.teardown()

    def setUp(self):
        # Reset rows between tests — keep schema, drop data.
        from models.employees import Employees
        from models.recurring_payments import RecurringPayments

        self.db.reset_tables([Employees, RecurringPayments])

    def _run(self, coro):
        return self.db.run(coro)

    def _session(self):
        return self.db.session_maker()

    def test_empty_state_is_invalid(self):
        async def _do():
            async with self._session() as db:
                return await CostEngineConfigService(db).compute_base_config()

        result = self._run(_do())
        self.assertFalse(result["valid"])
        self.assertEqual(result["total_productive_hours_month"], 0)
        self.assertEqual(result["average_labour_hour_cost"], 0.0)
        self.assertIn("no_productive_hours_available", result["warnings"])

    def test_only_productive_active_employees_counted(self):
        async def _do():
            async with self._session() as db:
                emp_svc = EmployeesService(db)
                await emp_svc.create({
                    "name": "A", "employee_type": "productive", "status": "active",
                    "cost_lunar_firma": 8000, "ore_productive_luna": 160,
                })
                await emp_svc.create({
                    "name": "B", "employee_type": "productive", "status": "inactive",
                    "cost_lunar_firma": 8000, "ore_productive_luna": 160,
                })
                await emp_svc.create({
                    "name": "C", "employee_type": "management", "status": "active",
                    "cost_lunar_firma": 15000, "ore_productive_luna": 0,
                })
                return await CostEngineConfigService(db).compute_base_config()

        result = self._run(_do())
        self.assertTrue(result["valid"])
        self.assertEqual(result["total_productive_hours_month"], 160.0)
        self.assertAlmostEqual(result["average_labour_hour_cost"], 50.0)

    def test_invalid_productive_employee_raises_warning(self):
        async def _do():
            async with self._session() as db:
                emp_svc = EmployeesService(db)
                await emp_svc.create({
                    "name": "OK", "employee_type": "productive", "status": "active",
                    "cost_lunar_firma": 6000, "ore_productive_luna": 120,
                })
                bad = await emp_svc.create({
                    "name": "BAD", "employee_type": "productive", "status": "active",
                    "cost_lunar_firma": None, "ore_productive_luna": 140,
                })
                result = await CostEngineConfigService(db).compute_base_config()
                return result, bad.id

        result, bad_id = self._run(_do())
        self.assertTrue(result["valid"])
        self.assertEqual(result["total_productive_hours_month"], 120.0)
        self.assertAlmostEqual(result["average_labour_hour_cost"], 50.0)
        self.assertTrue(any(f"employee_invalid:id={bad_id}" in w for w in result["warnings"]))

    def test_overhead_aggregation_mixes_monthly_and_annual(self):
        async def _do():
            async with self._session() as db:
                emp_svc = EmployeesService(db)
                await emp_svc.create({
                    "name": "Prod", "employee_type": "productive", "status": "active",
                    "cost_lunar_firma": 8000, "ore_productive_luna": 160,
                })
                pay_svc = RecurringPaymentsService(db)
                await pay_svc.create({
                    "name": "Chirie", "category": "chirie", "amount": 10000,
                    "periodicity": "lunar", "status": "active",
                    "include_in_overhead": True,
                })
                await pay_svc.create({
                    "name": "Asigurare anuala", "category": "asigurare", "amount": 12000,
                    "periodicity": "anual", "status": "active",
                    "include_in_overhead": True,
                })
                await pay_svc.create({
                    "name": "Leasing CNC", "category": "leasing", "amount": 4000,
                    "periodicity": "lunar", "status": "active",
                    "include_in_overhead": False,
                    "include_in_machine_cost": True,
                    "linked_machine_id": "cnc-1",
                })
                await pay_svc.create({
                    "name": "Old abonament", "category": "abonament", "amount": 500,
                    "periodicity": "lunar", "status": "inactive",
                    "include_in_overhead": True,
                })
                return await CostEngineConfigService(db).compute_base_config()

        result = self._run(_do())
        self.assertAlmostEqual(result["monthly_overhead_cost"], 11000.0)
        self.assertAlmostEqual(result["overhead_hour_cost"], 68.75)

    def test_overhead_skipped_when_also_machine_cost(self):
        async def _do():
            async with self._session() as db:
                emp_svc = EmployeesService(db)
                await emp_svc.create({
                    "name": "Prod", "employee_type": "productive", "status": "active",
                    "cost_lunar_firma": 8000, "ore_productive_luna": 160,
                })
                pay_svc = RecurringPaymentsService(db)
                await pay_svc.create({
                    "name": "Leasing CNC conflict", "category": "leasing", "amount": 4000,
                    "periodicity": "lunar", "status": "active",
                    "include_in_overhead": True,
                    "include_in_machine_cost": True,
                    "linked_machine_id": "cnc-1",
                })
                return await CostEngineConfigService(db).compute_base_config()

        result = self._run(_do())
        self.assertEqual(result["monthly_overhead_cost"], 0.0)

    def test_no_productive_hours_invalidates(self):
        async def _do():
            async with self._session() as db:
                await EmployeesService(db).create({
                    "name": "Mgr", "employee_type": "management", "status": "active",
                    "cost_lunar_firma": 15000, "ore_productive_luna": 0,
                })
                await RecurringPaymentsService(db).create({
                    "name": "Chirie", "category": "chirie", "amount": 5000,
                    "periodicity": "lunar", "status": "active",
                    "include_in_overhead": True,
                })
                return await CostEngineConfigService(db).compute_base_config()

        result = self._run(_do())
        self.assertFalse(result["valid"])
        self.assertEqual(result["total_productive_hours_month"], 0.0)
        self.assertEqual(result["overhead_hour_cost"], 0.0)
        self.assertIn("no_productive_hours_available", result["warnings"])


if __name__ == "__main__":
    unittest.main()