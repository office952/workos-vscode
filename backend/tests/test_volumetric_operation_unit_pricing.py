"""TPL-VOLUMETRIC-LETTERS â€” owner-defined unit-based operation pricing."""

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
    ERR_WORKCENTER_LINEAR_METER_QUANTITY_MISSING,
    ERR_WORKCENTER_PIECE_QUANTITY_MISSING,
    ERR_WORKCENTER_AREA_QUANTITY_MISSING,
    ERR_WORKCENTER_RATE_MISSING,
    ComponentCostContext,
    build_execution_layers_from_components,
)
from services.formula_handlers import resolve_formula  # noqa: E402
from services.pricing_registry_service import PricingRegistryService  # noqa: E402
from services.template_operation_policy import (  # noqa: E402
    is_quote_priced_operation,
    should_skip_operation_costing,
)
from services.volumetric_material_rate_resolver import (  # noqa: E402
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


def _workcenter_rates_fixture() -> dict:
    return {
        "PREPRESS": {"rate_basis": "per_piece", "rate_per_linear_meter": 2.0},
        "CNC_ROUTER": {"rate_basis": "per_linear_meter", "rate_per_linear_meter": 1.5},
        "LED_ASSEMBLY": {"rate_basis": "per_piece", "rate_per_linear_meter": 0.05},
        "ELECTRICAL_WIRING": {"rate_basis": "per_piece", "rate_per_linear_meter": 2.0},
        "PAINTING": {"rate_basis": "per_linear_meter", "rate_per_linear_meter": 4.0},
        "PACKAGING": {"rate_basis": "per_square_meter", "rate_per_linear_meter": 10.0},
        "VINYL_APPLICATION": {"rate_basis": "per_square_meter", "rate_per_linear_meter": 3.0},
        "RETURN_PROFILE_MACHINE_FORMING": {
            "rate_basis": "per_linear_meter",
            "rate_per_linear_meter": 5.0,
        },
        "RETURN_PROFILE_FACE_BONDING": {
            "rate_basis": "per_linear_meter",
            "rate_per_linear_meter": 5.0,
        },
    }


class TestUnitPricingFormulas(unittest.TestCase):
    def test_perimeter_pass_plexi_face_2_passes(self) -> None:
        res = resolve_formula(
            "perimeter_pass_linear_meter",
            {"pass_count": 2},
            {"letter_perimeter_m": 18.0},
        )
        self.assertTrue(res.resolved)
        self.assertAlmostEqual(res.value, 36.0)

    def test_perimeter_pass_forex_back_static_5_passes(self) -> None:
        res = resolve_formula(
            "perimeter_pass_linear_meter",
            {"pass_count": 5},
            {"letter_perimeter_m": 18.0},
        )
        self.assertTrue(res.resolved)
        self.assertAlmostEqual(res.value, 90.0)

    def test_perimeter_pass_forex_back_3_passes_default_no_bevel(self) -> None:
        res = resolve_formula(
            "perimeter_pass_linear_meter",
            {
                "base_pass_count": 3,
                "bevel_pass_count": 2,
                "bevel_quote_input_key": "back_bevel_enabled",
            },
            {"letter_perimeter_m": 18.0},
        )
        self.assertTrue(res.resolved)
        self.assertAlmostEqual(res.value, 54.0)
        self.assertTrue(res.breakdown.get("default_applied"))
        self.assertFalse(res.breakdown.get("back_bevel_enabled"))

    def test_perimeter_pass_forex_back_5_passes_with_bevel(self) -> None:
        res = resolve_formula(
            "perimeter_pass_linear_meter",
            {
                "base_pass_count": 3,
                "bevel_pass_count": 2,
                "bevel_quote_input_key": "back_bevel_enabled",
            },
            {"letter_perimeter_m": 18.0, "back_bevel_enabled": True},
        )
        self.assertTrue(res.resolved)
        self.assertAlmostEqual(res.value, 90.0)
        self.assertFalse(res.breakdown.get("default_applied"))
        self.assertTrue(res.breakdown.get("back_bevel_enabled"))

    def test_led_module_count_from_quote_input(self) -> None:
        res = resolve_formula("led_module_count", {}, {"led_module_count": 180})
        self.assertTrue(res.resolved)
        self.assertEqual(res.value, 180.0)


class TestTemplateOperationDeScope(unittest.TestCase):
    def test_assembly_not_quote_priced(self) -> None:
        for comp in _volumetric_letters_components():
            for op in comp.get("operations") or []:
                if op.get("code") == "assembly_letters":
                    self.assertFalse(is_quote_priced_operation(op))
                    self.assertTrue(should_skip_operation_costing(op))
                    return
        self.fail("assembly_letters not found")

    def test_no_laser_cutting_workcenter_in_volumetric_seed(self) -> None:
        workcenters = {
            op.get("workcenter")
            for comp in _volumetric_letters_components()
            for op in comp.get("operations") or []
        }
        self.assertNotIn("LASER_CUTTING", workcenters)

    def test_back_cut_uses_cnc_router(self) -> None:
        for comp in _volumetric_letters_components():
            for op in comp.get("operations") or []:
                if op.get("code") == "back_cut":
                    self.assertEqual(op.get("workcenter"), "CNC_ROUTER")
                    self.assertEqual(op.get("formula_id"), "perimeter_pass_linear_meter")
                    self.assertEqual(
                        (op.get("formula_params") or {}).get("gate"),
                        {"backing_present": True},
                    )
                    return
        self.fail("back_cut not found")


class TestUnitPricingCostEngine(unittest.TestCase):
    def _build(self, quote_input: dict | None = None) -> dict:
        ctx = ComponentCostContext(
            material_rates={},
            workcenter_rates=_workcenter_rates_fixture(),
            quantity=1,
            quote_input=dict(quote_input or FULL_QUOTE_INPUT),
        )
        return build_execution_layers_from_components(_template_payload(), ctx)

    def test_prepess_9_letters_18_eur(self) -> None:
        op = _op_by_code(self._build(), "vector_prep")
        self.assertIsNotNone(op)
        self.assertAlmostEqual(op["line_total"], 18.0)
        self.assertEqual(op["rate_basis"], "per_piece")

    def test_cnc_face_54_eur(self) -> None:
        op = _op_by_code(self._build(), "face_cnc_cut")
        self.assertIsNotNone(op)
        self.assertAlmostEqual(op["line_total"], 54.0)
        self.assertAlmostEqual(op["linear_meters"], 36.0)

    def test_cnc_back_81_eur_default_no_bevel(self) -> None:
        op = _op_by_code(self._build(), "back_cut")
        self.assertIsNotNone(op)
        self.assertAlmostEqual(op["line_total"], 81.0)
        self.assertAlmostEqual(op["linear_meters"], 54.0)

    def test_cnc_back_skipped_when_backing_present_false(self) -> None:
        op = _op_by_code(
            self._build(
                {
                    **FULL_QUOTE_INPUT,
                    "backing_present": False,
                    "intake_source": "intake_v4",
                }
            ),
            "back_cut",
        )
        self.assertIsNotNone(op)
        self.assertTrue(op.get("skipped"))
        self.assertEqual(op.get("skip_reason"), "gate:backing_absent")
        self.assertAlmostEqual(op["line_total"], 0.0)

    def test_cnc_back_iv4_confirmed_three_passes(self) -> None:
        qi = {
            **FULL_QUOTE_INPUT,
            "intake_source": "intake_v4",
            "backing_present": True,
            "back_bevel_enabled": False,
            "cnc_cutting_perimeter_ml": 12.725,
            "letter_perimeter_m": 12.725,
        }
        op = _op_by_code(self._build(qi), "back_cut")
        self.assertIsNotNone(op)
        self.assertAlmostEqual(op["line_total"], 57.2625, places=2)
        self.assertAlmostEqual(op["linear_meters"], 38.175, places=2)

    def test_cnc_back_iv4_confirmed_bevel_five_passes(self) -> None:
        qi = {
            **FULL_QUOTE_INPUT,
            "intake_source": "intake_v4",
            "backing_present": True,
            "back_bevel_enabled": True,
            "cnc_cutting_perimeter_ml": 12.725,
            "letter_perimeter_m": 12.725,
        }
        op = _op_by_code(self._build(qi), "back_cut")
        self.assertIsNotNone(op)
        self.assertAlmostEqual(op["line_total"], 95.4375, places=2)
        self.assertAlmostEqual(op["linear_meters"], 63.625, places=2)

    def test_cnc_back_135_eur_with_back_bevel_enabled(self) -> None:
        op = _op_by_code(
            self._build({**FULL_QUOTE_INPUT, "back_bevel_enabled": True}),
            "back_cut",
        )
        self.assertIsNotNone(op)
        self.assertAlmostEqual(op["line_total"], 135.0)
        self.assertAlmostEqual(op["linear_meters"], 90.0)

    def test_cnc_back_81_eur_when_back_bevel_explicitly_false(self) -> None:
        op = _op_by_code(
            self._build({**FULL_QUOTE_INPUT, "back_bevel_enabled": False}),
            "back_cut",
        )
        self.assertIsNotNone(op)
        self.assertAlmostEqual(op["line_total"], 81.0)

    def test_led_assembly_9_eur(self) -> None:
        op = _op_by_code(self._build(), "led_install_letters")
        self.assertIsNotNone(op)
        self.assertAlmostEqual(op["line_total"], 9.0)
        self.assertEqual(op["rate_basis"], "per_piece")

    def test_electrical_18_eur(self) -> None:
        op = _op_by_code(self._build(), "electrical_letters")
        self.assertIsNotNone(op)
        self.assertAlmostEqual(op["line_total"], 18.0)

    def test_painting_72_eur_when_volume_finish_is_painted(self) -> None:
        op = _op_by_code(
            self._build({**FULL_QUOTE_INPUT, "volume_finish": "paint_after_face_miter_bond"}),
            "painting",
        )
        self.assertIsNotNone(op)
        self.assertAlmostEqual(op["line_total"], 72.0)

    def test_packaging_28_8_eur(self) -> None:
        op = _op_by_code(self._build(), "packaging_letters")
        self.assertIsNotNone(op)
        self.assertAlmostEqual(op["line_total"], 28.8)
        self.assertEqual(op["rate_basis"], "per_square_meter")

    def test_no_laser_blocker(self) -> None:
        out = self._build()
        laser_errors = [
            e
            for e in out.get("errors") or []
            if "LASER_CUTTING" in str(e.get("detail") or "")
        ]
        self.assertEqual(laser_errors, [])

    def test_no_assembly_blocker(self) -> None:
        out = self._build()
        assembly_errors = [
            e
            for e in out.get("errors") or []
            if e.get("kind") == ERR_WORKCENTER_RATE_MISSING
            and "workcenter='ASSEMBLY'" in str(e.get("detail") or "")
        ]
        self.assertEqual(assembly_errors, [])

    def test_qc_no_blocker_no_cost(self) -> None:
        out = self._build()
        qc = _op_by_code(out, "qc_letters")
        self.assertIsNotNone(qc)
        self.assertEqual(qc.get("line_total"), 0.0)
        qc_errors = [
            e
            for e in out.get("errors") or []
            if "QC_INSPECTION" in str(e.get("detail") or "")
        ]
        self.assertEqual(qc_errors, [])

    def test_missing_letter_perimeter_blocks_cnc_and_painting(self) -> None:
        qi = dict(FULL_QUOTE_INPUT)
        del qi["letter_perimeter_m"]
        out = self._build(qi)
        kinds = {e.get("kind") for e in out.get("errors") or []}
        self.assertIn(ERR_NEEDS_QUOTE_INPUT, kinds)
        perimeter_errors = [
            e
            for e in out.get("errors") or []
            if "letter_perimeter_m" in str(e.get("detail") or "")
        ]
        self.assertTrue(perimeter_errors)

    def test_missing_letter_count_blocks_prepess_and_electrical(self) -> None:
        qi = dict(FULL_QUOTE_INPUT)
        del qi["letter_count"]
        out = self._build(qi)
        kinds = {e.get("kind") for e in out.get("errors") or []}
        self.assertIn(ERR_NEEDS_QUOTE_INPUT, kinds)
        count_errors = [
            e
            for e in out.get("errors") or []
            if "letter_count" in str(e.get("detail") or "")
        ]
        self.assertTrue(count_errors)

    def test_missing_led_module_count_blocks_led_assembly(self) -> None:
        qi = dict(FULL_QUOTE_INPUT)
        del qi["led_module_count"]
        out = self._build(qi)
        kinds = {e.get("kind") for e in out.get("errors") or []}
        self.assertIn(ERR_NEEDS_QUOTE_INPUT, kinds)
        led_errors = [
            e
            for e in out.get("errors") or []
            if "led_module_count" in str(e.get("detail") or "")
        ]
        self.assertTrue(led_errors)

    def test_missing_letter_face_area_blocks_packaging(self) -> None:
        qi = dict(FULL_QUOTE_INPUT)
        del qi["letter_face_area_m2"]
        out = self._build(qi)
        kinds = {e.get("kind") for e in out.get("errors") or []}
        self.assertIn(ERR_NEEDS_QUOTE_INPUT, kinds)
        area_errors = [
            e
            for e in out.get("errors") or []
            if "letter_face_area_m2" in str(e.get("detail") or "")
        ]
        self.assertTrue(area_errors)

    def test_missing_piece_quantity_when_formula_static(self) -> None:
        """Static per_piece ops surface quantity missing without formula pre-check."""
        tpl = _template_payload()
        components = json.loads(tpl["components_json"])
        for comp in components:
            for op in comp.get("operations") or []:
                if op.get("code") == "vector_prep":
                    op["calculation_type"] = "static"
                    op.pop("formula_id", None)
        tpl["components_json"] = json.dumps(components)
        ctx = ComponentCostContext(
            material_rates={},
            workcenter_rates=_workcenter_rates_fixture(),
            quantity=1,
            quote_input=dict(FULL_QUOTE_INPUT),
        )
        out = build_execution_layers_from_components(tpl, ctx)
        kinds = {e.get("kind") for e in out.get("errors") or []}
        self.assertIn(ERR_WORKCENTER_PIECE_QUANTITY_MISSING, kinds)


class TestVolumetricUnitPricingIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.db_fixture = IsolatedDBFixture(prefix="volumetric_unit_pricing_")
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

    def test_pricing_registry_has_owner_confirmed_operation_rates(self) -> None:
        from core.database import db_manager

        async def _go():
            async with db_manager.async_session_maker() as session:
                svc = PricingRegistryService(session)
                reg = await svc.build_registry(
                    template_filter="TPL-VOLUMETRIC-LETTERS"
                )
                return reg

        reg = _run(_go())
        codes = {r.get("pricing_code") for r in reg.get("items") or []}
        for wc in (
            "PREPRESS",
            "CNC_ROUTER",
            "LED_ASSEMBLY",
            "ELECTRICAL_WIRING",
            "PAINTING",
            "PACKAGING",
            "FACE_VINYL_APPLICATION_LABOR",
        ):
            self.assertIn(wc, codes)
        self.assertNotIn("LASER_CUTTING", codes)
        self.assertNotIn("ASSEMBLY", codes)
        self.assertNotIn("QC_INSPECTION", codes)

    def test_product_001_operation_line_totals(self) -> None:
        from core.database import db_manager
        from services.inventory_materials_admin_service import list_inventory_materials_admin
        from services.workcenter_rates_service import load_workcenter_rate_dict

        async def _go():
            product_quote_input = {
                **FULL_QUOTE_INPUT,
                "volume_finish": "paint_after_face_miter_bond",
            }
            async with db_manager.async_session_maker() as session:
                registry = await list_inventory_materials_admin(session)
                rates = {}
                for row in registry:
                    if str(row.get("status")) == "active" and row.get("unit_cost"):
                        rates[row["code"]] = float(row["unit_cost"])
                wc = await load_workcenter_rate_dict(session)
                resolved, _ = resolve_volumetric_material_rates_with_trace(
                    rates,
                    product_quote_input,
                    template_code="TPL-VOLUMETRIC-LETTERS",
                )
                return build_execution_layers_from_components(
                    _template_payload(),
                    ComponentCostContext(
                        material_rates=resolved,
                        workcenter_rates=wc,
                        base_currency="EUR",
                        quantity=1,
                        quote_input=dict(product_quote_input),
                    ),
                )

        out = _run(_go())
        expectations = {
            "vector_prep": 18.0,
            "face_cnc_cut": 54.0,
            "back_cut": 81.0,
            "side_forming": 90.0,
            "return_face_bonding": 90.0,
            "led_install_letters": 9.0,
            "electrical_letters": 18.0,
            "painting": 72.0,
            "packaging_letters": 28.8,
            "mounting_template_cnc_cut": 27.0,
        }
        for code, expected in expectations.items():
            op = _op_by_code(out, code)
            self.assertIsNotNone(op, f"missing op {code}")
            self.assertAlmostEqual(
                op["line_total"],
                expected,
                places=2,
                msg=f"{code} expected {expected}",
            )
