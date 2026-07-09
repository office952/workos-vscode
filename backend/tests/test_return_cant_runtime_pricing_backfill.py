from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import models  # noqa: F401,E402
from models.inventory_materials import Inventory_materials  # noqa: E402
from models.workcenter_rates import Workcenter_rates  # noqa: E402
from scripts.backfill_return_cant_pricing_keys import (  # noqa: E402
    TARGET_MATERIAL_ROWS,
    TARGET_WORKCENTER_ROWS,
    backfill_return_cant_pricing_keys,
)
from tests._db_fixture import IsolatedDBFixture  # noqa: E402


LEGACY_MATERIAL_ROWS = [
    ("MAT-ORACAL-641", "Folie autocolantă PVC — Oracal 641 Economy Cal", "mp", 6.5, "EUR"),
    ("MAT-ORACAL-651", "Folie autocolantă PVC — Oracal 651", "mp", 9.0, "EUR"),
    ("MAT-PROFIL-LATERAL-LITERE-30MM", "Profil aluminiu return/cant 30 mm", "ml", 2.0, "EUR"),
    ("MAT-PROFIL-LATERAL-LITERE-60MM", "Profil aluminiu return/cant 60 mm", "ml", 3.0, "EUR"),
    ("MAT-PROFIL-LATERAL-LITERE-80MM", "Profil aluminiu return/cant 80 mm", "ml", 4.0, "EUR"),
    ("MAT-PROFIL-LATERAL-LITERE-100MM", "Profil aluminiu return/cant 100 mm", "ml", 5.0, "EUR"),
    ("MAT-VOPSEA-RAL", "Vopsea RAL spray — tub", "buc", 10.0, "EUR"),
]

LEGACY_WORKCENTER_ROWS = [
    ("FACE_VINYL_APPLICATION_LABOR", "Manoperă aplicare folie fețe litere", "per_square_meter", 5.0, "EUR"),
    ("PAINTING", "Vopsire RAL — serviciu perimetru", "per_linear_meter", 4.0, "EUR"),
]


