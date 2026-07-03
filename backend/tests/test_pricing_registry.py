"""Pricing Registry aggregation — template-driven quote pricing."""

from __future__ import annotations

import asyncio
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from seeds.seed_acm_bond_materials import seed_acm_bond_materials  # noqa: E402
from seeds.seed_acm_owner_confirmed_prices import seed_acm_owner_confirmed_prices  # noqa: E402
from scripts.seed_acm_template_pack import seed_acm_template_pack  # noqa: E402
from seeds.seed_active_template_scope import seed_active_template_scope  # noqa: E402
from seeds.seed_build4_templates import seed_build4_templates  # noqa: E402
from seeds.seed_volumetric_owner_confirmed_prices import (  # noqa: E402
    seed_volumetric_owner_confirmed_prices,
)
from seeds.seed_volumetric_workcenter_rates import (  # noqa: E402
    seed_volumetric_operations_and_rates,
)
from services.inventory_materials_admin_service import (  # noqa: E402
    load_material_cost_dict,
    patch_inventory_material_by_code,
)
from services.workcenter_rates_service import update_workcenter_rate  # noqa: E402
from services.pricing_registry_service import (  # noqa: E402
    PricingRegistryService,
    infer_registry_category,
    map_confidence,
)
from models.inventory_materials import Inventory_materials  # noqa: E402
from sqlalchemy import select  # noqa: E402
from tests._db_fixture import IsolatedDBFixture  # noqa: E402


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


class TestPricingRegistryHelpers(unittest.TestCase):
    def test_infer_placi_for_acm(self) -> None:
        cat = infer_registry_category(
            pricing_code="MAT-ACM-BOND-3MM",
            pricing_kind="material",
        )
        self.assertEqual(cat, "Plăci")

    def test_infer_profile_category(self) -> None:
        cat = infer_registry_category(
            pricing_code="MAT-PROFIL-LATERAL-LITERE-60MM",
            pricing_kind="material",
        )
        self.assertEqual(cat, "Profile / canturi")

    def test_owner_confirmed_confidence(self) -> None:
        self.assertEqual(
            map_confidence(
                source_review_status="accepted_override",
                status="active",
                has_price=True,
            ),
            "owner_confirmed",
        )


