"""ACM template pack — seeds, formulas, SVG mapping, preliminary costing."""

from __future__ import annotations

import asyncio
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from seeds.seed_acm_bond_materials import seed_acm_bond_materials  # noqa: E402
from seeds.seed_acm_owner_confirmed_prices import seed_acm_owner_confirmed_prices  # noqa: E402
from scripts.seed_acm_template_pack import (  # noqa: E402
    CUT_ACM_QUOTE_INPUT_KEYS,
    ACM_CASSETTED_QUOTE_INPUT_KEYS,
    seed_acm_template_pack,
)
from services.acm_bond_material_rate_resolver import (  # noqa: E402
    RESOLUTION_RESOLVED,
    resolve_acm_bond_panel_material_rate,
)
from services.acm_quote_input_helpers import (  # noqa: E402
    derive_acm_casetted_quote_input,
    derive_cut_acm_quote_input,
)
from services.cost_engine_service import ComponentCostContext, build_execution_layers_from_components  # noqa: E402
from services.formula_handlers import resolve_formula  # noqa: E402
from services.svg_layer_template_mapping import map_svg_layer_to_template  # noqa: E402
from services.svg_layer_analysis_service import SvgLayerAnalysisService  # noqa: E402
from tests._db_fixture import IsolatedDBFixture  # noqa: E402

from models.inventory_materials import Inventory_materials  # noqa: E402
from models.product_templates import Product_templates  # noqa: E402
from sqlalchemy import select  # noqa: E402


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


MULTI_LAYER_SVG = """
<svg width="2880mm" height="1000mm" viewBox="0 0 2880 1000"
  xmlns="http://www.w3.org/2000/svg">
  <g id="TPL-VOLUMETRIC-LETTERS"><rect width="2880" height="800"/></g>
  <g id="TPL-ACM-CASSETTED-PANEL"><rect width="2880" height="1000"/></g>
  <g id="TPL-CUT-ACM-LETTERS"><rect width="500" height="200"/></g>
</svg>
""".strip()

CASSETTED_QUOTE_INPUT = {
    "panel_width_mm": 2880,
    "panel_height_mm": 1000,
    "acm_thickness_mm": 3,
    "return_depth_mm": 60,
    "rear_lip_mm": 25,
    "fold_sides": "all",
    "v_groove_angle_deg": 135,
    "frame_clearance_mm": 10,
    "quantity": 1,
}

CUT_QUOTE_INPUT = {
    "cut_area_m2": 0.1,
    "cut_perimeter_m": 12.0,
    "acm_thickness_mm": 3,
    "quantity": 1,
}


class TestAcmFormulas(unittest.TestCase):
    def test_rectangular_panel_area(self) -> None:
        res = resolve_formula(
            "rectangular_panel_area",
            {"waste_pct": 0},
            {"panel_width_mm": 2880, "panel_height_mm": 1000},
        )
        self.assertTrue(res.resolved)
        self.assertAlmostEqual(res.value, 2.88, places=2)

    def test_rectangular_panel_perimeter(self) -> None:
        res = resolve_formula(
            "rectangular_panel_perimeter",
            {},
            {"panel_width_mm": 2880, "panel_height_mm": 1000},
        )
        self.assertTrue(res.resolved)
        self.assertAlmostEqual(res.value, 7.76, places=2)

    def test_fold_length_all_sides(self) -> None:
        res = resolve_formula(
            "fold_length_from_sides",
            {},
            {
                "panel_width_mm": 1000,
                "panel_height_mm": 500,
                "fold_sides": "all",
            },
        )
        self.assertTrue(res.resolved)
        self.assertAlmostEqual(res.value, 3.0, places=2)

    def test_missing_panel_dims_fail(self) -> None:
        res = resolve_formula("rectangular_panel_area", {}, {})
        self.assertFalse(res.resolved)

    def test_rear_lip_warning(self) -> None:
        payload, warnings, blockers = derive_acm_casetted_quote_input(
            {**CASSETTED_QUOTE_INPUT, "rear_lip_mm": 20}
        )
        self.assertIn("rear_lip_below_minimum_25mm_two_fold", warnings)
        self.assertIn("fold_length_m", payload)


class TestAcmSvgMapping(unittest.TestCase):
    def test_three_exact_layers_map(self) -> None:
        for code in (
            "TPL-VOLUMETRIC-LETTERS",
            "TPL-ACM-CASSETTED-PANEL",
            "TPL-CUT-ACM-LETTERS",
        ):
            m = map_svg_layer_to_template(code)
            self.assertEqual(m.mapping_status, "mapped", code)
            self.assertEqual(m.mapped_template_code, code)

    def test_multi_layer_analysis_all_mapped(self) -> None:
        result = SvgLayerAnalysisService.analyze(MULTI_LAYER_SVG)
        self.assertEqual(result.summary["layers_mapped"], 3)
        self.assertEqual(result.summary["layers_unmapped"], 0)