class TestReturnCantRuntimePricingBackfill(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.db_fixture = IsolatedDBFixture(prefix="return_cant_runtime_backfill_")
        cls.db_fixture.setup()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.db_fixture.teardown()

    def setUp(self) -> None:
        self.db_fixture.reset_tables([Inventory_materials, Workcenter_rates])
        self.db_fixture.run(self._seed_legacy_rows())

    async def _seed_legacy_rows(self) -> None:
        async with self.db_fixture.session_maker() as session:
            for code, name, unit, unit_cost, currency in LEGACY_MATERIAL_ROWS:
                session.add(
                    Inventory_materials(
                        code=code,
                        name=name,
                        category="legacy_test",
                        unit=unit,
                        unit_cost=unit_cost,
                        currency=currency,
                        status="active",
                    )
                )
            for code, label, rate_basis, rate_per_linear_meter, currency in LEGACY_WORKCENTER_ROWS:
                session.add(
                    Workcenter_rates(
                        code=code,
                        label=label,
                        rate_per_hour=None,
                        rate_per_linear_meter=rate_per_linear_meter,
                        rate_basis=rate_basis,
                        currency=currency,
                        status="active",
                        is_active=True,
                    )
                )
            await session.commit()

    async def _run_backfill(self):
        async with self.db_fixture.session_maker() as session:
            return await backfill_return_cant_pricing_keys(session)

    async def _material_by_code(self, code: str):
        async with self.db_fixture.session_maker() as session:
            rows = (
                await session.execute(
                    Inventory_materials.__table__.select().where(Inventory_materials.code == code)
                )
            ).all()
            return rows

    async def _workcenter_by_code(self, code: str):
        async with self.db_fixture.session_maker() as session:
            rows = (
                await session.execute(
                    Workcenter_rates.__table__.select().where(Workcenter_rates.code == code)
                )
            ).all()
            return rows

    async def _legacy_snapshot(self):
        async with self.db_fixture.session_maker() as session:
            materials = (
                await session.execute(
                    Inventory_materials.__table__.select().where(
                        Inventory_materials.code.in_([row[0] for row in LEGACY_MATERIAL_ROWS])
                    ).order_by(Inventory_materials.code)
                )
            ).all()
            workcenters = (
                await session.execute(
                    Workcenter_rates.__table__.select().where(
                        Workcenter_rates.code.in_([row[0] for row in LEGACY_WORKCENTER_ROWS])
                    ).order_by(Workcenter_rates.code)
                )
            ).all()
            return materials, workcenters

    def test_inserts_missing_material_and_labor_rows_with_expected_values(self) -> None:
        report = self.db_fixture.run(self._run_backfill())

        self.assertEqual(report["summary"]["inserted"], 6)
        self.assertEqual(report["summary"]["already_ok"], 0)
        self.assertEqual(report["summary"]["conflicts"], 0)

        inserted_codes = {entry["code"] for entry in report["inserted"]}
        self.assertEqual(
            inserted_codes,
            {row["code"] for row in TARGET_MATERIAL_ROWS} | {row["code"] for row in TARGET_WORKCENTER_ROWS},
        )

        for target in TARGET_MATERIAL_ROWS:
            rows = self.db_fixture.run(self._material_by_code(target["code"]))
            self.assertEqual(len(rows), 1)
            row = rows[0]
            self.assertEqual(row.code, target["code"])
            self.assertEqual(row.name, target["name"])
            self.assertEqual(row.unit, target["unit"])
            self.assertAlmostEqual(row.unit_cost, target["unit_cost"])
            self.assertEqual(row.currency, target["currency"])
            self.assertEqual(row.status, "active")

        for target in TARGET_WORKCENTER_ROWS:
            rows = self.db_fixture.run(self._workcenter_by_code(target["code"]))
            self.assertEqual(len(rows), 1)
            row = rows[0]
            self.assertEqual(row.code, target["code"])
            self.assertEqual(row.label, target["label"])
            self.assertEqual(row.rate_basis, target["rate_basis"])
            self.assertAlmostEqual(row.rate_per_linear_meter, target["rate_per_linear_meter"])
            self.assertEqual(row.currency, target["currency"])
            self.assertEqual(row.status, "active")
            self.assertTrue(row.is_active)

    def test_second_run_is_idempotent_and_reports_already_ok(self) -> None:
        first = self.db_fixture.run(self._run_backfill())
        second = self.db_fixture.run(self._run_backfill())

        self.assertEqual(first["summary"]["inserted"], 6)
        self.assertEqual(second["summary"]["inserted"], 0)
        self.assertEqual(second["summary"]["already_ok"], 6)
        self.assertEqual(second["summary"]["conflicts"], 0)

    def test_does_not_overwrite_conflicting_existing_rows(self) -> None:
        async def _seed_conflicts() -> None:
            async with self.db_fixture.session_maker() as session:
                session.add(
                    Inventory_materials(
                        code="MAT-VOPSEA-RAL-CANT-30MM",
                        name="Vopsire RAL cant 30 mm - material",
                        category="conflict_test",
                        unit="ml",
                        unit_cost=9.0,
                        currency="EUR",
                        status="active",
                    )
                )
                session.add(
                    Workcenter_rates(
                        code="RETURN_CANT_VINYL_APPLICATION_LABOR",
                        label="Aplicare folie autocolanta pe cant",
                        rate_per_hour=None,
                        rate_per_linear_meter=9.0,
                        rate_basis="per_linear_meter",
                        currency="EUR",
                        status="active",
                        is_active=True,
                    )
                )
                await session.commit()

        self.db_fixture.run(_seed_conflicts())
        report = self.db_fixture.run(self._run_backfill())

        conflict_codes = {entry["code"] for entry in report["conflicts"]}
        self.assertEqual(
            conflict_codes,
            {"MAT-VOPSEA-RAL-CANT-30MM", "RETURN_CANT_VINYL_APPLICATION_LABOR"},
        )
        self.assertEqual(report["summary"]["conflicts"], 2)

        material_rows = self.db_fixture.run(self._material_by_code("MAT-VOPSEA-RAL-CANT-30MM"))
        self.assertEqual(len(material_rows), 1)
        self.assertAlmostEqual(material_rows[0].unit_cost, 9.0)

        workcenter_rows = self.db_fixture.run(self._workcenter_by_code("RETURN_CANT_VINYL_APPLICATION_LABOR"))
        self.assertEqual(len(workcenter_rows), 1)
        self.assertAlmostEqual(workcenter_rows[0].rate_per_linear_meter, 9.0)

    def test_does_not_touch_legacy_rows(self) -> None:
        before_materials, before_workcenters = self.db_fixture.run(self._legacy_snapshot())
        self.db_fixture.run(self._run_backfill())
        after_materials, after_workcenters = self.db_fixture.run(self._legacy_snapshot())

        self.assertEqual(before_materials, after_materials)
        self.assertEqual(before_workcenters, after_workcenters)


if __name__ == "__main__":
    unittest.main()