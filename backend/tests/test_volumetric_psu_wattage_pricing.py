"""LED PSU wattage variant pricing — registry + quote-time alias."""

from __future__ import annotations

import asyncio
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from seeds.seed_build4_templates import _volumetric_letters_components  # noqa: E402
from seeds.seed_volumetric_owner_confirmed_prices import (  # noqa: E402
    OWNER_CONFIRMED_PSU_WATTAGE_PRICES,
    seed_volumetric_owner_confirmed_prices,
)
from services.cost_engine_service import (  # noqa: E402
    ERR_MATERIAL_RATE_MISSING,
    ComponentCostContext,
    build_execution_layers_from_components,
)
from services.volumetric_material_rate_resolver import (  # noqa: E402
    RESOLUTION_MISSING_PSU_WATTS_SELECTION,
    RESOLUTION_RESOLVED,
    RESOLUTION_SKIPPED_NON_VOLUMETRIC_TEMPLATE,
    RESOLUTION_UNSUPPORTED_PSU_WATTS,
    RESOLUTION_VARIANT_RATE_MISSING,
    TEMPLATE_PSU_CODE,
    VOLUMETRIC_TEMPLATE_CODE,
    resolve_led_psu_material_rate,
    resolve_volumetric_material_rates_with_trace,
)
from services.product_readiness_service import ProductReadinessService  # noqa: E402
from services.volumetric_material_rate_resolver import (  # noqa: E402
    READINESS_WARNING_PSU_VARIANT_PRICING_READY,
)
from tests._db_fixture import IsolatedDBFixture  # noqa: E402

from models.inventory_materials import Inventory_materials  # noqa: E402
from models.product_templates import Product_templates  # noqa: E402
from sqlalchemy import select  # noqa: E402


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


FULL_QUOTE_INPUT = {
    "letter_face_area_m2": 2.88,
    "letter_perimeter_m": 18.0,
    "letter_count": 9,
    "led_module_count": 27,
    "return_depth_mm": 60,
    "selected_psu_watts": 100,
}


class TestVolumetricPsuWattageResolver(unittest.TestCase):
    def test_selected_psu_watts_100_resolves_to_100w_variant(self) -> None:
        base = {"MAT-LED-PSU-12V-100W": 16.0}
        trace = resolve_led_psu_material_rate(
            base,
            {"selected_psu_watts": 100},
            template_code=VOLUMETRIC_TEMPLATE_CODE,
        )
        self.assertEqual(trace.resolution_status, RESOLUTION_RESOLVED)
        self.assertEqual(trace.source_code, "MAT-LED-PSU-12V-100W")
        self.assertEqual(trace.selected_psu_watts, 100)
        self.assertEqual(trace.unit_cost, 16.0)

    def test_psu_watts_fallback_key(self) -> None:
        base = {"MAT-LED-PSU-12V-160W": 20.0}
        trace = resolve_led_psu_material_rate(
            base,
            {"psu_watts": 160, "letter_count": 1},
            template_code=VOLUMETRIC_TEMPLATE_CODE,
        )
        self.assertEqual(trace.resolution_status, RESOLUTION_RESOLVED)
        self.assertEqual(trace.source_code, "MAT-LED-PSU-12V-160W")

    def test_missing_psu_watts_selection_fails_closed(self) -> None:
        base = {"MAT-LED-PSU-12V-100W": 16.0}
        rates, trace = resolve_volumetric_material_rates_with_trace(
            base,
            {"letter_perimeter_m": 1.0, "return_depth_mm": 60},
            template_code=VOLUMETRIC_TEMPLATE_CODE,
        )
        self.assertNotIn(TEMPLATE_PSU_CODE, rates)
        self.assertEqual(
            trace.led_psu_12v.resolution_status,
            RESOLUTION_MISSING_PSU_WATTS_SELECTION,
        )

    def test_unsupported_psu_watts_150_fails_closed(self) -> None:
        trace = resolve_led_psu_material_rate(
            {"MAT-LED-PSU-12V-100W": 16.0},
            {"selected_psu_watts": 150},
            template_code=VOLUMETRIC_TEMPLATE_CODE,
        )
        self.assertEqual(trace.resolution_status, RESOLUTION_UNSUPPORTED_PSU_WATTS)

    def test_non_volumetric_template_skips_psu_alias(self) -> None:
        trace = resolve_led_psu_material_rate(
            {"MAT-LED-PSU-12V-100W": 16.0},
            {"selected_psu_watts": 100},
            template_code="TPL-ACP-LIGHT-ROUTED",
        )
        self.assertEqual(trace.resolution_status, RESOLUTION_SKIPPED_NON_VOLUMETRIC_TEMPLATE)

    def test_only_psu_code_aliased(self) -> None:
        base = {
            "MAT-LED-PSU-12V-100W": 16.0,
            "MAT-ACP-FATA-LITERE": 16.0,
        }
        rates, trace = resolve_volumetric_material_rates_with_trace(
            base,
            {"selected_psu_watts": 100},
            template_code=VOLUMETRIC_TEMPLATE_CODE,
        )
        self.assertEqual(rates["MAT-ACP-FATA-LITERE"], 16.0)
        self.assertEqual(rates[TEMPLATE_PSU_CODE], 16.0)
        self.assertEqual(trace.led_psu_12v.resolution_status, RESOLUTION_RESOLVED)

    def test_variant_missing_rate_fails_closed(self) -> None:
        trace = resolve_led_psu_material_rate(
            {},
            {"selected_psu_watts": 100},
            template_code=VOLUMETRIC_TEMPLATE_CODE,
        )
        self.assertEqual(trace.resolution_status, RESOLUTION_VARIANT_RATE_MISSING)


