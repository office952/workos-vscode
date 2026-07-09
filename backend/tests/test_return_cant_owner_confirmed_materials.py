from __future__ import annotations

import asyncio
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import select  # noqa: E402

from models.inventory_materials import Inventory_materials  # noqa: E402
from seeds.seed_volumetric_owner_confirmed_prices import (  # noqa: E402
    seed_volumetric_owner_confirmed_prices,
)
from services.inventory_materials_admin_service import (  # noqa: E402
    get_inventory_material_by_code,
)
from tests._db_fixture import IsolatedDBFixture  # noqa: E402


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


class TestReturnCantOwnerConfirmedMaterials(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.db_fixture = IsolatedDBFixture(prefix="return_cant_owner_materials_")
        cls.db_fixture.setup()
        _run(cls._seed())

    @classmethod
    def tearDownClass(cls) -> None:
        cls.db_fixture.teardown()

    @classmethod
    async def _seed(cls) -> None:
        from core.database import db_manager

        stubs = [
            ("MAT-VOPSEA-RAL", "Vopsea RAL spray — tub", "buc"),
            ("MAT-ORACAL-641", "Folie autocolantă PVC — Oracal 641 Economy Cal", "mp"),
            ("MAT-ORACAL-651", "Folie autocolantă PVC — Oracal 651", "mp"),
            ("MAT-VOPSEA-RAL-CANT-30MM", "Vopsire RAL cant 30 mm - material", "ml"),
            ("MAT-VOPSEA-RAL-CANT-60MM", "Vopsire RAL cant 60 mm - material", "ml"),
            ("MAT-VOPSEA-RAL-CANT-80MM", "Vopsire RAL cant 80 mm - material", "ml"),
            ("MAT-VOPSEA-RAL-CANT-100MM", "Vopsire RAL cant 100 mm - material", "ml"),
        ]
        async with db_manager.async_session_maker() as session:
            for code, name, unit in stubs:
                row = (
                    await session.execute(
                        select(Inventory_materials).where(Inventory_materials.code == code)
                    )
                ).scalar_one_or_none()
                if row is not None:
                    continue
                session.add(
                    Inventory_materials(
                        code=code,
                        name=name,
                        unit=unit,
                        category="test_return_cant_materials",
                        status="missing_price",
                    )
                )
            await session.commit()

        await seed_volumetric_owner_confirmed_prices()

    def test_return_cant_material_rows_are_owner_confirmed(self) -> None:
        async def _go():
            from core.database import db_manager

            async with db_manager.async_session_maker() as session:
                codes = [
                    "MAT-VOPSEA-RAL-CANT-30MM",
                    "MAT-VOPSEA-RAL-CANT-60MM",
                    "MAT-VOPSEA-RAL-CANT-80MM",
                    "MAT-VOPSEA-RAL-CANT-100MM",
                    "MAT-VOPSEA-RAL",
                    "MAT-ORACAL-641",
                    "MAT-ORACAL-651",
                ]
                return {
                    code: await get_inventory_material_by_code(session, code)
                    for code in codes
                }

        rows = _run(_go())

        self.assertEqual(rows["MAT-VOPSEA-RAL-CANT-30MM"]["unit"], "ml")
        self.assertEqual(rows["MAT-VOPSEA-RAL-CANT-30MM"]["unit_cost"], 2.0)
        self.assertEqual(rows["MAT-VOPSEA-RAL-CANT-60MM"]["unit_cost"], 2.5)
        self.assertEqual(rows["MAT-VOPSEA-RAL-CANT-80MM"]["unit_cost"], 3.0)
        self.assertEqual(rows["MAT-VOPSEA-RAL-CANT-100MM"]["unit_cost"], 4.0)

        for code in (
            "MAT-VOPSEA-RAL-CANT-30MM",
            "MAT-VOPSEA-RAL-CANT-60MM",
            "MAT-VOPSEA-RAL-CANT-80MM",
            "MAT-VOPSEA-RAL-CANT-100MM",
        ):
            self.assertEqual(rows[code]["status"], "active")
            self.assertEqual(rows[code]["currency"], "EUR")
            self.assertEqual(rows[code]["source_review_status"], "accepted_override")

        self.assertEqual(rows["MAT-VOPSEA-RAL"]["unit"], "buc")
        self.assertEqual(rows["MAT-VOPSEA-RAL"]["unit_cost"], 10.0)
        self.assertEqual(rows["MAT-ORACAL-641"]["unit"], "mp")
        self.assertEqual(rows["MAT-ORACAL-641"]["unit_cost"], 6.5)
        self.assertEqual(rows["MAT-ORACAL-651"]["unit"], "mp")
        self.assertEqual(rows["MAT-ORACAL-651"]["unit_cost"], 9.0)


if __name__ == "__main__":
    unittest.main()