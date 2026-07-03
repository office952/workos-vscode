"""Tests for operation authorization foundation (s45)."""
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
    MachineRegistry,
    OperationEmployeeAuthorization,
    OperationResourceRequirement,
)
from seeds.seed_build4_templates import _volumetric_letters_components
from seeds.seed_operational_workforce_registry import seed_operational_workforce_registry
from services.operational_registry_service import OperationalRegistryService
from sqlalchemy import select
from tests._db_fixture import IsolatedDBFixture


class TestOperationalAuthorizationFoundation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = IsolatedDBFixture(prefix="mgx_op_auth_")
        cls.db.setup()

    @classmethod
    def tearDownClass(cls):
        cls.db.teardown()

    def setUp(self):
        self.db.reset_tables(
            [
                OperationEmployeeAuthorization,
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

    def test_capacity_metadata_merge_preserves_unknown_keys(self):
        async def _check():
            async with self.db.session_maker() as session:
                svc = OperationalRegistryService(session)
                await svc.upsert_resource(
                    {
                        "machine_code": "MCH-TEST",
                        "name": "Test",
                        "machine_type": "cnc_router",
                        "capacity_metadata": {
                            "table_width_mm": 4000,
                            "legacy_field": "keep-me",
                        },
                    }
                )
                await svc.upsert_resource(
                    {
                        "machine_code": "MCH-TEST",
                        "name": "Test",
                        "machine_type": "cnc_router",
                        "capacity_metadata": {"table_length_mm": 2000},
                    }
                )
                row = await svc.get_resource("MCH-TEST")
                assert row is not None
                meta = row["capacity_metadata"]
                self.assertEqual(meta["table_width_mm"], 4000)
                self.assertEqual(meta["table_length_mm"], 2000)
                self.assertEqual(meta["legacy_field"], "keep-me")

        self._run(_check())

    def test_hybrid_explicit_and_skill_eligible_pool(self):
        async def _check():
            async with self.db.session_maker() as session:
                svc = OperationalRegistryService(session)
                emp1 = Employees(name="Calin", status="active", employee_type="productive")
                emp2 = Employees(name="Octavian", status="active", employee_type="productive")
                session.add_all([emp1, emp2])
                await session.flush()

                await svc.set_employee_authorizations(
                    emp1.id,
                    skill_codes=["SK_PRINT_OPERATOR"],
                    workcenter_codes=["WC_PRINT"],
                    resource_codes=["MCH-EPSON-60800"],
                )
                await svc.set_employee_authorizations(
                    emp2.id,
                    skill_codes=["SK_PRINT_OPERATOR"],
                    workcenter_codes=["WC_PRINT"],
                    resource_codes=["MCH-EPSON-60800"],
                )

                await svc.upsert_operation_mapping(
                    {
                        "operation_code": "print",
                        "required_skill_codes": ["SK_PRINT_OPERATOR"],
                        "allowed_workcenter_codes": ["WC_PRINT"],
                        "allowed_resource_codes": ["MCH-EPSON-60800"],
                        "authorization_mode": "hybrid",
                        "authorized_employee_ids": [emp1.id, emp2.id],
                    }
                )

                pool = await svc.get_eligible_employees_for_operation("print")
                names = {e["name"] for e in pool["items"]}
                self.assertEqual(pool["total"], 2)
                self.assertIn("Calin", names)
                self.assertIn("Octavian", names)

        self._run(_check())

    def test_resolve_operation_mapping_by_product_system_alias(self):
        async def _check():
            async with self.db.session_maker() as session:
                svc = OperationalRegistryService(session)
                await svc.upsert_operation_mapping(
                    {
                        "operation_code": "cnc_cutting",
                        "required_skill_codes": ["SK_CNC_OPERATOR"],
                        "product_system_aliases": ["face_cnc_cut", "back_cut"],
                    }
                )
                resolved = await svc.resolve_operation_mapping("face_cnc_cut")
                assert resolved is not None
                self.assertEqual(resolved["operation_code"], "cnc_cutting")
                self.assertEqual(resolved["resolution"], "alias")

        self._run(_check())

    def test_volumetric_letter_assembly_alias_resolves_eligible_pool(self):
        self._run(seed_operational_workforce_registry())

        async def _check():
            async with self.db.session_maker() as session:
                svc = OperationalRegistryService(session)
                resolved = await svc.resolve_operation_mapping("volumetric_letter_assembly")
                assert resolved is not None
                self.assertEqual(resolved["operation_code"], "assembly")
                self.assertEqual(resolved["resolution"], "alias")

                pool = await svc.get_eligible_employees_for_operation("volumetric_letter_assembly")
                names = {e["name"] for e in pool["items"]}
                self.assertGreater(pool["total"], 0)
                self.assertIn("Putaru Sandu", names)
                self.assertIn("Vali Colantator", names)
                self.assertIn("Costi Modelator", names)
                self.assertIn("Andrei Goghi", names)

        self._run(_check())

    def test_unknown_operation_code_returns_soft_missing_pool(self):
        self._run(seed_operational_workforce_registry())

        async def _check():
            async with self.db.session_maker() as session:
                svc = OperationalRegistryService(session)
                resolved = await svc.resolve_operation_mapping("unknown_op_xyz")
                self.assertIsNone(resolved)

                pool = await svc.get_eligible_employees_for_operation("unknown_op_xyz")
                self.assertEqual(pool["total"], 0)
                self.assertEqual(pool["items"], [])
                self.assertEqual(pool.get("resolution"), "not_found")
                self.assertIsNone(pool.get("resolved_operation_code"))

        self._run(_check())

    def test_inactive_employee_excluded_from_eligible_pool(self):
        async def _check():
            async with self.db.session_maker() as session:
                svc = OperationalRegistryService(session)
                active = Employees(name="Active Print", status="active", employee_type="productive")
                was_active = Employees(name="Was Active Print", status="active", employee_type="productive")
                session.add_all([active, was_active])
                await session.flush()

                for emp in (active, was_active):
                    await svc.set_employee_authorizations(
                        emp.id,
                        skill_codes=["SK_PRINT_OPERATOR"],
                        workcenter_codes=["WC_PRINT"],
                        resource_codes=["MCH-EPSON-60800"],
                    )

                await svc.upsert_operation_mapping(
                    {
                        "operation_code": "print",
                        "required_skill_codes": ["SK_PRINT_OPERATOR"],
                        "allowed_workcenter_codes": ["WC_PRINT"],
                        "allowed_resource_codes": ["MCH-EPSON-60800"],
                        "authorization_mode": "hybrid",
                        "authorized_employee_ids": [active.id, was_active.id],
                    }
                )

                pool = await svc.get_eligible_employees_for_operation("print")
                names = {e["name"] for e in pool["items"]}
                self.assertIn("Active Print", names)
                self.assertIn("Was Active Print", names)

                was_active.status = "inactive"
                await session.commit()

                pool_after = await svc.get_eligible_employees_for_operation("print")
                names_after = {e["name"] for e in pool_after["items"]}
                self.assertIn("Active Print", names_after)
                self.assertNotIn("Was Active Print", names_after)

                auth_rows = (
                    await session.execute(
                        select(OperationEmployeeAuthorization).where(
                            OperationEmployeeAuthorization.operation_code == "print",
                            OperationEmployeeAuthorization.employee_id == was_active.id,
                        )
                    )
                ).scalars().all()
                self.assertEqual(len(auth_rows), 1)

        self._run(_check())

    def test_hybrid_skill_pool_excludes_inactive_without_explicit_rows(self):
        async def _check():
            async with self.db.session_maker() as session:
                svc = OperationalRegistryService(session)
                active = Employees(name="Skill Active", status="active", employee_type="productive")
                inactive = Employees(name="Skill Inactive", status="inactive", employee_type="productive")
                session.add_all([active, inactive])
                await session.flush()

                for emp in (active, inactive):
                    await svc.set_employee_authorizations(
                        emp.id,
                        skill_codes=["SK_ASSEMBLY"],
                        workcenter_codes=["WC_ASSEMBLY"],
                        resource_codes=["WA-ASSEMBLY-01"],
                    )

                await svc.upsert_operation_mapping(
                    {
                        "operation_code": "assembly",
                        "required_skill_codes": ["SK_ASSEMBLY"],
                        "allowed_workcenter_codes": ["WC_ASSEMBLY"],
                        "allowed_resource_codes": ["WA-ASSEMBLY-01"],
                        "authorization_mode": "hybrid",
                    }
                )

                pool = await svc.get_eligible_employees_for_operation("assembly")
                names = {e["name"] for e in pool["items"]}
                self.assertIn("Skill Active", names)
                self.assertNotIn("Skill Inactive", names)

        self._run(_check())

    def test_product_template_operations_do_not_define_employee_ids(self):
        requirement_columns = {c.name for c in OperationResourceRequirement.__table__.columns}
        self.assertNotIn("employee_id", requirement_columns)
        self.assertNotIn("authorized_employee_ids", requirement_columns)

        for comp in _volumetric_letters_components():
            for op in comp.get("operations", []):
                for key in op.keys():
                    self.assertNotIn(
                        "employee",
                        key.lower(),
                        msg=f"unexpected employee key on template op {op.get('code')}",
                    )

    def test_inactive_employee_not_eligible_via_direct_check(self):
        async def _check():
            async with self.db.session_maker() as session:
                svc = OperationalRegistryService(session)
                emp = Employees(name="Inactive Weld", status="inactive", employee_type="productive")
                session.add(emp)
                await session.flush()
                await svc.set_employee_authorizations(
                    emp.id,
                    skill_codes=["SK_LOCKSMITH"],
                    workcenter_codes=["WC_METAL_FAB"],
                    resource_codes=["MCH-WELD-STEEL"],
                )
                await svc.upsert_operation_mapping(
                    {
                        "operation_code": "welding",
                        "required_skill_codes": ["SK_LOCKSMITH"],
                        "authorization_mode": "skill",
                    }
                )
                result = await svc.check_employee_operation_eligibility(emp.id, "welding")
                self.assertFalse(result["eligible"])
                self.assertEqual(result["reason"], "employee_inactive")
                self.assertEqual(result["authorization_status"], "not_authorized")

        self._run(_check())

    def test_unauthorized_employee_soft_eligibility_check(self):
        async def _check():
            async with self.db.session_maker() as session:
                svc = OperationalRegistryService(session)
                emp = Employees(name="Neautorizat", status="active", employee_type="productive")
                session.add(emp)
                await session.flush()
                await svc.upsert_operation_mapping(
                    {
                        "operation_code": "welding",
                        "required_skill_codes": ["SK_LOCKSMITH"],
                        "authorization_mode": "skill",
                    }
                )
                result = await svc.check_employee_operation_eligibility(emp.id, "welding")
                self.assertFalse(result["eligible"])
                self.assertEqual(result["authorization_status"], "not_authorized")

        self._run(_check())


if __name__ == "__main__":
    unittest.main()
