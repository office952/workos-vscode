"""Operational Reports Foundation — read-only aggregation tests."""
from __future__ import annotations

import ast
import inspect
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from models import employees, execution_plan, execution_reality, operational_registry  # noqa: F401
from models.employees import Employees
from models.execution_reality import ExecutionReality
from models.operational_registry import FieldInstallationTeam, FieldInstallationTeamMember
from seeds.seed_operational_workforce_registry import seed_operational_workforce_registry
from services.execution_reality_service import ExecutionRealityService
from services.operational_reports_service import OperationalReportsService
from services.operational_registry_service import (
    OperationalRegistryService,
    build_order_installation_ref,
)
from tests._db_fixture import IsolatedDBFixture


class TestOperationalReports(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = IsolatedDBFixture(prefix="mgx_op_reports_")
        cls.db.setup()

    @classmethod
    def tearDownClass(cls):
        cls.db.teardown()

    def setUp(self):
        self.db.reset_tables(
            [
                ExecutionReality,
                execution_plan.ExecutionPlan,
                FieldInstallationTeamMember,
                FieldInstallationTeam,
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

    def _summary(self, **kwargs) -> dict:
        async def _fetch():
            async with self.db.session_maker() as session:
                svc = OperationalReportsService(session)
                return await svc.build_summary(**kwargs)

        return self._run(_fetch())

    def test_employee_activity_aggregates_tasks(self):
        self._run(seed_operational_workforce_registry())

        async def _seed():
            from sqlalchemy import select

            async with self.db.session_maker() as session:
                emp = (
                    await session.execute(select(Employees).limit(1))
                ).scalar_one()
                svc = ExecutionRealityService(session)
                await svc.start_task(
                    801,
                    "ORD-801",
                    "T-1",
                    "2026-06-09T10:00:00+00:00",
                    initial_fields={
                        "employee_id": emp.id,
                        "employee_name": emp.name,
                        "operation_code": "print",
                    },
                )
                await svc.end_task(
                    801,
                    "T-1",
                    "2026-06-09T11:00:00+00:00",
                    completion_fields={
                        "completed_by_employee_id": emp.id,
                        "completed_by_employee_name": emp.name,
                    },
                )

        self._run(_seed())
        report = self._summary(category="employee_activity")
        self.assertEqual(len(report["employee_activity"]), 1)
        row = report["employee_activity"][0]
        self.assertEqual(row["tasks_started"], 1)
        self.assertEqual(row["tasks_completed"], 1)
        self.assertGreater(row["observed_minutes_total"], 0)

    def test_materials_report_includes_reporter(self):
        async def _seed():
            async with self.db.session_maker() as session:
                row = ExecutionReality(
                    order_id=802,
                    order_code="ORD-802",
                    tasks_json="[]",
                    materials_json=json.dumps(
                        [
                            {
                                "material_name": "Vinil alb",
                                "material_code": "VIN-001",
                                "quantity": 2.5,
                                "unit": "mp",
                                "task_id": "T-1",
                                "reported_by_employee_id": 42,
                                "reported_by_employee_name": "Ion Popescu",
                                "reported_at": "2026-06-09T12:00:00+00:00",
                                "consumption_notes": "folosit pe litere",
                            }
                        ]
                    ),
                )
                session.add(row)
                await session.commit()

        self._run(_seed())
        report = self._summary(category="materials")
        self.assertEqual(len(report["materials_reality"]), 1)
        mat = report["materials_reality"][0]
        self.assertEqual(mat["reported_by_employee_name"], "Ion Popescu")
        self.assertEqual(mat["consumption_notes"], "folosit pe litere")

    def test_field_installation_report_team_and_photos(self):
        self._run(seed_operational_workforce_registry())

        async def _seed():
            from sqlalchemy import select

            async with self.db.session_maker() as session:
                emp = (
                    await session.execute(select(Employees).limit(1))
                ).scalar_one()
                reg = OperationalRegistryService(session)
                team = await reg.create_field_installation_team(
                    build_order_installation_ref(803),
                    [emp.id],
                    status="planned",
                )
                await reg.start_field_installation_reporting(team["id"])
                await reg.complete_field_installation_reporting(
                    team["id"],
                    client_observations="Client mulțumit",
                    completion_photos=["https://example.com/a.jpg", "https://example.com/b.jpg"],
                )

        self._run(_seed())
        report = self._summary(category="field_installation")
        self.assertEqual(len(report["field_installation"]), 1)
        row = report["field_installation"][0]
        self.assertEqual(row["team_members_count"], 1)
        self.assertEqual(row["completion_photos_count"], 2)
        self.assertTrue(row["client_observations_present"])

    def test_employee_activity_excludes_salary_cost_profit(self):
        self._run(seed_operational_workforce_registry())

        async def _seed():
            from sqlalchemy import select

            async with self.db.session_maker() as session:
                emp = (
                    await session.execute(select(Employees).limit(1))
                ).scalar_one()
                svc = ExecutionRealityService(session)
                await svc.start_task(
                    805,
                    "ORD-805",
                    "T-1",
                    "2026-06-09T10:00:00+00:00",
                    initial_fields={"employee_id": emp.id, "employee_name": emp.name},
                )

        self._run(_seed())
        report = self._summary(category="employee_activity")
        blob = json.dumps(report["employee_activity"]).lower()
        for forbidden in (
            "salary",
            "salary_amount",
            "profit",
            "cost",
            "hourly",
            "internal_cost",
            "wage",
        ):
            self.assertNotIn(forbidden, blob)

    def test_task_reality_includes_employee_name_and_status(self):
        async def _seed():
            async with self.db.session_maker() as session:
                svc = ExecutionRealityService(session)
                await svc.start_task(
                    806,
                    "ORD-806",
                    "T-STATUS",
                    "2026-06-09T10:00:00+00:00",
                    initial_fields={"employee_id": 3, "employee_name": "Maria"},
                )

        self._run(_seed())
        report = self._summary(category="task_reality")
        row = report["task_reality"][0]
        self.assertEqual(row["employee_name"], "Maria")
        self.assertEqual(row["status"], "in_progress")

    def test_materials_report_does_not_adjust_stock(self):
        import services.operational_reports_service as mod

        tree = ast.parse(inspect.getsource(mod))
        forbidden_modules = {"inventory", "stock", "costengine", "cost_engine"}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    mod_name = alias.name.lower()
                    self.assertFalse(any(f in mod_name for f in forbidden_modules))
            if isinstance(node, ast.ImportFrom) and node.module:
                mod_name = node.module.lower()
                self.assertFalse(any(f in mod_name for f in forbidden_modules))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if node.func.attr in {"deduct", "adjust_stock", "update_inventory"}:
                    self.fail(f"Unexpected stock mutation call: .{node.func.attr}()")

    def test_completeness_summary_counts(self):
        async def _seed():
            async with self.db.session_maker() as session:
                svc = ExecutionRealityService(session)
                await svc.start_task(
                    804,
                    "ORD-804",
                    "T-WITH-EMP",
                    "2026-06-09T10:00:00+00:00",
                    initial_fields={"employee_id": 7, "employee_name": "Ana"},
                )
                await svc.start_task(804, "ORD-804", "T-NO-EMP", "2026-06-09T10:05:00+00:00")
                await svc.end_task(804, "T-WITH-EMP", "2026-06-09T11:00:00+00:00")
                await svc.add_materials(
                    804,
                    [
                        {
                            "material_name": "Adeziv",
                            "quantity": 1,
                            "unit": "l",
                            "task_id": "T-WITH-EMP",
                            "reported_by_employee_id": 7,
                        }
                    ],
                )

        self._run(_seed())
        report = self._summary(category="completeness")
        s = report["completeness_summary"]
        self.assertEqual(s["total_tasks"], 2)
        self.assertEqual(s["tasks_with_employee"], 1)
        self.assertEqual(s["tasks_without_employee"], 1)
        self.assertEqual(s["tasks_with_materials"], 1)
        self.assertEqual(s["tasks_without_materials"], 1)

    def test_completeness_summary_material_reporter_and_task_id(self):
        async def _seed():
            async with self.db.session_maker() as session:
                row = ExecutionReality(
                    order_id=807,
                    order_code="ORD-807",
                    tasks_json="[]",
                    materials_json=json.dumps(
                        [
                            {
                                "material_name": "Cu reporter",
                                "quantity": 1,
                                "unit": "mp",
                                "task_id": "T-1",
                                "reported_by_employee_id": 9,
                                "reported_at": "2026-06-09T12:00:00+00:00",
                            },
                            {
                                "material_name": "Fara reporter",
                                "quantity": 1,
                                "unit": "mp",
                                "reported_at": "2026-06-09T12:05:00+00:00",
                            },
                        ]
                    ),
                )
                session.add(row)
                await session.commit()

        self._run(_seed())
        s = self._summary(category="completeness")["completeness_summary"]
        self.assertEqual(s["total_materials_reported"], 2)
        self.assertEqual(s["materials_with_reporter"], 1)
        self.assertEqual(s["materials_without_reporter"], 1)
        self.assertEqual(s["materials_with_task_id"], 1)
        self.assertEqual(s["materials_without_task_id"], 1)

    def test_payload_does_not_expose_salary_cost_profit(self):
        report = self._summary()
        blob = json.dumps(report).lower()
        for forbidden in (
            "salary",
            "salary_amount",
            "profit",
            "cost_engine",
            "pricing",
            "wage",
            "hourly",
            "internal_cost",
            "margin",
        ):
            self.assertNotIn(forbidden, blob)

    def test_quote_pricing_costengine_untouched(self):
        import services.operational_reports_service as mod

        tree = ast.parse(inspect.getsource(mod))
        forbidden_modules = {"cost_engine", "quote", "pricing", "costengine"}
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                mod_name = node.module.lower()
                self.assertFalse(any(f in mod_name for f in forbidden_modules))

    def test_tpl_dispatch_untouched(self):
        import services.operational_reports_service as mod

        source = inspect.getsource(mod).lower()
        for forbidden in (
            "volumetric_execution_dispatch",
            "task_dispatch",
            "execution_plan_service",
        ):
            self.assertNotIn(forbidden, source)

    def test_service_is_read_only(self):
        import services.operational_reports_service as mod

        methods = [
            name
            for name, fn in inspect.getmembers(OperationalReportsService, inspect.isfunction)
            if not name.startswith("_")
        ]
        self.assertEqual(methods, ["build_summary"])
        tree = ast.parse(inspect.getsource(mod))

        def _is_db_mutation(call: ast.Call) -> bool:
            if not isinstance(call.func, ast.Attribute):
                return False
            if call.func.attr not in {"add", "delete", "commit"}:
                return False
            target = call.func.value
            if isinstance(target, ast.Attribute) and target.attr == "db":
                return True
            if isinstance(target, ast.Name) and target.id in {"session", "db"}:
                return True
            return False

        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and _is_db_mutation(node):
                self.fail(f"Unexpected DB mutation: .{node.func.attr}()")

    def test_router_is_get_only(self):
        import routers.operational_reports as router_mod

        source = inspect.getsource(router_mod)
        self.assertIn('@router.get("/summary")', source)
        self.assertNotIn("@router.post", source)
        self.assertNotIn("@router.patch", source)
