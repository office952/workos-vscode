"""Field installation team allocation — montaj teren multi-employee."""
from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from models import employees, operational_registry  # noqa: E402,F401
from models.employees import Employees
from seeds.seed_operational_workforce_registry import seed_operational_workforce_registry
from services.operational_registry_service import (
    OperationalRegistryService,
    build_order_installation_ref,
)
from tests._db_fixture import IsolatedDBFixture


class FieldInstallationTeamAllocationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = IsolatedDBFixture(prefix="mgx_field_install_")
        cls.db.setup()

    @classmethod
    def tearDownClass(cls):
        cls.db.teardown()

    def _run(self, coro):
        import asyncio

        return asyncio.get_event_loop().run_until_complete(coro)

    def test_create_team_without_members_then_add_multiple(self):
        self._run(seed_operational_workforce_registry())

        async def _check():
            from sqlalchemy import select

            async with self.db.session_maker() as session:
                svc = OperationalRegistryService(session)
                ref = build_order_installation_ref(9001)
                team = await svc.create_field_installation_team(ref, [])
                self.assertEqual(team["status"], "draft")
                self.assertEqual(team["order_id"], 9001)
                self.assertEqual(team["member_count"], 0)
                self.assertNotIn("salary_amount", str(team))

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

                updated = await svc.add_field_installation_team_member(
                    team["id"], putaru.id, role_on_site="montator"
                )
                updated = await svc.add_field_installation_team_member(
                    updated["id"], vali.id, role_on_site="electrician"
                )
                self.assertEqual(updated["member_count"], 2)
                self.assertEqual(len(updated["members"]), 2)

                listed = await svc.list_field_installation_teams(ref)
                self.assertEqual(len(listed), 1)
                self.assertEqual(listed[0]["member_count"], 2)

        self._run(_check())

    def test_remove_employee_from_team(self):
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
                    build_order_installation_ref(9002),
                    [putaru.id, vali.id],
                )
                updated = await svc.remove_field_installation_team_member(
                    team["id"], vali.id
                )
                self.assertEqual(updated["member_count"], 1)
                self.assertEqual(updated["members"][0]["employee_id"], putaru.id)

        self._run(_check())

    def test_reject_inactive_employee(self):
        self._run(seed_operational_workforce_registry())

        async def _check():
            from sqlalchemy import select

            async with self.db.session_maker() as session:
                svc = OperationalRegistryService(session)
                team = await svc.create_field_installation_team(
                    build_order_installation_ref(9003), []
                )
                emp = (
                    await session.execute(select(Employees).limit(1))
                ).scalar_one()
                emp.status = "inactive"
                await session.commit()

                with self.assertRaises(ValueError) as ctx:
                    await svc.add_field_installation_team_member(team["id"], emp.id)
                self.assertEqual(str(ctx.exception), "employee_inactive")

        self._run(_check())

    def test_reject_invalid_employee(self):
        self._run(seed_operational_workforce_registry())

        async def _check():
            async with self.db.session_maker() as session:
                svc = OperationalRegistryService(session)
                team = await svc.create_field_installation_team(
                    build_order_installation_ref(9004), []
                )
                with self.assertRaises(ValueError) as ctx:
                    await svc.add_field_installation_team_member(team["id"], 999999)
                self.assertEqual(str(ctx.exception), "employee_not_found")

        self._run(_check())

    def test_update_team_status(self):
        self._run(seed_operational_workforce_registry())

        async def _check():
            async with self.db.session_maker() as session:
                svc = OperationalRegistryService(session)
                team = await svc.create_field_installation_team(
                    build_order_installation_ref(9005), []
                )
                updated = await svc.update_field_installation_team(
                    team["id"], status="planned", notes="Montaj programat manual"
                )
                self.assertEqual(updated["status"], "planned")
                self.assertEqual(updated["notes"], "Montaj programat manual")

        self._run(_check())

    def test_field_installation_separate_from_colantare_mapping(self):
        self._run(seed_operational_workforce_registry())

        async def _check():
            async with self.db.session_maker() as session:
                svc = OperationalRegistryService(session)
                field = await svc.get_operation_mapping("field_installation")
                colantare = await svc.get_operation_mapping("colantare")
                self.assertIsNotNone(field)
                self.assertIsNotNone(colantare)
                assert field is not None and colantare is not None
                self.assertIn("WC_FIELD_INSTALLATION", field["allowed_workcenter_codes"])
                self.assertIn("WC_VINYL_APPLICATION", colantare["allowed_workcenter_codes"])
                self.assertNotEqual(
                    field["allowed_workcenter_codes"],
                    colantare["allowed_workcenter_codes"],
                )

        self._run(_check())


if __name__ == "__main__":
    unittest.main()
