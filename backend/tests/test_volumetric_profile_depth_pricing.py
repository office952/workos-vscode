"""Depth-tier profile lateral pricing — registry variants + quote-time alias."""

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
    PROFILE_DEPTH_VARIANT_CODES,
    seed_volumetric_owner_confirmed_prices,
)
from services.cost_engine_service import (  # noqa: E402
    ERR_MATERIAL_RATE_MISSING,
    ComponentCostContext,
    build_execution_layers_from_components,
)
from services.volumetric_material_rate_resolver import (  # noqa: E402
    PROFILE_DEPTH_MM_TO_VARIANT_CODE,
    RESOLUTION_MISSING_RETURN_DEPTH_MM,
    RESOLUTION_RESOLVED,
    RESOLUTION_SKIPPED_NON_VOLUMETRIC_TEMPLATE,
    RESOLUTION_UNSUPPORTED_RETURN_DEPTH_MM,
    RESOLUTION_VARIANT_RATE_MISSING,
    TEMPLATE_PROFILE_CODE,
    VOLUMETRIC_TEMPLATE_CODE,
    resolve_profile_lateral_material_rate,
    resolve_volumetric_material_rates,
    resolve_volumetric_material_rates_with_trace,
)
from tests._db_fixture import IsolatedDBFixture  # noqa: E402

from models.inventory_materials import Inventory_materials  # noqa: E402
from sqlalchemy import select  # noqa: E402


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


FULL_QUOTE_INPUT = {
    "letter_face_area_m2": 2.88,
    "letter_perimeter_m": 18.0,
    "letter_count": 9,
    "led_module_count": 27,
    "return_depth_mm": 80,
}


class TestVolumetricProfileDepthResolver(unittest.TestCase):
    def test_return_depth_60_resolves_to_60mm_variant(self) -> None:
        base = {"MAT-PROFIL-LATERAL-LITERE-60MM": 3.0}
        rates, trace = resolve_volumetric_material_rates_with_trace(
            base,
            {"return_depth_mm": 60, "selected_psu_watts": 100},
            template_code=VOLUMETRIC_TEMPLATE_CODE,
        )
        profile = trace.profile_lateral
        self.assertEqual(profile.resolution_status, RESOLUTION_RESOLVED)
        self.assertEqual(profile.source_code, "MAT-PROFIL-LATERAL-LITERE-60MM")
        self.assertEqual(profile.return_depth_mm, 60)
        self.assertEqual(profile.resolved_code, TEMPLATE_PROFILE_CODE)
        self.assertEqual(rates[TEMPLATE_PROFILE_CODE], 3.0)

    def test_maps_variant_rate_onto_template_code(self) -> None:
        base = {
            "MAT-PROFIL-LATERAL-LITERE-30MM": 2.0,
            "MAT-PROFIL-LATERAL-LITERE-60MM": 3.0,
            "MAT-PROFIL-LATERAL-LITERE-80MM": 4.0,
            "MAT-PROFIL-LATERAL-LITERE-100MM": 5.0,
        }
        out = resolve_volumetric_material_rates(base, {"return_depth_mm": 80})
        self.assertEqual(out[TEMPLATE_PROFILE_CODE], 4.0)
        self.assertEqual(out["MAT-PROFIL-LATERAL-LITERE-80MM"], 4.0)

    def test_unknown_depth_does_not_alias(self) -> None:
        base = {"MAT-PROFIL-LATERAL-LITERE-60MM": 3.0}
        out = resolve_volumetric_material_rates(base, {"return_depth_mm": 50})
        self.assertNotIn(TEMPLATE_PROFILE_CODE, out)

    def test_missing_return_depth_does_not_alias(self) -> None:
        base = {"MAT-PROFIL-LATERAL-LITERE-60MM": 3.0}
        quote_input = {"letter_perimeter_m": 10.0}
        out = resolve_volumetric_material_rates(base, quote_input)
        self.assertNotIn(TEMPLATE_PROFILE_CODE, out)
        trace = resolve_profile_lateral_material_rate(
            base, quote_input, template_code=VOLUMETRIC_TEMPLATE_CODE
        )
        self.assertEqual(trace.resolution_status, RESOLUTION_MISSING_RETURN_DEPTH_MM)

    def test_unsupported_return_depth_70_does_not_alias(self) -> None:
        base = {"MAT-PROFIL-LATERAL-LITERE-60MM": 3.0}
        out = resolve_volumetric_material_rates(base, {"return_depth_mm": 70})
        self.assertNotIn(TEMPLATE_PROFILE_CODE, out)
        trace = resolve_profile_lateral_material_rate(
            base, {"return_depth_mm": 70}, template_code=VOLUMETRIC_TEMPLATE_CODE
        )
        self.assertEqual(trace.resolution_status, RESOLUTION_UNSUPPORTED_RETURN_DEPTH_MM)

    def test_non_volumetric_template_skips_alias(self) -> None:
        base = {"MAT-PROFIL-LATERAL-LITERE-60MM": 3.0}
        trace = resolve_profile_lateral_material_rate(
            base,
            {"return_depth_mm": 60},
            template_code="TPL-ACP-LIGHT-ROUTED",
        )
        self.assertEqual(trace.resolution_status, RESOLUTION_SKIPPED_NON_VOLUMETRIC_TEMPLATE)

    def test_only_profile_code_is_aliased(self) -> None:
        base = {
            "MAT-PROFIL-LATERAL-LITERE-60MM": 3.0,
            "MAT-ACP-FATA-LITERE": 16.0,
        }
        out = resolve_volumetric_material_rates(
            base, {"return_depth_mm": 60}, template_code=VOLUMETRIC_TEMPLATE_CODE
        )
        self.assertEqual(out["MAT-ACP-FATA-LITERE"], 16.0)
        self.assertEqual(out[TEMPLATE_PROFILE_CODE], 3.0)

    def test_variant_missing_rate_fails_closed(self) -> None:
        trace = resolve_profile_lateral_material_rate(
            {},
            {"return_depth_mm": 60},
            template_code=VOLUMETRIC_TEMPLATE_CODE,
        )
        self.assertEqual(trace.resolution_status, RESOLUTION_VARIANT_RATE_MISSING)
        self.assertEqual(trace.source_code, "MAT-PROFIL-LATERAL-LITERE-60MM")


