"""TPL-VOLUMETRIC-LETTERS — illumination gating for LED/electrical cost and plan."""

from __future__ import annotations

import json
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from data_models.product_contracts import (  # noqa: E402
    CostResult,
    CostValidation,
    ProductDefinition,
    ProductDimensions,
    ProductLayer,
    ProductMaterial,
    ProductProcess,
    QuoteCalculationSnapshot,
    QuotePrice,
    QuotePricing,
)
from seeds.seed_build4_templates import _volumetric_letters_components  # noqa: E402
from services.cost_engine_service import (  # noqa: E402
    ComponentCostContext,
    build_execution_layers_from_components,
)
from services.execution_plan_service import ExecutionPlanService  # noqa: E402
from services.order_snapshot_service import OrderSnapshotService  # noqa: E402
from services.quote_input_line_gate import should_skip_quote_input_gated_line  # noqa: E402
from services.volumetric_quote_input_policy import is_illumination_enabled  # noqa: E402


def _template_payload() -> dict:
    return {
        "template_code": "TPL-VOLUMETRIC-LETTERS",
        "components_json": json.dumps(_volumetric_letters_components()),
        "operations_json": "[]",
        "required_materials_json": "[]",
    }


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
    "face_finish_type": "none",
    "mounting_system": "direct_wall",
    "mounting_template_enabled": True,
    "back_bevel_enabled": False,
}

LEX_LIKE_QUOTE_INPUT = {
    **BASE_QUOTE_INPUT,
    "illumination_type": "none",
    "lighting_system_type": "none",
    "mounting_template_enabled": False,
    "volume_finish": "paint_after_face_miter_bond",
    "paint_tube_count": 3,
}

MATERIAL_RATES = {
    "MAT-ACP-FATA-LITERE": 16.0,
    "MAT-SPATE-PVC-LITERE": 16.0,
    "MAT-LED-MODULE": 0.5,
    "MAT-LED-PSU-12V": 16.0,
    "MAT-LED-PSU-12V-100W": 16.0,
    "MAT-SABLON-MONTAJ": 6.0,
    "MAT-PROFIL-LATERAL-LITERE-60MM": 3.0,
    "MAT-CONSUMABILE-MONTAJ": 5.0,
}


def _workcenter_rates_fixture() -> dict:
    return {
        "PREPRESS": {"rate_basis": "per_piece", "rate_per_linear_meter": 2.0},
        "CNC_ROUTER": {"rate_basis": "per_linear_meter", "rate_per_linear_meter": 1.5},
        "LED_ASSEMBLY": {"rate_basis": "per_piece", "rate_per_linear_meter": 0.05},
        "ELECTRICAL_WIRING": {"rate_basis": "per_piece", "rate_per_linear_meter": 2.0},
        "PAINTING": {"rate_basis": "per_linear_meter", "rate_per_linear_meter": 4.0},
        "PACKAGING": {"rate_basis": "per_square_meter", "rate_per_linear_meter": 10.0},
        "RETURN_PROFILE_MACHINE_FORMING": {
            "rate_basis": "per_linear_meter",
            "rate_per_linear_meter": 5.0,
        },
        "RETURN_PROFILE_FACE_BONDING": {
            "rate_basis": "per_linear_meter",
            "rate_per_linear_meter": 5.0,
        },
    }


def _build(quote_input: dict) -> dict:
    ctx = ComponentCostContext(
        material_rates=dict(MATERIAL_RATES),
        workcenter_rates=_workcenter_rates_fixture(),
        quantity=1,
        quote_input=quote_input,
    )
    return build_execution_layers_from_components(_template_payload(), ctx)


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


def _active_line_total(line: dict | None) -> float:
    if line is None:
        return 0.0
    if line.get("skipped"):
        return 0.0
    return float(line.get("line_total") or 0.0)


class _FakeOrderRow:
    def __init__(self, order_id: int, code: str, snapshot_dict: dict):
        self.id = order_id
        self.code = code
        self.snapshot_version = 1
        self.snapshot_line_items = json.dumps(snapshot_dict)


class TestIlluminationPolicyHelper(unittest.TestCase):
    def test_none_disables_even_with_led_module_count(self) -> None:
        qi = {**BASE_QUOTE_INPUT, "illumination_type": "none", "lighting_system_type": "none"}
        self.assertFalse(is_illumination_enabled(qi))

    def test_non_illuminated_disables(self) -> None:
        self.assertFalse(
            is_illumination_enabled({**BASE_QUOTE_INPUT, "illumination_type": "non_illuminated"})
        )

    def test_lighting_none_disables(self) -> None:
        self.assertFalse(
            is_illumination_enabled(
                {**BASE_QUOTE_INPUT, "illumination_type": "frontlit", "lighting_system_type": "none"}
            )
        )

    def test_frontlit_and_led_modules_enables(self) -> None:
        qi = {
            **BASE_QUOTE_INPUT,
            "illumination_type": "frontlit",
            "lighting_system_type": "led_modules",
        }
        self.assertTrue(is_illumination_enabled(qi))

    def test_legacy_missing_fields_remains_enabled(self) -> None:
        self.assertTrue(is_illumination_enabled(BASE_QUOTE_INPUT))


