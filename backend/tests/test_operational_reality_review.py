"""Operational Reality Review — read-only gap detection tests."""
from __future__ import annotations

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
from services.operational_reality_review_service import OperationalRealityReviewService
from services.operational_registry_service import (
    OperationalRegistryService,
    build_order_installation_ref,
)
from tests._db_fixture import IsolatedDBFixture


class TestOperationalRealityReview(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = IsolatedDBFixture(prefix="mgx_op_reality_review_")
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
                employees.Employees,
            ]
        )

    def _run(self, coro):
        return self.db.run(coro)

    def _review(self) -> dict:
        async def _fetch():
            async with self.db.session_maker() as session:
                svc = OperationalRealityReviewService(session)
                return await svc.build_review()

        return self._run(_fetch())

    def test_detect_task_missing_employee_id(self):
        async def _seed():
            async with self.db.session_maker() as session:
                svc = ExecutionRealityService(session)
                await svc.start_task(501, "ORD-501", "T-NO-EMP", "2026-06-09T10:00:00+00:00")

        self._run(_seed())
        review = self._review()
        types = {g["gap_type"] for g in review["gaps"]}
        self.assertIn("TASK_MISSING_EMPLOYEE", types)
        self.assertGreaterEqual(review["summary"]["tasks_without_employee"], 1)

    def test_detect_task_started_not_completed(self):
        async def _seed():
            async with self.db.session_maker() as session:
                svc = ExecutionRealityService(session)
                await svc.start_task(
                    502,
                    "ORD-502",
                    "T-OPEN",
                    "2026-06-09T10:00:00+00:00",
                    initial_fields={"employee_id": 1, "employee_name": "Test Op"},
                )

        self._run(_seed())
        review = self._review()
        types = {g["gap_type"] for g in review["gaps"]}
        self.assertIn("TASK_STARTED_NOT_COMPLETED", types)
        self.assertEqual(review["summary"]["tasks_started_not_completed"], 1)

    def test_detect_task_completed_without_notes(self):
        async def _seed():
            async with self.db.session_maker() as session:
                svc = ExecutionRealityService(session)
                await svc.start_task(503, "ORD-503", "T-DONE", "2026-06-09T10:00:00+00:00")
                await svc.end_task(503, "T-DONE", "2026-06-09T11:00:00+00:00")

        self._run(_seed())
        review = self._review()
        types = {g["gap_type"] for g in review["gaps"]}
        self.assertIn("TASK_COMPLETED_WITHOUT_COMPLETION_NOTES", types)

    def test_detect_materials_without_task_id(self):
        async def _seed():
            async with self.db.session_maker() as session:
                row = ExecutionReality(
                    order_id=504,
                    order_code="ORD-504",
                    tasks_json="[]",
                    materials_json=json.dumps(
                        [{"material_name": "Vinil", "quantity": 1.0, "unit": "mp"}]
                    ),
                )
                session.add(row)
                await session.commit()

        self._run(_seed())
        review = self._review()
        types = {g["gap_type"] for g in review["gaps"]}
        self.assertIn("MATERIAL_WITHOUT_TASK_ID", types)
        self.assertEqual(review["summary"]["materials_without_task_id"], 1)

    def test_detect_materials_without_reporter(self):
        async def _seed():
            async with self.db.session_maker() as session:
                row = ExecutionReality(
                    order_id=505,
                    order_code="ORD-505",
                    tasks_json="[]",
                    materials_json=json.dumps(
                        [
                            {
                                "material_name": "Adeziv",
                                "quantity": 0.5,
                                "unit": "L",
                                "task_id": "T-1",
                            }
                        ]
                    ),
                )
                session.add(row)
                await session.commit()

        self._run(_seed())
        review = self._review()
        types = {g["gap_type"] for g in review["gaps"]}
        self.assertIn("MATERIAL_WITHOUT_REPORTER", types)
        self.assertEqual(review["summary"]["materials_without_reporter"], 1)

    def test_detect_field_installation_completed_without_photos(self):
        self._run(seed_operational_workforce_registry())

        async def _seed():
            from sqlalchemy import select

            async with self.db.session_maker() as session:
                emp = (
                    await session.execute(select(Employees).limit(1))
                ).scalar_one()
                reg = OperationalRegistryService(session)
                team = await reg.create_field_installation_team(
                    build_order_installation_ref(506),
                    [emp.id],
                    status="planned",
                )
                await reg.start_field_installation_reporting(team["id"])
                await reg.complete_field_installation_reporting(
                    team["id"],
                    client_observations="OK",
                    completion_photos=[],
                )

        self._run(_seed())
        review = self._review()
        types = {g["gap_type"] for g in review["gaps"]}
        self.assertIn("FIELD_INSTALLATION_COMPLETED_WITHOUT_PHOTOS", types)

    def test_detect_field_installation_without_team_members(self):
        async def _seed():
            async with self.db.session_maker() as session:
                reg = OperationalRegistryService(session)
                await reg.create_field_installation_team(
                    build_order_installation_ref(507),
                    [],
                    status="planned",
                )

        self._run(_seed())
        review = self._review()
        types = {g["gap_type"] for g in review["gaps"]}
        self.assertIn("FIELD_INSTALLATION_WITHOUT_TEAM_MEMBERS", types)
        severities = {g["severity"] for g in review["gaps"] if g["gap_type"] == "FIELD_INSTALLATION_WITHOUT_TEAM_MEMBERS"}
        self.assertIn("critical", severities)

    def test_dashboard_does_not_expose_salary(self):
        async def _seed():
            async with self.db.session_maker() as session:
                svc = ExecutionRealityService(session)
                await svc.start_task(508, "ORD-508", "T-1", "2026-06-09T10:00:00+00:00")

        self._run(_seed())
        review = self._review()
        blob = json.dumps(review).lower()
        for forbidden in ("salary", "salariu", "wage", "cost_engine", "profit", "pricing"):
            self.assertNotIn(forbidden, blob)

    def test_service_is_read_only(self):
        methods = [
            name
            for name, fn in inspect.getmembers(OperationalRealityReviewService, inspect.isfunction)
            if not name.startswith("_")
        ]
        self.assertEqual(methods, ["build_review"])
        import ast
        import services.operational_reality_review_service as mod

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
                self.fail(f"Unexpected DB mutation call: .{node.func.attr}()")

    def test_no_cost_engine_quote_pricing_imports(self):
        import ast
        import services.operational_reality_review_service as mod

        tree = ast.parse(inspect.getsource(mod))
        forbidden_modules = {
            "cost_engine",
            "costengine",
            "quote_orchestrator",
            "pricing",
        }
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    mod_name = alias.name.lower()
                    self.assertFalse(
                        any(f in mod_name for f in forbidden_modules),
                        msg=f"Forbidden import: {alias.name}",
                    )
            if isinstance(node, ast.ImportFrom) and node.module:
                mod_name = node.module.lower()
                self.assertFalse(
                    any(f in mod_name for f in forbidden_modules),
                    msg=f"Forbidden import from: {node.module}",
                )

    def test_endpoint_router_is_get_only(self):
        import routers.operational_reality_review as router_mod

        source = inspect.getsource(router_mod)
        self.assertIn('@router.get("/review")', source)
        self.assertNotIn("@router.post", source)
        self.assertNotIn("@router.put", source)
        self.assertNotIn("@router.patch", source)
        self.assertNotIn("@router.delete", source)