class TestVolumetricProfileDepthRegistry(unittest.TestCase):
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
            for row in OWNER_CONFIRMED_PROFILE_DEPTH_PRICES:
                code = row["code"]
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
                        unit="ml",
                        category="profil_metal",
                        unit_cost=None,
                        status="missing_price",
                    )
                )
            session.add(
                Inventory_materials(
                    code=TEMPLATE_PROFILE_CODE,
                    name="Profil lateral litere",
                    unit="ml",
                    category="profil_metal",
                    unit_cost=None,
                    status="missing_price",
                )
            )
            await session.commit()

    def test_depth_variants_active_in_registry(self) -> None:
        from core.database import db_manager
        from services.inventory_materials_admin_service import get_inventory_material_by_code

        async def _go():
            async with db_manager.async_session_maker() as session:
                out = {}
                for spec in OWNER_CONFIRMED_PROFILE_DEPTH_PRICES:
                    row = await get_inventory_material_by_code(session, spec["code"])
                    out[spec["code"]] = row
                return out

        rows = _run(_go())
        for spec in OWNER_CONFIRMED_PROFILE_DEPTH_PRICES:
            row = rows[spec["code"]]
            self.assertEqual(row["status"], "active")
            self.assertEqual(row["unit_cost"], spec["unit_cost"])

    def test_engine_unblocks_profile_with_return_depth_mm(self) -> None:
        rates = {spec["code"]: spec["unit_cost"] for spec in OWNER_CONFIRMED_PROFILE_DEPTH_PRICES}
        rates.update(
            {
                "MAT-ACP-FATA-LITERE": 16.0,
                "MAT-SPATE-PVC-LITERE": 16.0,
                "MAT-LED-MODULE": 0.5,
            }
        )
        resolved = resolve_volumetric_material_rates(rates, FULL_QUOTE_INPUT)
        components = _volumetric_letters_components()
        template = {
            "template_code": "TPL-VOLUMETRIC-LETTERS",
            "components_json": json.dumps(components),
            "operations_json": "[]",
            "required_materials_json": "[]",
        }
        ctx = ComponentCostContext(
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
        )
        out = build_execution_layers_from_components(template, ctx)
        missing = [
            e
            for e in out.get("errors") or []
            if e.get("kind") == ERR_MATERIAL_RATE_MISSING
            and TEMPLATE_PROFILE_CODE in str(e.get("detail") or "")
        ]
        self.assertEqual(missing, [], msg=out.get("errors"))


if __name__ == "__main__":
    unittest.main()
