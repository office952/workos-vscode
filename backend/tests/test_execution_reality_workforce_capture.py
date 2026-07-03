"""Execution reality workforce capture — atelier tasks + field installation reporting."""
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
from services.execution_reality_service import ExecutionRealityService
from services.execution_reality_workforce import resolve_task_workforce_context
from services.operational_registry_service import (
    OperationalRegistryService,
    build_order_installation_ref,
)
from tests._db_fixture import IsolatedDBFixture


class TestExecutionRealityWorkforceCapture(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = IsolatedDBFixture(prefix="mgx_exec_reality_wf_")
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

    def test_start_task_preserves_employee_and_workforce_context(self):
        self._run(seed_operational_workforce_registry())

        async def _check():
            from sqlalchemy import select

            async with self.db.session_maker() as session:
                calin = (
                    await session.execute(
                        select(Employees).where(Employees.name == "Calin Cimpean")
                    )
                ).scalar_one()
                ctx = await resolve_task_workforce_context(
                    session, process_type="print", machine_type="MCH-EPSON-60800"
                )
                svc = ExecutionRealityService(session)
                await svc.start_task(
                    101,
                    "ORD-101",
                    "T-PRINT-1",
                    "2026-06-09T10:00:00+00:00",
                    initial_fields={
                        **ctx,
                        "employee_id": calin.id,
                        "employee_name": calin.name,
                        "operator_name": calin.name,
                    },
                )
                row = await svc.get_by_order(101)
                assert row is not None
                tasks = json.loads(row.tasks_json)
                self.assertEqual(tasks[0]["employee_id"], calin.id)
                self.assertEqual(tasks[0]["employee_name"], calin.name)
                self.assertEqual(tasks[0]["operation_code"], "print")
                self.assertIn("workcenter_code", tasks[0])

        self._run(_check())

    def test_complete_task_saves_completion_notes(self):
        async def _check():
            async with self.db.session_maker() as session:
                svc = ExecutionRealityService(session)
                await svc.start_task(102, "ORD-102", "T-1", "2026-06-09T10:00:00+00:00")
                await svc.end_task(
                    102,
                    "T-1",
                    "2026-06-09T11:00:00+00:00",
                    completion_fields={
                        "completion_notes": "QC OK",
                        "completed_by_employee_id": 5,
                    },
                )
                row = await svc.get_by_order(102)
                assert row is not None
                tasks = json.loads(row.tasks_json)
                self.assertEqual(tasks[0]["completion_notes"], "QC OK")
                self.assertEqual(tasks[0]["completed_by_employee_id"], 5)

        self._run(_check())

    def test_materials_linked_to_task_and_employee_no_stock(self):
        async def _check():
            async with self.db.session_maker() as session:
                svc = ExecutionRealityService(session)
                await svc.start_task(103, "ORD-103", "T-MAT", "2026-06-09T10:00:00+00:00")
                await svc.add_materials(
                    103,
                    [
                        {
                            "material_name": "Silicon montaj",
                            "quantity": 2,
                            "unit": "buc",
                            "task_id": "T-MAT",
                            "reported_by_employee_id": 3,
                            "reported_by_employee_name": "Operator Test",
                            "consumption_notes": "Consum teren",
                        }
                    ],
                )
                mats = await svc.get_materials(103)
                self.assertEqual(len(mats), 1)
                self.assertEqual(mats[0]["task_id"], "T-MAT")
                self.assertEqual(mats[0]["reported_by_employee_id"], 3)
                self.assertNotIn("salary_amount", json.dumps(mats))

        self._run(_check())

    def test_legacy_task_without_employee_remains_readable(self):
        async def _check():
            async with self.db.session_maker() as session:
                svc = ExecutionRealityService(session)
                await svc.start_task(104, "ORD-104", "T-LEG", "2026-06-09T10:00:00+00:00")
                row = await svc.get_by_order(104)
                assert row is not None
                tasks = json.loads(row.tasks_json)
                self.assertNotIn("employee_id", tasks[0])
                self.assertEqual(tasks[0]["task_id"], "T-LEG")

        self._run(_check())

    def test_field_installation_start_end_with_photos_and_observations(self):
        self._run(seed_operational_workforce_registry())

        async def _check():
            from sqlalchemy import select

            async with self.db.session_maker() as session:
                svc = OperationalRegistryService(session)
                putaru = (
                    await session.execute(
                        select(Employees).where(Employees.name == "Putaru Sandu")
                    )
                ).scalar_one()
                vali = (
                    await session.execute(
                        select(Employees).where(Employees.name == "Vali Colantator")
                    )
                ).scalar_one()
                team = await svc.create_field_installation_team(
                    build_order_installation_ref(200),
                    [putaru.id, vali.id],
                )
                started = await svc.start_field_installation_reporting(
                    team["id"],
                    started_by_employee_id=putaru.id,
                    members_present=[putaru.id, vali.id],
                )
                self.assertEqual(started["status"], "in_progress")
                self.assertTrue(started["reporting_ready"])
                self.assertEqual(len(started["members_present"]), 2)

                completed = await svc.complete_field_installation_reporting(
                    team["id"],
                    client_observations="Client mulțumit",
                    completion_photos=["https://example.com/final.jpg"],
                    completed_by_employee_id=putaru.id,
                )
                self.assertEqual(completed["status"], "completed")
                self.assertEqual(completed["client_observations"], "Client mulțumit")
                self.assertEqual(completed["completion_photos"], ["https://example.com/final.jpg"])
                self.assertNotIn("salary_amount", json.dumps(completed))

        self._run(_check())

    def test_field_installation_start_warns_without_members(self):
        self._run(seed_operational_workforce_registry())

        async def _check():
            async with self.db.session_maker() as session:
                svc = OperationalRegistryService(session)
                team = await svc.create_field_installation_team(
                    build_order_installation_ref(201), []
                )
                started = await svc.start_field_installation_reporting(team["id"])
                self.assertIn("no_team_members_allocated", started["warnings"])

        self._run(_check())

    def test_field_installation_separate_from_colantare(self):
        self._run(seed_operational_workforce_registry())

        async def _check():
            async with self.db.session_maker() as session:
                svc = OperationalRegistryService(session)
                field = await svc.get_operation_mapping("field_installation")
                colantare = await svc.get_operation_mapping("colantare")
                assert field and colantare
                self.assertIn("WC_FIELD_INSTALLATION", field["allowed_workcenter_codes"])
                self.assertIn("WC_VINYL_APPLICATION", colantare["allowed_workcenter_codes"])

        self._run(_check())


if __name__ == "__main__":
    unittest.main()
