"""TPL-VOLUMETRIC-LETTERS — MAT-VOPSEA-RAL whole-tube material vs PAINTING service."""

from __future__ import annotations

import asyncio
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from seeds.seed_active_template_scope import seed_active_template_scope  # noqa: E402
from seeds.seed_build4_templates import _volumetric_letters_components  # noqa: E402
from seeds.seed_volumetric_owner_confirmed_prices import (  # noqa: E402
    OWNER_CONFIRMED_VOLUMETRIC_PRICES,
    seed_volumetric_owner_confirmed_prices,
)
from seeds.seed_volumetric_workcenter_rates import seed_volumetric_operations_and_rates  # noqa: E402
from services.cost_engine_service import (  # noqa: E402
    ERR_NEEDS_QUOTE_INPUT,
    ERR_MATERIAL_RATE_MISSING,
    ComponentCostContext,
    build_execution_layers_from_components,
)
from services.formula_handlers import resolve_formula  # noqa: E402
from services.pricing_registry_service import PricingRegistryService  # noqa: E402
from services.volumetric_material_rate_resolver import (  # noqa: E402
    resolve_volumetric_material_rates_with_trace,
)
from tests._db_fixture import IsolatedDBFixture  # noqa: E402

from models.inventory_materials import Inventory_materials  # noqa: E402
from sqlalchemy import select  # noqa: E402


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


BASE_QUOTE_INPUT = {
    "letter_face_area_m2": 2.88,
    "letter_perimeter_m": 18.0,
    "letter_count": 9,
    "return_depth_mm": 60,
    "selected_psu_watts": 100,
    "psu_watts": 100,
    "led_module_count": 180,
    "mounting_template_area_m2": 2.88,
    "face_finish_type": "none",
    "mounting_system": "direct_wall",
    "mounting_template_enabled": True,
    "back_bevel_enabled": False,
}


def _full_quote_input(**overrides) -> dict:
    return {**BASE_QUOTE_INPUT, **overrides}


def _template_payload() -> dict:
    return {
        "template_code": "TPL-VOLUMETRIC-LETTERS",
        "components_json": json.dumps(_volumetric_letters_components()),
        "operations_json": "[]",
        "required_materials_json": "[]",
    }


def _mat_by_code(out: dict, code: str) -> dict | None:
    for comp in out.get("components") or []:
        for md in comp.get("materials_detail") or []:
            if md.get("material_code") == code:
                return md
    return None


def _op_by_code(out: dict, code: str) -> dict | None:
    for comp in out.get("components") or []:
        for op in comp.get("operations_detail") or []:
            if op.get("code") == code:
                return op
    return None


def _vopsea_seed_row() -> dict:
    return next(r for r in OWNER_CONFIRMED_VOLUMETRIC_PRICES if r["code"] == "MAT-VOPSEA-RAL")


class TestCeilQuoteInputQuantityFormula(unittest.TestCase):
    def test_three_tubes_integer(self) -> None:
        res = resolve_formula(
            "ceil_quote_input_quantity",
            {"quote_input_key": "paint_tube_count"},
            {"paint_tube_count": 3},
        )
        self.assertTrue(res.resolved)
        self.assertEqual(res.value, 3.0)
        self.assertEqual(res.breakdown.get("charged_integer_quantity"), 3)

    def test_three_point_two_tubes_ceil_to_four(self) -> None:
        res = resolve_formula(
            "ceil_quote_input_quantity",
            {},
            {"paint_tube_count": 3.2},
        )
        self.assertTrue(res.resolved)
        self.assertEqual(res.value, 4.0)
        self.assertAlmostEqual(res.breakdown.get("raw_estimate"), 3.2)

    def test_fallback_estimated_paint_tubes(self) -> None:
        res = resolve_formula("ceil_quote_input_quantity", {}, {"estimated_paint_tubes": 2.1})
        self.assertTrue(res.resolved)
        self.assertEqual(res.value, 3.0)

    def test_missing_input_fails(self) -> None:
        res = resolve_formula("ceil_quote_input_quantity", {}, {})
        self.assertFalse(res.resolved)
        self.assertIsNone(res.value)
        self.assertEqual(res.error["kind"], "MISSING_INPUT")