class TestAcmTemplatePackSeeds(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.db_fixture = IsolatedDBFixture(prefix="acm_template_pack_testdb_")
        cls.db_fixture.setup()
        _run(cls._seed_all())

    @classmethod
    def tearDownClass(cls) -> None:
        cls.db_fixture.teardown()

    @classmethod
    async def _seed_all(cls) -> None:
        await seed_acm_bond_materials()
        await seed_acm_owner_confirmed_prices()
        await seed_acm_template_pack()
        await cls._seed_workcenter_rates()

    @classmethod
    async def _seed_workcenter_rates(cls) -> None:
        from core.database import db_manager
        from models.workcenter_rates import Workcenter_rates

        rates = {
            "PANEL_CUTTING": 120.0,
            "CNC_ROUTER": 150.0,
            "ASSEMBLY": 100.0,
            "FINISHING": 90.0,
        }
        async with db_manager.async_session_maker() as session:
            for code, rate in rates.items():
                existing = await session.execute(
                    select(Workcenter_rates).where(Workcenter_rates.code == code)
                )
                row = existing.scalar_one_or_none()
                if row is None:
                    session.add(
                        Workcenter_rates(
                            code=code,
                            label=code,
                            rate_per_hour=rate,
                            status="active",
                        )
                    )
                else:
                    row.rate_per_hour = rate
                    row.status = "active"
            await session.commit()

    def test_templates_exist_with_formula_metadata(self) -> None:
        async def _go():
            async with self.db_fixture.session_maker() as session:
                for code in ("TPL-ACM-CASSETTED-PANEL", "TPL-CUT-ACM-LETTERS"):
                    row = await session.execute(
                        select(Product_templates).where(
                            Product_templates.template_code == code
                        )
                    )
                    tpl = row.scalar_one_or_none()
                    self.assertIsNotNone(tpl, code)
                    comps = json.loads(tpl.components_json)
                    self.assertGreater(len(comps), 0)
                    has_formula = any(
                        m.get("calculation_type") == "formula_based"
                        for c in comps
                        for m in c.get("materials", []) + c.get("operations", [])
                    )
                    self.assertTrue(has_formula, code)

        _run(_go())

    def test_acm_3mm_owner_confirmed_price(self) -> None:
        async def _go():
            async with self.db_fixture.session_maker() as session:
                row = await session.execute(
                    select(Inventory_materials).where(
                        Inventory_materials.code == "MAT-ACM-BOND-3MM"
                    )
                )
                mat = row.scalar_one_or_none()
                self.assertIsNotNone(mat)
                self.assertEqual(mat.unit_cost, 15.0)
                self.assertEqual(str(mat.currency).upper(), "EUR")

        _run(_go())

    def test_acm_4mm_needs_review_not_fake_active_owner(self) -> None:
        async def _go():
            async with self.db_fixture.session_maker() as session:
                row = await session.execute(
                    select(Inventory_materials).where(
                        Inventory_materials.code == "MAT-ACM-BOND-4MM"
                    )
                )
                mat = row.scalar_one_or_none()
                self.assertIsNotNone(mat)
                self.assertEqual(str(mat.source_review_status), "needs_review")

        _run(_go())

    def test_casetted_preliminary_cost_engine_resolves(self) -> None:
        payload, _, blockers = derive_acm_casetted_quote_input(CASSETTED_QUOTE_INPUT)
        self.assertEqual(blockers, [])
        async def _go():
            async with self.db_fixture.session_maker() as session:
                row = await session.execute(
                    select(Product_templates).where(
                        Product_templates.template_code == "TPL-ACM-CASSETTED-PANEL"
                    )
                )
                tpl = row.scalar_one_or_none()
                self.assertIsNotNone(tpl)
                material_rates = {"MAT-ACM-BOND-3MM": 15.0, "MAT-ACM-BOND-PANEL": 15.0}
                material_rates["MAT-SURUBURI-GEN"] = 5.0
                resolved = resolve_acm_bond_panel_material_rate(
                    material_rates,
                    payload,
                    template_code="TPL-ACM-CASSETTED-PANEL",
                )
                self.assertEqual(resolved.resolution_status, RESOLUTION_RESOLVED)
                material_rates["MAT-ACM-BOND-PANEL"] = resolved.unit_cost
                product_template = {
                    "template_code": "TPL-ACM-CASSETTED-PANEL",
                    "components_json": tpl.components_json,
                }
                ctx = ComponentCostContext(
                    material_rates=material_rates,
                    workcenter_rates={
                        "PANEL_CUTTING": 120.0,
                        "CNC_ROUTER": 150.0,
                        "ASSEMBLY": 100.0,
                    },
                    quantity=1,
                    quote_input=payload,
                )
                v2 = build_execution_layers_from_components(product_template, ctx)
                self.assertTrue(v2["is_valid"], v2.get("errors"))

        _run(_go())

    def test_cut_acm_preliminary_cost_engine_resolves(self) -> None:
        payload, _, blockers = derive_cut_acm_quote_input(CUT_QUOTE_INPUT)
        self.assertEqual(blockers, [])

        async def _go():
            async with self.db_fixture.session_maker() as session:
                row = await session.execute(
                    select(Product_templates).where(
                        Product_templates.template_code == "TPL-CUT-ACM-LETTERS"
                    )
                )
                tpl = row.scalar_one_or_none()
                material_rates = {"MAT-ACM-BOND-3MM": 15.0, "MAT-ACM-BOND-PANEL": 15.0}
                resolved = resolve_acm_bond_panel_material_rate(
                    material_rates,
                    payload,
                    template_code="TPL-CUT-ACM-LETTERS",
                )
                material_rates["MAT-ACM-BOND-PANEL"] = resolved.unit_cost
                product_template = {
                    "template_code": "TPL-CUT-ACM-LETTERS",
                    "components_json": tpl.components_json,
                }
                ctx = ComponentCostContext(
                    material_rates=material_rates,
                    workcenter_rates={
                        "CNC_ROUTER": 150.0,
                        "FINISHING": 90.0,
                    },
                    quantity=1,
                    quote_input=payload,
                )
                v2 = build_execution_layers_from_components(product_template, ctx)
                self.assertTrue(v2["is_valid"], v2.get("errors"))

        _run(_go())

    def test_quote_input_keys_documented(self) -> None:
        self.assertIn("panel_width_mm", ACM_CASSETTED_QUOTE_INPUT_KEYS)
        self.assertIn("cut_perimeter_m", CUT_ACM_QUOTE_INPUT_KEYS)
