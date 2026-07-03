"""Preliminary costing — LED perimeter pitch, sablon area, estimated registry rows."""

from __future__ import annotations

import asyncio
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from seeds.seed_build4_templates import _volumetric_letters_components  # noqa: E402
from seeds.seed_volumetric_owner_confirmed_prices import (  # noqa: E402
    ESTIMATED_PRELIMINARY_ACTIVATED_CODES,
    OWNER_CONFIRMED_ACTIVATED_CODES,
    PRELIMINARY_COSTING_ALIAS_CODES,
    seed_volumetric_owner_confirmed_prices,
)
from services.cost_engine_service import (  # noqa: E402
    ERR_FORMULA_UNKNOWN,
    ERR_MATERIAL_RATE_MISSING,
    ComponentCostContext,
    build_execution_layers_from_components,
)
from services.formula_handlers import resolve_formula  # noqa: E402
from services.volumetric_material_rate_resolver import (  # noqa: E402
    RESOLUTION_RESOLVED,
    TEMPLATE_PSU_CODE,
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
    "return_depth_mm": 60,
    "selected_psu_watts": 100,
    "psu_watts": 100,
    "led_module_count": 180,
    "mounting_template_area_m2": 2.88,
    "paint_tube_count": 3,
    "face_finish_type": "none",
    "mounting_system": "direct_wall",
    "mounting_template_enabled": True,
    "back_bevel_enabled": False,
}


class TestLedPerimeterPitchFormula(unittest.TestCase):
    def test_18m_perimeter_yields_180_modules(self) -> None:
        res = resolve_formula(
            "led_per_letter",
            {"module_length_mm": 75, "module_gap_mm": 25},
            {"letter_perimeter_m": 18.0},
        )
        self.assertTrue(res.resolved)
        self.assertEqual(res.value, 180.0)
        self.assertEqual(res.breakdown.get("mode"), "perimeter_pitch")
        self.assertEqual(res.breakdown.get("pitch_mm"), 100.0)

    def test_missing_perimeter_fails(self) -> None:
        res = resolve_formula(
            "led_per_letter",
            {"module_length_mm": 75, "module_gap_mm": 25},
            {},
        )
        self.assertFalse(res.resolved)

    def test_legacy_letter_count_mode_unchanged(self) -> None:
        res = resolve_formula(
            "led_per_letter",
            {"modules_per_letter": 3},
            {"letter_count": 9},
        )
        self.assertTrue(res.resolved)
        self.assertEqual(res.value, 27.0)
        self.assertEqual(res.breakdown.get("mode"), "letter_count")


class TestMountingTemplateAreaFormula(unittest.TestCase):
    def test_mounting_template_area_m2_key(self) -> None:
        res = resolve_formula(
            "letter_face_area",
            {"waste_pct": 0, "area_quote_input_key": "mounting_template_area_m2"},
            {"mounting_template_area_m2": 2.88},
        )
        self.assertTrue(res.resolved)
        self.assertAlmostEqual(res.value, 2.88)

    def test_mounting_template_area_alias(self) -> None:
        res = resolve_formula(
            "mounting_template_area",
            {"waste_pct": 0.05},
            {"mounting_template_area_m2": 2.88},
        )
        self.assertTrue(res.resolved)
        self.assertAlmostEqual(res.value, 2.88144, places=5)


class TestPreliminaryRegistryAndEngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.db_fixture = IsolatedDBFixture()
        cls.db_fixture.setup()
        _run(cls._seed_stubs())
        _run(seed_volumetric_owner_confirmed_prices())

    @classmethod
    def tearDownClass(cls) -> None:
        cls.db_fixture.teardown()

    @classmethod
    async def _seed_stubs(cls) -> None:
        from core.database import db_manager

        codes = [
            ("MAT-ACP-FATA-LITERE", "mp"),
            ("MAT-SPATE-PVC-LITERE", "mp"),
            ("MAT-LED-MODULE", "buc"),
            ("MAT-SABLON-MONTAJ", "mp"),
            ("MAT-VOPSEA-RAL", "set"),
            ("MAT-CONSUMABILE-MONTAJ", "set"),
            ("MAT-PROFIL-LATERAL-LITERE", "ml"),
            ("MAT-PROFIL-LATERAL-LITERE-60MM", "ml"),
            ("MAT-LED-PSU-12V", "buc"),
            ("MAT-LED-PSU-12V-100W", "buc"),
        ]
        async with db_manager.async_session_maker() as session:
            for code, unit in codes:
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
                        unit=unit,
                        category="test",
                        status="missing_price",
                    )
                )
            await session.commit()

    def test_estimated_rows_needs_review(self) -> None:
        from core.database import db_manager
        from services.inventory_materials_admin_service import get_inventory_material_by_code

        async def _go():
            async with db_manager.async_session_maker() as session:
                out = {}
                for code in ESTIMATED_PRELIMINARY_ACTIVATED_CODES:
                    out[code] = await get_inventory_material_by_code(session, code)
                return out

        rows = _run(_go())
        for code in ESTIMATED_PRELIMINARY_ACTIVATED_CODES:
            self.assertEqual(rows[code]["status"], "active")
            self.assertEqual(rows[code]["source_review_status"], "needs_review")

    def test_preliminary_engine_resolves_core_materials(self) -> None:
        from core.database import db_manager
        from services.inventory_materials_admin_service import list_inventory_materials_admin

        async def _rates():
            async with db_manager.async_session_maker() as session:
                registry = await list_inventory_materials_admin(session)
            rates = {}
            for row in registry:
                if str(row.get("status")) == "active" and row.get("unit_cost"):
                    rates[row["code"]] = float(row["unit_cost"])
            return rates

        rates = _run(_rates())
        resolved, trace = resolve_volumetric_material_rates_with_trace(
            rates,
            FULL_QUOTE_INPUT,
            template_code="TPL-VOLUMETRIC-LETTERS",
        )
        self.assertEqual(trace.profile_lateral.resolution_status, RESOLUTION_RESOLVED)
        self.assertEqual(trace.led_psu_12v.resolution_status, RESOLUTION_RESOLVED)
        self.assertEqual(trace.led_psu_12v.source_code, "MAT-LED-PSU-12V-100W")

        components = _volumetric_letters_components()
        for comp in components:
            if comp.get("component_id") == "comp_led_litere":
                led_line = comp["materials"][0]
                self.assertEqual(led_line.get("requires_quote_input"), ["letter_perimeter_m"])
            if comp.get("component_id") == "comp_finisaj_litere":
                sablon = next(
                    m for m in comp["materials"] if m.get("material_code") == "MAT-SABLON-MONTAJ"
                )
                self.assertEqual(sablon.get("calculation_type"), "formula_based")
                self.assertEqual(
                    sablon.get("requires_quote_input"), ["mounting_template_area_m2"]
                )

        out = build_execution_layers_from_components(
            {
                "template_code": "TPL-VOLUMETRIC-LETTERS",
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
        kinds = {e.get("kind") for e in out.get("errors") or []}
        self.assertNotIn(ERR_FORMULA_UNKNOWN, kinds)

        led_mat = None
        for comp in out.get("components") or []:
            for md in comp.get("materials_detail") or []:
                if md.get("material_code") == "MAT-LED-MODULE":
                    led_mat = md
        self.assertIsNotNone(led_mat)
        self.assertEqual(led_mat["quantity"], 180.0)

        missing_template_codes = []
        for e in out.get("errors") or []:
            if e.get("kind") != ERR_MATERIAL_RATE_MISSING:
                continue
            detail = str(e.get("detail") or "")
            for code in OWNER_CONFIRMED_ACTIVATED_CODES | ESTIMATED_PRELIMINARY_ACTIVATED_CODES:
                if code in detail:
                    missing_template_codes.append(code)
        for alias in PRELIMINARY_COSTING_ALIAS_CODES:
            self.assertNotIn(alias, missing_template_codes)


if __name__ == "__main__":
    unittest.main()
