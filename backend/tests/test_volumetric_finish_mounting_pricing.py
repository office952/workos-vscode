"""TPL-VOLUMETRIC-LETTERS — face finish, mounting template, and premount bar pricing."""

from __future__ import annotations

import asyncio
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from seeds.seed_active_template_scope import seed_active_template_scope  # noqa: E402
from seeds.seed_build4_templates import (  # noqa: E402
    _volumetric_letters_components,
    seed_build4_templates,
)
from seeds.seed_volumetric_owner_confirmed_prices import (  # noqa: E402
    seed_volumetric_owner_confirmed_prices,
)
from seeds.seed_volumetric_workcenter_rates import (  # noqa: E402
    seed_volumetric_operations_and_rates,
)
from services.cost_engine_service import (  # noqa: E402
    ERR_NEEDS_QUOTE_INPUT,
    ComponentCostContext,
    build_execution_layers_from_components,
)
from services.volumetric_material_rate_resolver import (  # noqa: E402
    resolve_volumetric_material_rates_with_trace,
)
from services.volumetric_quote_input_policy import (  # noqa: E402
    WARNING_ACM_SEPARATE_TEMPLATE,
    WARNING_MOUNTING_BAR_PROFILE_PRICE_MISSING,
    WARNING_MOUNTING_LABOR_NOT_PRICED,
    WARNING_PRODUCTION_METADATA_MISSING,
    collect_volumetric_captured_unpriced_warnings,
)
from services.formula_handlers import resolve_formula  # noqa: E402
from tests._db_fixture import IsolatedDBFixture  # noqa: E402

from models.inventory_materials import Inventory_materials  # noqa: E402
from sqlalchemy import select  # noqa: E402


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


