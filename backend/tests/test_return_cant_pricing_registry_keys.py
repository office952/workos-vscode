from __future__ import annotations

import asyncio
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import select  # noqa: E402

from models.inventory_materials import Inventory_materials  # noqa: E402
from models.product_templates import Product_templates  # noqa: E402
from seeds.seed_volumetric_owner_confirmed_prices import (  # noqa: E402
    seed_volumetric_owner_confirmed_prices,
)
from seeds.seed_volumetric_workcenter_rates import (  # noqa: E402
    seed_volumetric_workcenter_rates,
)
from services.pricing_registry_service import PricingRegistryService  # noqa: E402
from services.template_usage_mode_policy import TPL_VOLUMETRIC_LETTERS_V2  # noqa: E402
from tests._db_fixture import IsolatedDBFixture  # noqa: E402


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


class TestReturnCantPricingRegistryKeys(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.db_fixture = IsolatedDBFixture(prefix="return_cant_pricing_registry_")
        cls.db_fixture.setup()
        _run(cls._seed())

    @classmethod
    def tearDownClass(cls) -> None:
        cls.db_fixture.teardown()

    @classmethod
    async def _seed(cls) -> None:
        from core.database import db_manager

        material_stubs = [
            ("MAT-ORACAL-641", "Folie autocolantă PVC — Oracal 641 Economy Cal", "mp"),
            ("MAT-ORACAL-651", "Folie autocolantă PVC — Oracal 651", "mp"),
            ("MAT-PROFIL-LATERAL-LITERE-30MM", "Profil aluminiu return/cant 30 mm", "ml"),
            ("MAT-PROFIL-LATERAL-LITERE-60MM", "Profil aluminiu return/cant 60 mm", "ml"),
            ("MAT-PROFIL-LATERAL-LITERE-80MM", "Profil aluminiu return/cant 80 mm", "ml"),
            ("MAT-PROFIL-LATERAL-LITERE-100MM", "Profil aluminiu return/cant 100 mm", "ml"),
            ("MAT-VOPSEA-RAL", "Vopsea RAL spray — tub", "buc"),
            ("MAT-VOPSEA-RAL-CANT-30MM", "Vopsire RAL cant 30 mm - material", "ml"),
            ("MAT-VOPSEA-RAL-CANT-60MM", "Vopsire RAL cant 60 mm - material", "ml"),
            ("MAT-VOPSEA-RAL-CANT-80MM", "Vopsire RAL cant 80 mm - material", "ml"),
            ("MAT-VOPSEA-RAL-CANT-100MM", "Vopsire RAL cant 100 mm - material", "ml"),
        ]

        async with db_manager.async_session_maker() as session:
            template = (
                await session.execute(
                    select(Product_templates).where(
                        Product_templates.template_code == TPL_VOLUMETRIC_LETTERS_V2
                    )
                )
            ).scalar_one_or_none()
            if template is None:
                session.add(
                    Product_templates(
                        template_code=TPL_VOLUMETRIC_LETTERS_V2,
                        family_name="Volumetric Letters V2",
                        description="Test template for return_cant pricing registry keys",
                        components_json="[]",
                        operations_json="[]",
                        required_materials_json="[]",
                        active=True,
                    )
                )

            for code, name, unit in material_stubs:
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
                        category="test_return_cant_pricing",
                        status="missing_price",
                    )
                )

            await session.commit()

        await seed_volumetric_owner_confirmed_prices()
        await seed_volumetric_workcenter_rates()

    def test_registry_contains_new_return_cant_keys_without_overwriting_legacy(self) -> None:
        async def _go():
            async with self.db_fixture.session_maker() as session:
                registry = await PricingRegistryService(session).build_registry(
                    template_filter=TPL_VOLUMETRIC_LETTERS_V2
                )
                return registry

        registry = _run(_go())
        items = registry.get("items") or []
        by_code = {item["pricing_code"]: item for item in items}

        self.assertEqual(len(items), len(by_code))

        self.assertEqual(by_code["RETURN_CANT_VINYL_APPLICATION_LABOR"]["unit"], "EUR/ml")
        self.assertEqual(by_code["RETURN_CANT_VINYL_APPLICATION_LABOR"]["base_cost"], 1.0)
        self.assertEqual(
            by_code["RETURN_CANT_VINYL_APPLICATION_LABOR"]["rate_basis"],
            "per_linear_meter",
        )

        self.assertEqual(by_code["RETURN_CANT_RAL_PAINT_LABOR"]["unit"], "EUR/ml")
        self.assertEqual(by_code["RETURN_CANT_RAL_PAINT_LABOR"]["base_cost"], 1.0)
        self.assertEqual(
            by_code["RETURN_CANT_RAL_PAINT_LABOR"]["rate_basis"],
            "per_linear_meter",
        )

        self.assertEqual(by_code["MAT-VOPSEA-RAL-CANT-30MM"]["unit"], "ml")
        self.assertEqual(by_code["MAT-VOPSEA-RAL-CANT-30MM"]["base_cost"], 2.0)
        self.assertEqual(by_code["MAT-VOPSEA-RAL-CANT-60MM"]["base_cost"], 2.5)
        self.assertEqual(by_code["MAT-VOPSEA-RAL-CANT-80MM"]["base_cost"], 3.0)
        self.assertEqual(by_code["MAT-VOPSEA-RAL-CANT-100MM"]["base_cost"], 4.0)

        self.assertEqual(by_code["MAT-ORACAL-641"]["unit"], "mp")
        self.assertEqual(by_code["MAT-ORACAL-651"]["unit"], "mp")
        self.assertEqual(by_code["FACE_VINYL_APPLICATION_LABOR"]["unit"], "EUR/mp")
        self.assertEqual(by_code["FACE_VINYL_APPLICATION_LABOR"]["base_cost"], 5.0)
        self.assertEqual(by_code["PAINTING"]["base_cost"], 4.0)
        self.assertEqual(by_code["MAT-VOPSEA-RAL"]["base_cost"], 10.0)



if __name__ == "__main__":
    unittest.main()