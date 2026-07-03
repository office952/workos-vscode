"""Tests for Operational Workforce & Resource Registry foundation."""
from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from models import employees, operational_registry  # noqa: E402,F401
from models.employees import Employees
from models.operational_registry import (
    EmployeeResourceAuthorization,
    EmployeeSkillAuthorization,
    EmployeeWorkcenterAuthorization,
    FieldInstallationTeam,
    FieldInstallationTeamMember,
    MachineRegistry,
    OperationResourceRequirement,
)
from seeds.seed_operational_workforce_registry import (
    OPERATION_MAPPINGS,
    REAL_EMPLOYEES,
    REAL_RESOURCES,
    seed_operational_workforce_registry,
)
from services.operational_registry_service import OperationalRegistryService
from tests._db_fixture import IsolatedDBFixture


class TestOperationalResourceRegistry(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = IsolatedDBFixture(prefix="mgx_op_registry_")
        cls.db.setup()

    @classmethod
    def tearDownClass(cls):
        cls.db.teardown()

    def setUp(self):
        self.db.reset_tables(
            [
                FieldInstallationTeamMember,
                FieldInstallationTeam,
                OperationResourceRequirement,
                EmployeeResourceAuthorization,
                EmployeeSkillAuthorization,
                EmployeeWorkcenterAuthorization,
                MachineRegistry,
                Employees,
            ]
        )

    def _run(self, coro):
        return self.db.run(coro)

    def test_seed_creates_real_employees_once(self):
        stats1 = self._run(seed_operational_workforce_registry())
        stats2 = self._run(seed_operational_workforce_registry())

        self.assertEqual(stats1["employees_created"], 8)
        self.assertEqual(stats1["resources_upserted"], len(REAL_RESOURCES))
        self.assertEqual(stats1["operation_mappings_upserted"], len(OPERATION_MAPPINGS))
        self.assertEqual(stats2["employees_created"], 0)
        self.assertEqual(stats2["employees_updated"], 8)

        async def _check():
            from sqlalchemy import select

            async with self.db.session_maker() as session:
                rows = (await session.execute(select(Employees))).scalars().all()
                names = {r.name for r in rows}
                self.assertEqual(len(rows), 8)
                for spec in REAL_EMPLOYEES:
                    self.assertIn(spec["name"], names)

                calin = (
                    await session.execute(
                        select(Employees).where(Employees.name == "Calin Cimpean")
                    )
                ).scalar_one()
                self.assertEqual(calin.cost_lunar_firma, 8500.0)
                self.assertEqual(calin.salary_currency, "RON")
                self.assertEqual(calin.salary_period, "monthly")
                self.assertIsNone(calin.user_id)

        self._run(_check())

    def test_many_to_many_authorizations(self):
        self._run(seed_operational_workforce_registry())

        async def _check():
            from sqlalchemy import func, select

            async with self.db.session_maker() as session:
                svc = OperationalRegistryService(session)
                calin = (
                    await session.execute(
                        select(Employees).where(Employees.name == "Calin Cimpean")
                    )
                ).scalar_one()
                auth = await svc.get_employee_authorizations(calin.id)
                self.assertIn("SK_PRINT_OPERATOR", auth["skill_codes"])
                self.assertIn("MCH-EPSON-60800", auth["resource_codes"])

                # Multiple employees on same resource
                authorized = await svc.get_authorized_employees_for_resource("MCH-EPSON-60800")
                names = {e["name"] for e in authorized}
                self.assertIn("Calin Cimpean", names)
                self.assertIn("Octavian Dumitru", names)
                self.assertGreaterEqual(len(names), 2)

                # Same employee on multiple resources
                self.assertGreaterEqual(len(auth["resource_codes"]), 3)

                # Count authorizations table rows
                skill_count = (
                    await session.execute(select(func.count(EmployeeSkillAuthorization.id)))
                ).scalar()
                resource_count = (
                    await session.execute(select(func.count(EmployeeResourceAuthorization.id)))
                ).scalar()
                self.assertGreaterEqual(skill_count, 20)
                self.assertGreaterEqual(resource_count, 20)

        self._run(_check())

    def test_operation_mapping_links_product_system_codes(self):
        self._run(seed_operational_workforce_registry())

        async def _check():
            async with self.db.session_maker() as session:
                svc = OperationalRegistryService(session)
                mapping = await svc.get_operation_mapping("colantare")
                self.assertIsNotNone(mapping)
                assert mapping is not None
                self.assertIn("SK_VINYL_APPLICATOR", mapping["required_skill_codes"])
                self.assertIn("WC_VINYL_APPLICATION", mapping["allowed_workcenter_codes"])
                self.assertIn("vinyl_application", mapping["product_system_aliases"])
                self.assertIn("vinyl_cutting", mapping["product_system_aliases"])
                self.assertIn(
                    "Montaj autocolant atelier",
                    mapping["notes"] or "",
                )

                assembly = await svc.get_operation_mapping("assembly")
                self.assertIsNotNone(assembly)
                assert assembly is not None
                self.assertIn("volumetric_letter_assembly", assembly["product_system_aliases"])
                self.assertIn("assembly_letters", assembly["product_system_aliases"])

                field = await svc.get_operation_mapping("field_installation")
                self.assertIsNotNone(field)
                assert field is not None
                self.assertIn("SK_FIELD_INSTALLER", field["required_skill_codes"])

        self._run(_check())

    def test_seed_operation_mappings_idempotent_no_duplicates(self):
        self._run(seed_operational_workforce_registry())
        self._run(seed_operational_workforce_registry())

        async def _check():
            from sqlalchemy import func, select

            async with self.db.session_maker() as session:
                count = (
                    await session.execute(select(func.count(OperationResourceRequirement.id)))
                ).scalar()
                self.assertEqual(count, len(OPERATION_MAPPINGS))

        self._run(_check())

    def test_field_installation_team_multi_employee(self):
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
                    "INTAKE-MONTAJ-001",
                    [putaru.id, vali.id],
                    site_address="Str. Exemplu 10, București",
                    roles_on_site={putaru.id: "lead", vali.id: "installer"},
                )
                self.assertEqual(team["status"], "draft")
                self.assertEqual(len(team["members"]), 2)
                member_names = {m["employee_name"] for m in team["members"]}
                self.assertEqual(member_names, {"Putaru Sandu", "Vali Colantator"})

        self._run(_check())

    def test_resources_include_machines_tools_and_work_areas(self):
        self._run(seed_operational_workforce_registry())

        async def _check():
            async with self.db.session_maker() as session:
                svc = OperationalRegistryService(session)
                items = await svc.list_resources()
                kinds = {r["resource_kind"] for r in items}
                self.assertIn("machine", kinds)
                self.assertIn("tool", kinds)
                self.assertIn("work_area", kinds)

                cnc = await svc.get_resource("MCH-CNC-4020")
                self.assertIsNotNone(cnc)
                assert cnc is not None
                self.assertEqual(cnc["capacity_metadata"]["table_width_mm"], 4000)

        self._run(_check())

    def test_list_employees_with_authorizations_returns_registry_shape(self):
        self._run(seed_operational_workforce_registry())

        async def _check():
            async with self.db.session_maker() as session:
                svc = OperationalRegistryService(session)
                payload = await svc.list_employees_with_authorizations()
                self.assertIn("items", payload)
                self.assertIn("total", payload)
                self.assertGreater(payload["total"], 0)
                first = payload["items"][0]
                self.assertIn("user_id", first)
                self.assertIn("skill_codes", first)
                self.assertIn("resource_codes", first)

        self._run(_check())

    def test_dev_schema_repair_restores_missing_employee_columns(self):
        self._run(seed_operational_workforce_registry())

        async def _check():
            from core.database import db_manager
            from sqlalchemy import text

            async with db_manager.engine.begin() as conn:
                cols = (
                    await conn.execute(text("PRAGMA table_info(employees)"))
                ).fetchall()
                col_names = {row[1] for row in cols}
                self.assertIn("user_id", col_names)

                await conn.execute(text("ALTER TABLE employees DROP COLUMN user_id"))

            await db_manager.check_and_repair_existing_tables()

            async with db_manager.engine.begin() as conn:
                cols = (
                    await conn.execute(text("PRAGMA table_info(employees)"))
                ).fetchall()
                col_names = {row[1] for row in cols}
                self.assertIn("user_id", col_names)

            async with self.db.session_maker() as session:
                svc = OperationalRegistryService(session)
                payload = await svc.list_employees_with_authorizations()
                self.assertGreater(payload["total"], 0)

        self._run(_check())


if __name__ == "__main__":
    unittest.main()