class TestVolumetricPsuRegistryAndEngine(unittest.TestCase):
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
            for spec in OWNER_CONFIRMED_PSU_WATTAGE_PRICES:
                code = spec["code"]
                if (
                    await session.execute(
                        select(Inventory_materials).where(Inventory_materials.code == code)
                    )
                ).scalar_one_or_none():
                    continue
                session.add(
                    Inventory_materials(
                        code=code,
                        name=code,
                        unit="buc",
                        category="iluminat_led",
                        unit_cost=None,
                        status="missing_price",
                    )
                )
            if (
                await session.execute(
                    select(Inventory_materials).where(
                        Inventory_materials.code == TEMPLATE_PSU_CODE
                    )
                )
            ).scalar_one_or_none() is None:
                session.add(
                    Inventory_materials(
                        code=TEMPLATE_PSU_CODE,
                        name="PSU 12V",
                        unit="buc",
                        category="iluminat_led",
                        unit_cost=None,
                        status="missing_price",
                    )
                )
            await session.commit()

    def test_psu_variants_active_after_seed(self) -> None:
        from core.database import db_manager
        from services.inventory_materials_admin_service import get_inventory_material_by_code

        async def _go():
            async with db_manager.async_session_maker() as session:
                rows = {}
                for spec in OWNER_CONFIRMED_PSU_WATTAGE_PRICES:
                    rows[spec["code"]] = await get_inventory_material_by_code(
                        session, spec["code"]
                    )
                return rows

        rows = _run(_go())
        for spec in OWNER_CONFIRMED_PSU_WATTAGE_PRICES:
            row = rows[spec["code"]]
            self.assertEqual(row["status"], "active")
            self.assertEqual(row["unit_cost"], spec["unit_cost"])
            self.assertEqual(str(row["currency"]).upper(), "EUR")
            self.assertEqual(row["source_review_status"], "accepted_override")
            notes = str(row.get("source_notes") or "")
            self.assertIn("5.2 RON/EUR", notes)
            self.assertIn("commercially rounded", notes)

    def test_engine_unblocks_psu_with_selected_psu_watts(self) -> None:
        rates = {spec["code"]: spec["unit_cost"] for spec in OWNER_CONFIRMED_PSU_WATTAGE_PRICES}
        rates.update(
            {
                "MAT-PROFIL-LATERAL-LITERE-60MM": 3.0,
                "MAT-ACP-FATA-LITERE": 16.0,
                "MAT-SPATE-PVC-LITERE": 16.0,
                "MAT-LED-MODULE": 0.5,
            }
        )
        resolved, trace = resolve_volumetric_material_rates_with_trace(
            rates,
            FULL_QUOTE_INPUT,
            template_code=VOLUMETRIC_TEMPLATE_CODE,
        )
        self.assertEqual(trace.led_psu_12v.resolution_status, RESOLUTION_RESOLVED)
        components = _volumetric_letters_components()
        out = build_execution_layers_from_components(
            {
                "template_code": VOLUMETRIC_TEMPLATE_CODE,
                "components_json": json.dumps(components),
                "operations_json": "[]",
                "required_materials_json": "[]",
            },
            ComponentCostContext(
                material_rates=resolved,
                workcenter_rates={
                    "CNC_ROUTER": 90.0,
                    "LASER_CUTTING": 90.0,
                    "ASSEMBLY": 80.0,
                    "LED_ASSEMBLY": 60.0,
                    "ELECTRICAL_WIRING": 60.0,
                    "PAINTING": 70.0,
                    "QC_INSPECTION": 50.0,
                    "PACKAGING": 40.0,
                    "PREPRESS": 50.0,
                },
                quantity=1,
                quote_input=dict(FULL_QUOTE_INPUT),
            ),
        )
        psu_missing = [
            e
            for e in out.get("errors") or []
            if e.get("kind") == ERR_MATERIAL_RATE_MISSING
            and TEMPLATE_PSU_CODE in str(e.get("detail") or "")
        ]
        self.assertEqual(psu_missing, [], msg=out.get("errors"))