class TestPaintMaterialTemplateDefinition(unittest.TestCase):
    def test_vopsea_uses_tube_formula(self) -> None:
        for comp in _volumetric_letters_components():
            if comp.get("component_id") != "comp_finisaj_litere":
                continue
            vopsea = next(
                m for m in comp.get("materials") or []
                if m.get("material_code") == "MAT-VOPSEA-RAL"
            )
            self.assertEqual(vopsea.get("unit"), "buc")
            self.assertEqual(vopsea.get("formula_id"), "ceil_quote_input_quantity")
            return
        self.fail("MAT-VOPSEA-RAL not found")


class TestPaintMaterialCostEngine(unittest.TestCase):
    def _build(self, quote_input: dict, rates: dict | None = None) -> dict:
        material_rates = rates or {"MAT-VOPSEA-RAL": 10.0}
        ctx = ComponentCostContext(
            material_rates=material_rates,
            workcenter_rates={"PAINTING": {"rate_basis": "per_linear_meter", "rate_per_linear_meter": 4.0}},
            quantity=1,
            quote_input=quote_input,
        )
        return build_execution_layers_from_components(_template_payload(), ctx)

    def test_three_tubes_thirty_eur_material(self) -> None:
        out = self._build(
            _full_quote_input(
                paint_tube_count=3,
                volume_finish="paint_after_face_miter_bond",
            )
        )
        mat = _mat_by_code(out, "MAT-VOPSEA-RAL")
        self.assertIsNotNone(mat)
        self.assertEqual(mat["quantity"], 3.0)
        self.assertAlmostEqual(mat["line_total"], 30.0)

    def test_three_point_two_tubes_forty_eur_material(self) -> None:
        out = self._build(
            _full_quote_input(
                paint_tube_count=3.2,
                volume_finish="paint_after_face_miter_bond",
            )
        )
        mat = _mat_by_code(out, "MAT-VOPSEA-RAL")
        self.assertIsNotNone(mat)
        self.assertEqual(mat["quantity"], 4.0)
        self.assertAlmostEqual(mat["line_total"], 40.0)

    def test_missing_paint_tube_count_blocks_in_paint_mode(self) -> None:
        out = self._build(
            {
                **BASE_QUOTE_INPUT,
                "volume_finish": "paint_after_face_miter_bond",
            }
        )
        kinds = {e.get("kind") for e in out.get("errors") or []}
        self.assertIn(ERR_NEEDS_QUOTE_INPUT, kinds)
        mat = _mat_by_code(out, "MAT-VOPSEA-RAL")
        self.assertIsNotNone(mat)
        self.assertFalse(mat.get("resolved", True))

    def test_stock_cant_without_paint_tubes_does_not_block(self) -> None:
        out = self._build(
            {
                **BASE_QUOTE_INPUT,
                "volume_finish": "none",
                "return_color": "white",
            }
        )
        kinds = {e.get("kind") for e in out.get("errors") or []}
        self.assertNotIn(ERR_NEEDS_QUOTE_INPUT, kinds)
        mat = _mat_by_code(out, "MAT-VOPSEA-RAL")
        self.assertIsNotNone(mat)
        self.assertTrue(mat.get("skipped"))
        self.assertEqual(mat.get("skip_reason"), "gate:paint_finish_inactive")

    def test_stale_paint_tubes_stock_mode_no_block(self) -> None:
        out = self._build(
            {
                **BASE_QUOTE_INPUT,
                "volume_finish": "none",
                "paint_tube_count": 3,
            }
        )
        kinds = {e.get("kind") for e in out.get("errors") or []}
        self.assertNotIn(ERR_NEEDS_QUOTE_INPUT, kinds)
        mat = _mat_by_code(out, "MAT-VOPSEA-RAL")
        self.assertTrue(mat.get("skipped"))

    def test_painting_operation_separate_seventy_two_eur(self) -> None:
        out = self._build(
            _full_quote_input(
                paint_tube_count=3,
                volume_finish="paint_after_face_miter_bond",
            )
        )
        paint_op = _op_by_code(out, "painting")
        mat = _mat_by_code(out, "MAT-VOPSEA-RAL")
        self.assertIsNotNone(paint_op)
        self.assertIsNotNone(mat)
        self.assertAlmostEqual(paint_op["line_total"], 72.0)
        self.assertAlmostEqual(mat["line_total"], 30.0)
        self.assertNotAlmostEqual(paint_op["line_total"], mat["line_total"])


class TestPaintMaterialIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.db_fixture = IsolatedDBFixture(prefix="volumetric_paint_tube_")
        cls.db_fixture.setup()
        _run(cls._seed())

    @classmethod
    def tearDownClass(cls) -> None:
        cls.db_fixture.teardown()

    @classmethod
    async def _seed(cls) -> None:
        from core.database import db_manager
        from seeds.seed_build4_templates import seed_build4_templates

        codes = [
            ("MAT-ACP-FATA-LITERE", "mp"),
            ("MAT-SPATE-PVC-LITERE", "mp"),
            ("MAT-LED-MODULE", "buc"),
            ("MAT-SABLON-MONTAJ", "mp"),
            ("MAT-VOPSEA-RAL", "buc"),
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
        await seed_build4_templates()
        await seed_volumetric_owner_confirmed_prices()
        await seed_volumetric_operations_and_rates()
        await seed_active_template_scope()

    def test_owner_confirmed_ten_eur_per_tube(self) -> None:
        row = _vopsea_seed_row()
        self.assertEqual(row["unit_cost"], 10.0)
        self.assertIn("50 RON/tub", row["source_notes"])

    def test_pricing_registry_owner_confirmed_vopsea(self) -> None:
        from core.database import db_manager

        async def _go():
            async with db_manager.async_session_maker() as session:
                svc = PricingRegistryService(session)
                reg = await svc.build_registry(template_filter="TPL-VOLUMETRIC-LETTERS")
                return reg

        reg = _run(_go())
        vopsea = next(
            (i for i in reg["items"] if i["pricing_code"] == "MAT-VOPSEA-RAL"),
            None,
        )
        self.assertIsNotNone(vopsea)
        self.assertEqual(vopsea["confidence"], "owner_confirmed")
        self.assertAlmostEqual(float(vopsea["base_cost"]), 10.0)

    def test_product_001_paint_lines(self) -> None:
        from core.database import db_manager
        from services.inventory_materials_admin_service import list_inventory_materials_admin
        from services.workcenter_rates_service import load_workcenter_rate_dict

        async def _go():
            async with db_manager.async_session_maker() as session:
                registry = await list_inventory_materials_admin(session)
                rates = {}
                for row in registry:
                    if str(row.get("status")) == "active" and row.get("unit_cost"):
                        rates[row["code"]] = float(row["unit_cost"])
                wc = await load_workcenter_rate_dict(session)
                resolved, _ = resolve_volumetric_material_rates_with_trace(
                    rates,
                    _full_quote_input(paint_tube_count=3),
                    template_code="TPL-VOLUMETRIC-LETTERS",
                )
                return build_execution_layers_from_components(
                    _template_payload(),
                    ComponentCostContext(
                        material_rates=resolved,
                        workcenter_rates=wc,
                        base_currency="EUR",
                        quantity=1,
                        quote_input=_full_quote_input(paint_tube_count=3),
                    ),
                )

        out = _run(_go())
        mat = _mat_by_code(out, "MAT-VOPSEA-RAL")
        paint_op = _op_by_code(out, "painting")
        self.assertIsNotNone(mat)
        self.assertIsNotNone(paint_op)
        self.assertAlmostEqual(mat["line_total"], 30.0)
        self.assertAlmostEqual(paint_op["line_total"], 72.0)

        vopsea_missing = [
            e
            for e in out.get("errors") or []
            if e.get("kind") == ERR_MATERIAL_RATE_MISSING
            and "MAT-VOPSEA-RAL" in str(e.get("detail") or "")
        ]
        self.assertEqual(vopsea_missing, [])


if __name__ == "__main__":
    unittest.main()