class TestIlluminationNoneCostGate(unittest.TestCase):
    def test_led_ops_and_materials_skipped_with_illumination_none(self) -> None:
        out = _build(
            {
                **BASE_QUOTE_INPUT,
                "illumination_type": "none",
                "lighting_system_type": "none",
            }
        )
        led_op = _op_by_code(out, "led_install_letters")
        electrical_op = _op_by_code(out, "electrical_letters")
        led_mat = _mat_by_code(out, "MAT-LED-MODULE")
        psu_mat = _mat_by_code(out, "MAT-LED-PSU-12V")

        self.assertEqual(led_op.get("skipped"), True)
        self.assertEqual(led_op.get("skip_reason"), "gate:illumination_disabled")
        self.assertEqual(electrical_op.get("skipped"), True)
        self.assertEqual(led_mat.get("skipped"), True)
        self.assertEqual(psu_mat.get("skipped"), True)
        self.assertEqual(_active_line_total(led_op), 0.0)
        self.assertEqual(_active_line_total(electrical_op), 0.0)
        self.assertEqual(_active_line_total(led_mat), 0.0)
        self.assertEqual(_active_line_total(psu_mat), 0.0)

    def test_face_cnc_remains_active_when_illumination_none(self) -> None:
        out = _build(
            {
                **BASE_QUOTE_INPUT,
                "illumination_type": "none",
                "lighting_system_type": "none",
            }
        )
        face = _op_by_code(out, "face_cnc_cut")
        self.assertIsNotNone(face)
        self.assertGreater(_active_line_total(face), 0.0)


class TestIlluminatedRegression(unittest.TestCase):
    def test_led_ops_and_materials_active_when_illuminated(self) -> None:
        out = _build(
            {
                **BASE_QUOTE_INPUT,
                "illumination_type": "frontlit",
                "lighting_system_type": "led_modules",
            }
        )
        led_op = _op_by_code(out, "led_install_letters")
        electrical_op = _op_by_code(out, "electrical_letters")
        led_mat = _mat_by_code(out, "MAT-LED-MODULE")
        psu_mat = _mat_by_code(out, "MAT-LED-PSU-12V")

        self.assertNotEqual(led_op.get("skipped"), True)
        self.assertNotEqual(electrical_op.get("skipped"), True)
        self.assertNotEqual(led_mat.get("skipped"), True)
        self.assertNotEqual(psu_mat.get("skipped"), True)
        self.assertGreater(_active_line_total(led_op), 0.0)
        self.assertGreater(_active_line_total(electrical_op), 0.0)
        self.assertGreater(_active_line_total(led_mat), 0.0)
        self.assertGreater(_active_line_total(psu_mat), 0.0)


class TestConditionalMaterialGate(unittest.TestCase):
    def test_illumination_enabled_conditional_skips_when_disabled(self) -> None:
        entry = {
            "formula_params": {"conditional": "illumination_enabled"},
        }
        reason = should_skip_quote_input_gated_line(
            entry,
            {**BASE_QUOTE_INPUT, "illumination_type": "none"},
        )
        self.assertEqual(reason, "gate:illumination_disabled")

    def test_illumination_enabled_conditional_active_when_enabled(self) -> None:
        entry = {
            "formula_params": {"conditional": "illumination_enabled"},
        }
        reason = should_skip_quote_input_gated_line(
            entry,
            {**BASE_QUOTE_INPUT, "illumination_type": "backlit", "lighting_system_type": "led_modules"},
        )
        self.assertIsNone(reason)


class TestLexLikePlanWithoutLedTasks(unittest.TestCase):
    def test_plan_excludes_led_and_electrical_when_illumination_none(self) -> None:
        out = _build(LEX_LIKE_QUOTE_INPUT)
        component_breakdown = [
            {
                "component_id": comp.get("component_id"),
                "operations_detail": comp.get("operations_detail") or [],
            }
            for comp in out.get("components") or []
        ]

        layers = [
            ProductLayer(
                layer_id="layer_1",
                layer_type="structure",
                material=ProductMaterial(
                    material_id="MAT-ACP-FATA-LITERE",
                    name="Face",
                    unit="sqm",
                ),
                thickness_mm=3,
                finish="",
                components=[],
                processes=[
                    ProductProcess(
                        process_id=code,
                        type=legacy,
                        machine_type="WC",
                        estimated_time_minutes=0.0,
                    )
                    for code, legacy in [
                        ("vector_prep", "prepress"),
                        ("face_cnc_cut", "cnc"),
                        ("back_cut", "cnc"),
                        ("led_install_letters", "assembly"),
                        ("electrical_letters", "wiring"),
                        ("painting", "painting"),
                        ("assembly_letters", "assembly"),
                        ("qc_letters", "qc_inspection"),
                    ]
                ],
            )
        ]
        snap = QuoteCalculationSnapshot(
            product_definition=ProductDefinition(
                product_id="TPL-VOLUMETRIC-LETTERS",
                product_type="Litere volumetrice",
                quantity=1,
                dimensions=ProductDimensions(width_mm=4800, height_mm=600, depth_mm=60),
                layers=layers,
            ),
            cost_result=CostResult(
                is_valid=True,
                currency="RON",
                materials_cost=400.0,
                labour_cost=300.0,
                machine_cost=200.0,
                external_cost=0.0,
                overhead_cost=50.0,
                total_cost=950.0,
                estimated_time_minutes=75.0,
                breakdown=[],
                validation=CostValidation(),
            ),
            pricing=QuotePricing(margin_pct=20, discount_pct=0, vat_pct=19),
            price=QuotePrice(net=1000, gross=1190, final=1190),
            status="priced",
        )
        order = OrderSnapshotService().create_from_quote(
            snap,
            component_breakdown=component_breakdown,
        )
        row = _FakeOrderRow(501, "ORD-LEX-LIGHT-GATE", order.to_dict())
        plan = ExecutionPlanService().from_order(row)

        process_ids = {t.process_id for t in plan.tasks}
        process_types = {t.process_type for t in plan.tasks}
        self.assertNotIn("led_install_letters", process_ids)
        self.assertNotIn("electrical_letters", process_ids)
        self.assertNotIn("led_wiring", process_types)
        self.assertIn("face_cnc_cut", process_ids)


if __name__ == "__main__":
    unittest.main()