class TestVolumetricPsuReadinessPolicy(unittest.TestCase):
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
        from seeds.seed_build4_templates import _volumetric_letters_components

        async with db_manager.async_session_maker() as session:
            for spec in OWNER_CONFIRMED_PSU_WATTAGE_PRICES:
                code = spec["code"]
                if (
                    await session.execute(
                        select(Inventory_materials).where(Inventory_materials.code == code)
                    )
                ).scalar_one_or_none():
                    continue
                session.add(
                    Inventory_materials(
                        code=code,
                        name=code,
                        unit="buc",
                        category="iluminat_led",
                        unit_cost=None,
                        status="missing_price",
                    )
                )
            if (
                await session.execute(
                    select(Inventory_materials).where(
                        Inventory_materials.code == TEMPLATE_PSU_CODE
                    )
                )
            ).scalar_one_or_none() is None:
                session.add(
                    Inventory_materials(
                        code=TEMPLATE_PSU_CODE,
                        name="PSU",
                        unit="buc",
                        category="iluminat_led",
                        unit_cost=None,
                        status="missing_price",
                    )
                )
            tpl = (
                await session.execute(
                    select(Product_templates).where(
                        Product_templates.template_code == VOLUMETRIC_TEMPLATE_CODE
                    )
                )
            ).scalar_one_or_none()
            if tpl is None:
                session.add(
                    Product_templates(
                        template_code=VOLUMETRIC_TEMPLATE_CODE,
                        family_id="signage",
                        family_name="Signage",
                        components_json=json.dumps(_volumetric_letters_components()),
                        operations_json=json.dumps([]),
                        required_materials_json=json.dumps([]),
                        active=True,
                    )
                )
            await session.commit()

    def test_generic_psu_not_marked_price_complete_when_variants_ready(self) -> None:
        from core.database import db_manager

        async def _go():
            async with db_manager.async_session_maker() as session:
                tpl = (
                    await session.execute(
                        select(Product_templates).where(
                            Product_templates.template_code == VOLUMETRIC_TEMPLATE_CODE
                        )
                    )
                ).scalar_one_or_none()
                return await ProductReadinessService(session).evaluate(tpl.id)

        result = _run(_go()).to_dict()
        blockers = result["technical_readiness"]["blockers"]
        warnings = result["technical_readiness"]["warnings"]
        self.assertNotIn(f"active_material_price_incomplete:{TEMPLATE_PSU_CODE}", blockers)
        self.assertIn(READINESS_WARNING_PSU_VARIANT_PRICING_READY, warnings)
        self.assertTrue(
            any(
                str(w).startswith(f"volumetric_psu_wattage_required_at_quote:{TEMPLATE_PSU_CODE}")
                for w in result["costengine_readiness"]["warnings"]
            )
        )
        self.assertFalse(result["ready_for_quote"])


if __name__ == "__main__":
    unittest.main()
