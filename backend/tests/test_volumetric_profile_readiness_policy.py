"""Readiness policy for depth-tier volumetric profile (no false green on generic code)."""

from __future__ import annotations

import asyncio
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from seeds.seed_build4_templates import _volumetric_letters_components  # noqa: E402
from seeds.seed_volumetric_owner_confirmed_prices import (  # noqa: E402
    OWNER_CONFIRMED_PROFILE_DEPTH_PRICES,
    OWNER_CONFIRMED_PSU_WATTAGE_PRICES,
    OWNER_CONFIRMED_VOLUMETRIC_PRICES,
    TEMPLATE_PROFILE_CODE,
    seed_volumetric_owner_confirmed_prices,
)
from services.product_readiness_service import ProductReadinessService  # noqa: E402
from services.volumetric_material_rate_resolver import (  # noqa: E402
    READINESS_WARNING_VARIANT_PRICING_READY,
)
from tests._db_fixture import IsolatedDBFixture  # noqa: E402

from models.inventory_materials import Inventory_materials  # noqa: E402
from models.product_templates import Product_templates  # noqa: E402
from sqlalchemy import select  # noqa: E402


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


class TestVolumetricProfileReadinessPolicy(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.db_fixture = IsolatedDBFixture()
        cls.db_fixture.setup()
        _run(cls._seed())
        _run(seed_volumetric_owner_confirmed_prices())

    @classmethod
    def tearDownClass(cls) -> None:
        cls.db_fixture.teardown()

    @classmethod
    async def _seed(cls) -> None:
        from core.database import db_manager

        async with db_manager.async_session_maker() as session:
            for spec in (
                OWNER_CONFIRMED_VOLUMETRIC_PRICES
                + OWNER_CONFIRMED_PROFILE_DEPTH_PRICES
                + OWNER_CONFIRMED_PSU_WATTAGE_PRICES
            ):
                code = spec["code"]
                existing = (
                    await session.execute(
                        select(Inventory_materials).where(Inventory_materials.code == code)
                    )
                ).scalar_one_or_none()
                if existing:
                    continue
                session.add(
                    Inventory_materials(
                        code=code,
                        name=code,
                        unit="ml" if "PROFIL" in code else "mp",
                        category="test",
                        unit_cost=None,
                        status="missing_price",
                    )
                )
            if (
                await session.execute(
                    select(Inventory_materials).where(
                        Inventory_materials.code == TEMPLATE_PROFILE_CODE
                    )
                )
            ).scalar_one_or_none() is None:
                session.add(
                    Inventory_materials(
                        code=TEMPLATE_PROFILE_CODE,
                        name="Profil lateral",
                        unit="ml",
                        category="profil_metal",
                        unit_cost=None,
                        status="missing_price",
                    )
                )

            existing_tpl = (
                await session.execute(
                    select(Product_templates).where(
                        Product_templates.template_code == "TPL-VOLUMETRIC-LETTERS"
                    )
                )
            ).scalar_one_or_none()
            if existing_tpl is None:
                components = _volumetric_letters_components()
                session.add(
                    Product_templates(
                        template_code="TPL-VOLUMETRIC-LETTERS",
                        family_id="signage",
                        family_name="Signage",
                        components_json=json.dumps(components),
                        operations_json=json.dumps([]),
                        required_materials_json=json.dumps([]),
                        active=True,
                    )
                )
            await session.commit()

    def test_variants_ready_generic_not_marked_active_price_complete(self) -> None:
        from core.database import db_manager

        async def _go():
            async with db_manager.async_session_maker() as session:
                tpl = (
                    await session.execute(
                        select(Product_templates).where(
                            Product_templates.template_code == "TPL-VOLUMETRIC-LETTERS"
                        )
                    )
                ).scalar_one_or_none()
                assert tpl is not None
                result = await ProductReadinessService(session).evaluate(tpl.id)
                return result.to_dict()

        body = _run(_go())
        blockers = body["technical_readiness"]["blockers"]
        warnings = body["technical_readiness"]["warnings"]

        self.assertNotIn(
            f"active_material_price_incomplete:{TEMPLATE_PROFILE_CODE}",
            blockers,
            "generic profile must not be treated as singly priced when variants are ready",
        )
        self.assertNotIn(
            f"active_template_material_not_active:{TEMPLATE_PROFILE_CODE}:missing_price",
            blockers,
        )
        self.assertIn(READINESS_WARNING_VARIANT_PRICING_READY, warnings)
        self.assertTrue(
            any(
                str(w).startswith("volumetric_profile_return_depth_required_at_quote:")
                for w in body["costengine_readiness"]["warnings"]
            )
        )

    def test_ready_for_quote_still_false_without_dossier_approval(self) -> None:
        """Variant policy is a warning — not a fake ready_for_quote."""
        from core.database import db_manager

        async def _go():
            async with db_manager.async_session_maker() as session:
                tpl = (
                    await session.execute(
                        select(Product_templates).where(
                            Product_templates.template_code == "TPL-VOLUMETRIC-LETTERS"
                        )
                    )
                ).scalar_one_or_none()
                result = await ProductReadinessService(session).evaluate(tpl.id)
                return result.to_dict()

        body = _run(_go())
        self.assertFalse(body["ready_for_quote"])


if __name__ == "__main__":
    unittest.main()