BASE_QUOTE_INPUT = {
    "width_mm": 4800,
    "height_mm": 600,
    "depth_mm": 60,
    "letter_face_area_m2": 2.88,
    "letter_perimeter_m": 18.0,
    "return_material_perimeter_ml": 18.0,
    "cnc_cutting_perimeter_ml": 18.0,
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


def _template_payload() -> dict:
    return {
        "template_code": "TPL-VOLUMETRIC-LETTERS",
        "components_json": json.dumps(_volumetric_letters_components()),
        "operations_json": "[]",
        "required_materials_json": "[]",
    }


def _op_by_code(out: dict, code: str) -> dict | None:
    for comp in out.get("components") or []:
        for op in comp.get("operations_detail") or []:
            if op.get("code") == code:
                return op
    return None


def _mat_by_code(out: dict, code: str) -> dict | None:
    for comp in out.get("components") or []:
        for mat in comp.get("materials_detail") or []:
            if mat.get("material_code") == code:
                return mat
    return None


def _workcenter_rates_fixture() -> dict:
    return {
        "PREPRESS": {"rate_basis": "per_piece", "rate_per_linear_meter": 2.0},
        "CNC_ROUTER": {"rate_basis": "per_linear_meter", "rate_per_linear_meter": 1.5},
        "LED_ASSEMBLY": {"rate_basis": "per_piece", "rate_per_linear_meter": 0.05},
        "ELECTRICAL_WIRING": {"rate_basis": "per_piece", "rate_per_linear_meter": 2.0},
        "PAINTING": {"rate_basis": "per_linear_meter", "rate_per_linear_meter": 4.0},
        "PACKAGING": {"rate_basis": "per_square_meter", "rate_per_linear_meter": 10.0},
        "VINYL_APPLICATION": {"rate_basis": "per_square_meter", "rate_per_linear_meter": 3.0},
        "FACE_VINYL_APPLICATION_LABOR": {
            "rate_basis": "per_square_meter",
            "rate_per_linear_meter": 5.0,
        },
        "RETURN_PROFILE_MACHINE_FORMING": {
            "rate_basis": "per_linear_meter",
            "rate_per_linear_meter": 5.0,
        },
        "RETURN_PROFILE_FACE_BONDING": {
            "rate_basis": "per_linear_meter",
            "rate_per_linear_meter": 5.0,
        },
    }


MATERIAL_RATES = {
    "MAT-ACP-FATA-LITERE": 16.0,
    "MAT-SPATE-PVC-LITERE": 16.0,
    "MAT-LED-MODULE": 0.5,
    "MAT-SABLON-MONTAJ": 6.0,
    "MAT-SABLON-HARTIE": 5.0,
    "MAT-VOPSEA-RAL": 10.0,
    "MAT-CONSUMABILE-MONTAJ": 5.0,
    "MAT-PROFIL-LATERAL-LITERE-60MM": 3.0,
    "MAT-LED-PSU-12V-100W": 16.0,
    "MAT-ORACAL-651": 5.0,
    "MAT-VINYL-PRINT": 10.0,
    "MAT-VINYL-PRINT-LAMINATED": 10.0,
    "MAT-PREMOUNT-BAR-STEEL": 2.0,
    "MAT-PREMOUNT-BAR-ALUMINUM": 3.5,
}


class TestVolumetricFinishMountingPricing(unittest.TestCase):
    def _build(self, quote_input: dict | None = None) -> dict:
        qi = dict(quote_input or BASE_QUOTE_INPUT)
        ctx = ComponentCostContext(
            material_rates=dict(MATERIAL_RATES),
            workcenter_rates=_workcenter_rates_fixture(),
            quantity=1,
            quote_input=qi,
        )
        return build_execution_layers_from_components(_template_payload(), ctx)

    def test_oracal_651_material_and_application(self) -> None:
        out = self._build({**BASE_QUOTE_INPUT, "face_finish_type": "oracal_651"})
        mat = _mat_by_code(out, "MAT-ORACAL-651")
        op = _op_by_code(out, "vinyl_application")
        used_sqm = round(2.88 * 1.10, 6)
        self.assertIsNotNone(mat)
        self.assertAlmostEqual(mat["line_total"], round(used_sqm * 5, 4))
        self.assertIsNotNone(op)
        self.assertAlmostEqual(op["line_total"], round(used_sqm * 5, 4))
        self.assertAlmostEqual(op.get("rate_per_linear_meter"), 5.0)
        breakdown = (op.get("formula_breakdown") or {})
        self.assertTrue(breakdown.get("fallback_weak_estimate"))
        warnings = collect_volumetric_captured_unpriced_warnings(
            "TPL-VOLUMETRIC-LETTERS",
            {**BASE_QUOTE_INPUT, "face_finish_type": "oracal_651"},
        )
        self.assertIn(
            f"{WARNING_PRODUCTION_METADATA_MISSING}:face_vinyl_color_code",
            warnings,
        )
        self.assertIn(
            f"{WARNING_PRODUCTION_METADATA_MISSING}:face_vinyl_roll_width_mm",
            warnings,
        )

    def test_printed_vinyl_material_and_application(self) -> None:
        out = self._build({**BASE_QUOTE_INPUT, "face_finish_type": "printed_vinyl"})
        mat = _mat_by_code(out, "MAT-VINYL-PRINT")
        op = _op_by_code(out, "vinyl_application")
        used_sqm = round(2.88 * 1.10, 6)
        self.assertAlmostEqual(mat["line_total"], round(used_sqm * 10, 4))
        self.assertAlmostEqual(op["line_total"], round(used_sqm * 5, 4))

    def test_printed_laminated_vinyl_material_and_application(self) -> None:
        out = self._build(
            {**BASE_QUOTE_INPUT, "face_finish_type": "printed_laminated_vinyl"}
        )
        mat = _mat_by_code(out, "MAT-VINYL-PRINT-LAMINATED")
        op = _op_by_code(out, "vinyl_application")
        used_sqm = round(2.88 * 1.10, 6)
        self.assertAlmostEqual(mat["line_total"], round(used_sqm * 10, 4))
        self.assertAlmostEqual(op["line_total"], round(used_sqm * 5, 4))

    def test_face_finish_none_skips_vinyl_lines(self) -> None:
        out = self._build(BASE_QUOTE_INPUT)
        oracal = _mat_by_code(out, "MAT-ORACAL-651")
        if oracal is not None:
            self.assertTrue(oracal.get("skipped"))
            self.assertEqual(oracal.get("line_total"), 0.0)
        op = _op_by_code(out, "vinyl_application")
        self.assertIsNotNone(op)
        self.assertEqual(op.get("skipped"), True)
        self.assertEqual(op.get("line_total"), 0.0)

    def test_mounting_template_enabled_includes_sablon(self) -> None:
        out = self._build(BASE_QUOTE_INPUT)
        mat = _mat_by_code(out, "MAT-SABLON-MONTAJ")
        op = _op_by_code(out, "mounting_template_cnc_cut")
        self.assertIsNotNone(mat)
        self.assertAlmostEqual(mat["line_total"], 17.28)
        self.assertIsNotNone(op)
        self.assertAlmostEqual(op["line_total"], 27.0)

    def test_mounting_template_disabled_excludes_sablon(self) -> None:
        qi = dict(BASE_QUOTE_INPUT)
        qi["mounting_template_enabled"] = False
        out = self._build(qi)
        mat = _mat_by_code(out, "MAT-SABLON-MONTAJ")
        op = _op_by_code(out, "mounting_template_cnc_cut")
        self.assertIsNotNone(mat)
        self.assertEqual(mat.get("skipped"), True)
        self.assertEqual(mat.get("line_total"), 0.0)
        self.assertIsNotNone(op)
        self.assertEqual(op.get("skipped"), True)
        self.assertEqual(op.get("line_total"), 0.0)

    def test_mounting_template_paper_uses_hartie_not_forex(self) -> None:
        qi = dict(BASE_QUOTE_INPUT)
        qi["mounting_template_material_type"] = "paper"
        out = self._build(qi)
        paper = _mat_by_code(out, "MAT-SABLON-HARTIE")
        forex = _mat_by_code(out, "MAT-SABLON-MONTAJ")
        op = _op_by_code(out, "mounting_template_cnc_cut")
        self.assertIsNotNone(paper)
        self.assertAlmostEqual(paper["line_total"], 14.40)
        self.assertIsNotNone(forex)
        self.assertEqual(forex.get("skipped"), True)
        self.assertEqual(forex.get("line_total"), 0.0)
        self.assertIsNotNone(op)
        self.assertEqual(op.get("skipped"), True)

    def test_mounting_bar_formula_auto_from_width(self) -> None:
        res = resolve_formula(
            "mounting_bar_total_length",
            {"default_bar_count": 2},
            {"width_mm": 4800},
        )
        self.assertTrue(res.resolved)
        self.assertAlmostEqual(res.value, 9.6)
        self.assertFalse(res.breakdown.get("override_used"))

    def test_mounting_bar_formula_override(self) -> None:
        res = resolve_formula(
            "mounting_bar_total_length",
            {},
            {"width_mm": 4800, "mounting_bar_length_m": 5},
        )
        self.assertTrue(res.resolved)
        self.assertAlmostEqual(res.value, 5.0)
        self.assertTrue(res.breakdown.get("override_used"))

    def test_steel_bars_auto_width_9_6m(self) -> None:
        out = self._build(
            {
                **BASE_QUOTE_INPUT,
                "mounting_system": "steel_bars",
                "mounting_bar_profile": "30x30x1.5",
            }
        )
        mat = _mat_by_code(out, "MAT-PREMOUNT-BAR-STEEL")
        self.assertIsNotNone(mat)
        self.assertAlmostEqual(mat["quantity"], 9.6)
        self.assertAlmostEqual(mat["line_total"], 19.20)

    def test_aluminum_bars_auto_width_9_6m(self) -> None:
        out = self._build(
            {
                **BASE_QUOTE_INPUT,
                "mounting_system": "aluminum_bars",
                "mounting_bar_profile": "30x30x1.5",
            }
        )
        mat = _mat_by_code(out, "MAT-PREMOUNT-BAR-ALUMINUM")
        self.assertIsNotNone(mat)
        self.assertAlmostEqual(mat["quantity"], 9.6)
        self.assertAlmostEqual(mat["line_total"], 33.60)

    def test_steel_bars_override_5m(self) -> None:
        out = self._build(
            {
                **BASE_QUOTE_INPUT,
                "mounting_system": "steel_bars",
                "mounting_bar_profile": "30x30x1.5",
                "mounting_bar_length_m": 5,
            }
        )
        mat = _mat_by_code(out, "MAT-PREMOUNT-BAR-STEEL")
        self.assertIsNotNone(mat)
        self.assertAlmostEqual(mat["line_total"], 10.0)

    def test_aluminum_bars_override_5m(self) -> None:
        out = self._build(
            {
                **BASE_QUOTE_INPUT,
                "mounting_system": "aluminum_bars",
                "mounting_bar_profile": "30x30x1.5",
                "mounting_bar_length_m": 5,
            }
        )
        mat = _mat_by_code(out, "MAT-PREMOUNT-BAR-ALUMINUM")
        self.assertIsNotNone(mat)
        self.assertAlmostEqual(mat["line_total"], 17.5)

    def test_steel_bars_count_3_width_4800(self) -> None:
        out = self._build(
            {
                **BASE_QUOTE_INPUT,
                "mounting_system": "steel_bars",
                "mounting_bar_profile": "30x30x1.5",
                "mounting_bar_count": 3,
            }
        )
        mat = _mat_by_code(out, "MAT-PREMOUNT-BAR-STEEL")
        self.assertAlmostEqual(mat["quantity"], 14.4)
        self.assertAlmostEqual(mat["line_total"], 28.80)

    def test_steel_bars_missing_width_and_override_blocks(self) -> None:
        qi = dict(BASE_QUOTE_INPUT)
        qi["mounting_system"] = "steel_bars"
        qi["mounting_bar_profile"] = "30x30x1.5"
        del qi["width_mm"]
        out = self._build(qi)
        kinds = {e.get("kind") for e in out.get("errors") or []}
        self.assertIn(ERR_NEEDS_QUOTE_INPUT, kinds)

    def test_unknown_steel_profile_skipped_no_cost(self) -> None:
        out = self._build(
            {
                **BASE_QUOTE_INPUT,
                "mounting_system": "steel_bars",
                "mounting_bar_profile": "40x40x2",
            }
        )
        mat = _mat_by_code(out, "MAT-PREMOUNT-BAR-STEEL")
        self.assertIsNotNone(mat)
        self.assertEqual(mat.get("skipped"), True)
        self.assertEqual(mat.get("line_total"), 0.0)
        warnings = collect_volumetric_captured_unpriced_warnings(
            "TPL-VOLUMETRIC-LETTERS",
            {
                "mounting_system": "steel_bars",
                "mounting_bar_profile": "40x40x2",
            },
        )
        self.assertEqual(
            warnings,
            [f"{WARNING_MOUNTING_BAR_PROFILE_PRICE_MISSING}:steel:40x40x2"],
        )

    def test_acm_panel_separate_template_warning(self) -> None:
        warnings = collect_volumetric_captured_unpriced_warnings(
            "TPL-VOLUMETRIC-LETTERS",
            {**BASE_QUOTE_INPUT, "mounting_system": "acm_panel"},
        )
        self.assertEqual(
            warnings,
            [f"{WARNING_ACM_SEPARATE_TEMPLATE}:mounting_system=acm_panel"],
        )

    def test_steel_bars_mounting_labor_warning(self) -> None:
        warnings = collect_volumetric_captured_unpriced_warnings(
            "TPL-VOLUMETRIC-LETTERS",
            {
                **BASE_QUOTE_INPUT,
                "mounting_system": "steel_bars",
                "mounting_bar_profile": "30x30x1.5",
            },
        )
        self.assertEqual(
            warnings,
            [f"{WARNING_MOUNTING_LABOR_NOT_PRICED}:mounting_system=steel_bars"],
        )


class TestVolumetricFinishMountingIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.db_fixture = IsolatedDBFixture(prefix="volumetric_finish_mount_")
        cls.db_fixture.setup()
        _run(cls._seed())

    @classmethod
    def tearDownClass(cls) -> None:
        cls.db_fixture.teardown()

    @classmethod
    async def _seed(cls) -> None:
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
            ("MAT-ORACAL-651", "mp"),
            ("MAT-VINYL-PRINT", "mp"),
            ("MAT-VINYL-PRINT-LAMINATED", "mp"),
            ("MAT-PREMOUNT-BAR-STEEL", "ml"),
            ("MAT-PREMOUNT-BAR-ALUMINUM", "ml"),
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

    def _build_from_registry(self, quote_input: dict) -> dict:
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
                    quote_input,
                    template_code="TPL-VOLUMETRIC-LETTERS",
                )
                return build_execution_layers_from_components(
                    _template_payload(),
                    ComponentCostContext(
                        material_rates=resolved,
                        workcenter_rates=wc,
                        base_currency="EUR",
                        quantity=1,
                        quote_input=dict(quote_input),
                    ),
                )

        return _run(_go())

    def test_baseline_direct_wall_template_enabled_no_blockers(self) -> None:
        out = self._build_from_registry(BASE_QUOTE_INPUT)
        self.assertFalse(
            [e for e in out.get("errors") or [] if e.get("kind") == ERR_NEEDS_QUOTE_INPUT]
        )
        self.assertIsNotNone(_mat_by_code(out, "MAT-SABLON-MONTAJ"))
        self.assertAlmostEqual(
            _mat_by_code(out, "MAT-SABLON-MONTAJ")["line_total"],
            17.28,
        )


if __name__ == "__main__":
    unittest.main()