class TestPricingRegistryService(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.db_fixture = IsolatedDBFixture(prefix="pricing_registry_testdb_")
        cls.db_fixture.setup()
        _run(cls._seed())

    @classmethod
    def tearDownClass(cls) -> None:
        cls.db_fixture.teardown()

    @classmethod
    async def _seed(cls) -> None:
        from core.database import db_manager

        await seed_build4_templates()
        await seed_acm_bond_materials()
        await seed_acm_owner_confirmed_prices()
        await seed_acm_template_pack()
        await cls._seed_material_stubs()
        await seed_volumetric_owner_confirmed_prices()
        await seed_volumetric_operations_and_rates()
        await seed_active_template_scope()

    @classmethod
    async def _seed_material_stubs(cls) -> None:
        """Minimal rows so volumetric price seed can PATCH owner-confirmed costs."""
        from core.database import db_manager

        codes = [
            ("MAT-ACP-FATA-LITERE", "mp"),
            ("MAT-SPATE-PVC-LITERE", "mp"),
            ("MAT-LED-MODULE", "buc"),
            ("MAT-SABLON-MONTAJ", "mp"),
            ("MAT-VOPSEA-RAL", "buc"),
            ("MAT-CONSUMABILE-MONTAJ", "set"),
            ("MAT-PROFIL-LATERAL-LITERE", "ml"),
            ("MAT-PROFIL-LATERAL-LITERE-30MM", "ml"),
            ("MAT-PROFIL-LATERAL-LITERE-60MM", "ml"),
            ("MAT-PROFIL-LATERAL-LITERE-80MM", "ml"),
            ("MAT-PROFIL-LATERAL-LITERE-100MM", "ml"),
            ("MAT-LED-PSU-12V", "buc"),
            ("MAT-LED-PSU-12V-60W", "buc"),
            ("MAT-LED-PSU-12V-100W", "buc"),
            ("MAT-LED-PSU-12V-160W", "buc"),
            ("MAT-LED-PSU-12V-200W", "buc"),
        ]
        async with db_manager.async_session_maker() as session:
            for code, unit in codes:
                exists = (
                    await session.execute(
                        select(Inventory_materials).where(
                            Inventory_materials.code == code
                        )
                    )
                ).scalar_one_or_none()
                if exists:
                    continue
                session.add(
                    Inventory_materials(
                        code=code,
                        name=code,
                        unit=unit,
                        category="test",
                        status="missing_price",
                    )
                )
            await session.commit()

    def test_volumetric_template_includes_product_001_materials(self) -> None:
        async def _go():
            async with self.db_fixture.session_maker() as session:
                svc = PricingRegistryService(session)
                reg = await svc.build_registry(template_filter="TPL-VOLUMETRIC-LETTERS")
                codes = {i["pricing_code"] for i in reg["items"]}
                self.assertIn("MAT-LED-MODULE", codes)
                self.assertIn("MAT-SPATE-PVC-LITERE", codes)
                self.assertIn("MAT-PROFIL-LATERAL-LITERE-60MM", codes)
                self.assertIn("RETURN_PROFILE_MACHINE_FORMING", codes)
                return reg

        reg = _run(_go())
        self.assertGreater(reg["summary"]["materials_count"], 5)

    def test_inactive_acm_template_excluded_from_pricing_registry(self) -> None:
        async def _go():
            async with self.db_fixture.session_maker() as session:
                svc = PricingRegistryService(session)
                default_reg = await svc.build_registry()
                filtered_reg = await svc.build_registry(
                    template_filter="TPL-ACM-CASSETTED-PANEL"
                )
                return default_reg, filtered_reg

        default_reg, filtered_reg = _run(_go())
        default_usage = [
            u["template_code"] for u in default_reg.get("template_usage") or []
        ]
        self.assertEqual(default_usage, ["TPL-VOLUMETRIC-LETTERS"])
        self.assertEqual(
            {i["pricing_code"] for i in filtered_reg["items"]},
            set(),
        )

    def test_cost_engine_rate_matches_registry_material(self) -> None:
        async def _go():
            async with self.db_fixture.session_maker() as session:
                ce_rates = await load_material_cost_dict(session)
                svc = PricingRegistryService(session)
                reg = await svc.build_registry(
                    template_filter="TPL-VOLUMETRIC-LETTERS"
                )
                led = next(
                    i for i in reg["items"] if i["pricing_code"] == "MAT-LED-MODULE"
                )
                self.assertEqual(led["cost_engine_rate"], ce_rates.get("MAT-LED-MODULE"))
                self.assertTrue(led["cost_engine_rate_match"])
                spate = next(
                    i
                    for i in reg["items"]
                    if i["pricing_code"] == "MAT-SPATE-PVC-LITERE"
                )
                self.assertEqual(
                    spate["cost_engine_rate"], ce_rates.get("MAT-SPATE-PVC-LITERE")
                )

        _run(_go())

    def test_estimated_not_owner_confirmed(self) -> None:
        async def _go():
            async with self.db_fixture.session_maker() as session:
                svc = PricingRegistryService(session)
                reg = await svc.build_registry(
                    template_filter="TPL-VOLUMETRIC-LETTERS"
                )
                consumabile = next(
                    (
                        i
                        for i in reg["items"]
                        if i["pricing_code"] == "MAT-CONSUMABILE-MONTAJ"
                    ),
                    None,
                )
                if consumabile:
                    self.assertIn(
                        consumabile["confidence"],
                        {"estimated", "needs_review", "missing"},
                    )
                    self.assertNotEqual(consumabile["confidence"], "owner_confirmed")
                vopsea = next(
                    (i for i in reg["items"] if i["pricing_code"] == "MAT-VOPSEA-RAL"),
                    None,
                )
                if vopsea:
                    self.assertEqual(vopsea["confidence"], "owner_confirmed")

        _run(_go())

    def test_registry_reflects_material_price_patch(self) -> None:
        async def _go():
            async with self.db_fixture.session_maker() as session:
                await patch_inventory_material_by_code(
                    session,
                    "MAT-LED-MODULE",
                    unit_cost=9.99,
                    change_reason="pricing registry edit test",
                    changed_by="test",
                    provided_fields={"unit_cost", "change_reason"},
                )
                await session.commit()
                svc = PricingRegistryService(session)
                reg = await svc.build_registry(
                    template_filter="TPL-VOLUMETRIC-LETTERS"
                )
                led = next(
                    i for i in reg["items"] if i["pricing_code"] == "MAT-LED-MODULE"
                )
                self.assertEqual(led["base_cost"], 9.99)
                ce_rates = await load_material_cost_dict(session)
                self.assertEqual(ce_rates.get("MAT-LED-MODULE"), 9.99)

        _run(_go())

    def test_registry_reflects_workcenter_rate_patch(self) -> None:
        async def _go():
            async with self.db_fixture.session_maker() as session:
                await update_workcenter_rate(
                    session,
                    "RETURN_PROFILE_MACHINE_FORMING",
                    rate_per_linear_meter=6.5,
                    rate_basis="per_linear_meter",
                    status="active",
                    notes="[Pricing] registry edit test",
                )
                await session.commit()
                svc = PricingRegistryService(session)
                reg = await svc.build_registry(
                    template_filter="TPL-VOLUMETRIC-LETTERS"
                )
                row = next(
                    i
                    for i in reg["items"]
                    if i["pricing_code"] == "RETURN_PROFILE_MACHINE_FORMING"
                )
                self.assertEqual(row["base_cost"], 6.5)

        _run(_go())
