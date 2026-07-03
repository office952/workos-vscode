"""Tests for /operator employee selection and authorization guard."""
from __future__ import annotations

import json
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from models import employees, execution_plan, execution_reality, operational_registry  # noqa: F401
from models.employees import Employees
from models.execution_plan import ExecutionPlan
from models.execution_reality import ExecutionReality
from seeds.seed_operational_workforce_registry import seed_operational_workforce_registry
from services.execution_plan_service import ExecutionPlanService
from services.execution_reality_service import ExecutionRealityService
from services.operator_employee_guard import OperatorEmployeeGuard
from tests._db_fixture import IsolatedDBFixture


def _sample_snapshot():
    return {
        "product_definition": {
            "quantity": 1,
            "layers": [
                {
                    "layer_id": "L1",
                    "processes": [
                        {
                            "process_id": "P1",
                            "type": "print",
                            "estimated_time_minutes": 30,
                            "machine_type": "printer_large_format",
                        }
                    ],
                }
            ],
        },
        "cost_result": {"estimated_time_minutes": 30},
    }


class TestOperatorEmployeeSelection(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = IsolatedDBFixture(prefix="mgx_op_emp_sel_")
        cls.db.setup()

    @classmethod
    def tearDownClass(cls):
        cls.db.teardown()

    def setUp(self):
        self.db.reset_tables(
            [
                ExecutionReality,
                ExecutionPlan,
                operational_registry.FieldInstallationTeamMember,
                operational_registry.FieldInstallationTeam,
                operational_registry.OperationResourceRequirement,
                operational_registry.EmployeeResourceAuthorization,
                operational_registry.EmployeeSkillAuthorization,
                operational_registry.EmployeeWorkcenterAuthorization,
                operational_registry.MachineRegistry,
                Employees,
            ]
        )

    def _run(self, coro):
        return self.db.run(coro)

    def _create_plan(self, order_id: int = 1, order_code: str = "ORD-001"):
        async def _do():
            from types import SimpleNamespace

            order = SimpleNamespace(
                id=order_id,
                code=order_code,
                snapshot_version=1,
                snapshot_line_items=json.dumps(_sample_snapshot()),
            )
            dto = ExecutionPlanService().from_order(order)
            async with self.db.session_maker() as session:
                row = ExecutionPlan(
                    order_id=dto.order_id,
                    order_code=dto.order_code,
                    snapshot_version=dto.snapshot_version,
                    tasks_json=json.dumps([t.to_dict() for t in dto.tasks]),
                    total_estimated_time_minutes=dto.total_estimated_time_minutes,
                )
                session.add(row)
                await session.commit()
                return dto.tasks[0].task_id

        return self._run(_do())

    def test_start_with_valid_employee_id_persists_in_reality(self):
        self._run(seed_operational_workforce_registry())
        task_id = self._create_plan()

        async def _do():
            from sqlalchemy import select

            async with self.db.session_maker() as session:
                calin = (
                    await session.execute(
                        select(Employees).where(Employees.name == "Calin Cimpean")
                    )
                ).scalar_one()

                guard = OperatorEmployeeGuard(session)
                result = await guard.validate_for_task_start(
                    employee_id=calin.id,
                    process_type="print",
                    machine_type="printer_large_format",
                )
                self.assertTrue(result.allowed)
                self.assertEqual(result.employee_name, "Calin Cimpean")

                svc = ExecutionRealityService(session)
                await svc.start_task(
                    order_id=1,
                    order_code="ORD-001",
                    task_id=task_id,
                    timestamp="2026-06-09T10:00:00+00:00",
                )

                reality = (
                    await session.execute(
                        select(ExecutionReality).where(ExecutionReality.order_id == 1)
                    )
                ).scalar_one()
                tasks = json.loads(reality.tasks_json)
                entry = next(t for t in tasks if t["task_id"] == task_id)
                entry["employee_id"] = calin.id
                entry["employee_name"] = calin.name
                entry["operator_name"] = calin.name
                reality.tasks_json = json.dumps(tasks)
                await session.commit()

                refreshed = (
                    await session.execute(
                        select(ExecutionReality).where(ExecutionReality.order_id == 1)
                    )
                ).scalar_one()
                saved = json.loads(refreshed.tasks_json)[0]
                self.assertEqual(saved["employee_id"], calin.id)
                self.assertEqual(saved["employee_name"], "Calin Cimpean")

        self._run(_do())

    def test_invalid_employee_id_blocked(self):
        self._run(seed_operational_workforce_registry())

        async def _do():
            async with self.db.session_maker() as session:
                guard = OperatorEmployeeGuard(session)
                result = await guard.validate_for_task_start(employee_id=99999)
                self.assertFalse(result.allowed)
                self.assertIn("employee_not_found", result.errors)

        self._run(_do())

    def test_start_without_employee_id_legacy_allowed(self):
        async def _do():
            async with self.db.session_maker() as session:
                guard = OperatorEmployeeGuard(session)
                result = await guard.validate_for_task_start(employee_id=None)
                self.assertTrue(result.allowed)
                self.assertTrue(result.legacy_operator)
                self.assertIn("operator_legacy_no_employee_id", result.warnings)

        self._run(_do())

    def test_authorization_mismatch_is_warning_not_block(self):
        self._run(seed_operational_workforce_registry())

        async def _do():
            from sqlalchemy import select

            async with self.db.session_maker() as session:
                florin = (
                    await session.execute(
                        select(Employees).where(Employees.name == "Florin CNC")
                    )
                ).scalar_one()
                guard = OperatorEmployeeGuard(session)
                result = await guard.validate_for_task_start(
                    employee_id=florin.id,
                    process_type="print",
                    machine_type="printer_large_format",
                )
                self.assertTrue(result.allowed)
                self.assertEqual(result.authorization_status, "not_authorized")
                self.assertIn("employee_authorization_mismatch", result.warnings)

        self._run(_do())


if __name__ == "__main__":
    unittest.main()
