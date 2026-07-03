"""BUILD_INTAKE_V4_CNC_ROUTER_PASSES_AND_BEVEL_COSTING_AUDIT — pass policy + quote input perimeter."""

from __future__ import annotations

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from seeds.seed_build4_templates import (  # noqa: E402
    _volumetric_letters_components,
)
from services.cost_engine_service import (  # noqa: E402
    ComponentCostContext,
    build_execution_layers_from_components,
)
from services.intake_v4_cnc_router_pass_policy_service import (
    CNC_PERIMETER_QUOTE_INPUT_KEY,
    DEFAULT_CNC_RATE_EUR_PER_ML_PASS,
    build_cnc_operation_estimate_preview,
    estimate_cnc_router_cost_eur,
    face_plexi_cnc_passes,
    forex_backing_cnc_passes,
    passes_for_depth_mm,
    resolve_cnc_cutting_perimeter_ml,
)
from services.intake_v4_pricing_input_service import _patch_quote_input_from_v4_geometry
from schemas.intake_v4 import IntakeV4ProductBinding, IntakeV4WorkspacePayload


PERIM_ML = 12.725


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


def _build_iv4_quote(quote_input: dict) -> dict:
    ctx = ComponentCostContext(
        material_rates={},
        workcenter_rates={"CNC_ROUTER": {"rate_basis": "per_linear_meter", "rate_per_linear_meter": 1.5}},
        quantity=1,
        quote_input=quote_input,
    )
    return build_execution_layers_from_components(_template_payload(), ctx)


class TestCncPassPolicy:
    def test_face_plexi_with_bevel_two_passes(self):
        assert face_plexi_cnc_passes(face_bevel_enabled=True)["total_passes"] == 2

    def test_face_plexi_without_bevel_one_pass(self):
        assert face_plexi_cnc_passes(face_bevel_enabled=False)["total_passes"] == 1

    def test_forex_10mm_no_bevel_three_passes(self):
        row = forex_backing_cnc_passes(back_bevel_enabled=False)
        assert row["cut_passes"] == 3
        assert row["bevel_passes"] == 0
        assert row["total_passes"] == 3

    def test_forex_10mm_bevel_7mm_five_passes(self):
        row = forex_backing_cnc_passes(back_bevel_enabled=True)
        assert row["cut_passes"] == 3
        assert row["bevel_passes"] == 2
        assert row["total_passes"] == 5

    def test_passes_for_depth_ceil_rule(self):
        assert passes_for_depth_mm(depth_mm=10.0) == 3
        assert passes_for_depth_mm(depth_mm=7.0) == 2
        assert passes_for_depth_mm(depth_mm=3.5) == 1

    def test_cnc_cutting_perimeter_prefers_canonical_key(self):
        geom = {
            "letter_perimeter_m": 11.6299,
            "cnc_cutting_perimeter_ml": PERIM_ML,
            "face_cutting_perimeter_ml": 13.1322,
        }
        assert resolve_cnc_cutting_perimeter_ml(geom) == PERIM_ML

    def test_led_perimeter_remains_separate_in_preview(self):
        preview = build_cnc_operation_estimate_preview(
            {
                "cnc_cutting_perimeter_ml": PERIM_ML,
                "led_perimeter_ml": 11.6299,
                "return_material_perimeter_ml": 14.5711,
            }
        )
        assert preview["cnc_perimeter_ml"] == PERIM_ML
        assert preview["led_perimeter_ml"] == 11.6299
        assert preview["return_material_perimeter_ml"] == 14.5711

    def test_return_cant_perimeter_separate_from_cnc(self):
        preview = build_cnc_operation_estimate_preview(
            {"cnc_cutting_perimeter_ml": PERIM_ML, "return_material_perimeter_ml": 14.5711}
        )
        assert preview["cnc_perimeter_ml"] != preview["return_material_perimeter_ml"]

    def test_operation_cost_perimeter_times_passes_times_rate(self):
        cost = estimate_cnc_router_cost_eur(
            perimeter_ml=PERIM_ML,
            total_passes=2,
            rate_eur_per_ml_pass=DEFAULT_CNC_RATE_EUR_PER_ML_PASS,
        )
        assert cost == pytest.approx(38.175, rel=1e-4)

    def test_face_plexi_cost_with_bevel_iv4_scale(self):
        preview = build_cnc_operation_estimate_preview(
            {"cnc_cutting_perimeter_ml": PERIM_ML},
            face_bevel_enabled=True,
        )
        assert preview["face_plexi"]["estimated_cost_eur"] == pytest.approx(38.175, rel=1e-4)

    def test_face_plexi_cost_without_bevel_iv4_scale(self):
        preview = build_cnc_operation_estimate_preview(
            {"cnc_cutting_perimeter_ml": PERIM_ML},
            face_bevel_enabled=False,
        )
        assert preview["face_plexi"]["estimated_cost_eur"] == pytest.approx(19.0875, rel=1e-4)

    def test_forex_backing_no_bevel_cost_iv4_scale(self):
        preview = build_cnc_operation_estimate_preview(
            {"cnc_cutting_perimeter_ml": PERIM_ML},
            backing_active=True,
            back_bevel_enabled=False,
        )
        assert preview["forex_backing"]["total_passes"] == 3
        assert preview["forex_backing"]["estimated_cost_eur"] == pytest.approx(57.2625, rel=1e-3)

    def test_forex_backing_with_bevel_cost_iv4_scale(self):
        preview = build_cnc_operation_estimate_preview(
            {"cnc_cutting_perimeter_ml": PERIM_ML},
            backing_active=True,
            back_bevel_enabled=True,
        )
        assert preview["forex_backing"]["total_passes"] == 5
        assert preview["forex_backing"]["estimated_cost_eur"] == pytest.approx(95.4375, rel=1e-3)

    def test_missing_backing_no_forex_cost(self):
        preview = build_cnc_operation_estimate_preview(
            {"cnc_cutting_perimeter_ml": PERIM_ML},
            backing_active=False,
        )
        assert preview["forex_backing"] is None


class TestPricingInputCncPerimeterPatch:
    def test_patches_cnc_cutting_and_bevel_perimeter(self):
        path_geometry = {
            "letter_perimeter_m": 11.6299,
            "cnc_cutting_perimeter_ml": PERIM_ML,
            "led_perimeter_ml": 11.6299,
            "face_cutting_perimeter_ml": 13.1322,
        }
        patched = _patch_quote_input_from_v4_geometry(
            {},
            path_geometry,
            IntakeV4WorkspacePayload(product_binding=IntakeV4ProductBinding(template_code="TPL-VOLUMETRIC-LETTERS")),
        )
        assert patched[CNC_PERIMETER_QUOTE_INPUT_KEY] == PERIM_ML
        assert patched["bevel_perimeter_ml"] == PERIM_ML
        assert patched["back_bevel_enabled"] is False
        assert patched["backing_present"] is False
        assert patched.get("backing_material") is None


class TestIntakeV4BackingGateCostEngine:
    def test_iv4_46499080_like_payload_skips_back_cut(self):
        qi = {
            "intake_source": "intake_v4",
            "backing_present": False,
            "back_bevel_enabled": False,
            "cnc_cutting_perimeter_ml": PERIM_ML,
            "letter_perimeter_m": 11.6299,
            "letter_face_area_m2": 2.0,
            "letter_count": 10,
        }
        out = _build_iv4_quote(qi)
        back = _op_by_code(out, "back_cut")
        face = _op_by_code(out, "face_cnc_cut")
        assert back is not None
        assert back.get("skipped") is True
        assert back.get("skip_reason") == "gate:backing_absent"
        assert back["line_total"] == 0.0
        assert face is not None
        assert face.get("skipped") is not True
        assert face["line_total"] == pytest.approx(38.175, rel=1e-3)

    def test_no_phantom_5726_when_backing_absent(self):
        qi = {
            "intake_source": "intake_v4",
            "backing_present": False,
            "cnc_cutting_perimeter_ml": PERIM_ML,
            "letter_perimeter_m": PERIM_ML,
        }
        back = _op_by_code(_build_iv4_quote(qi), "back_cut")
        assert back is not None
        assert back["line_total"] != pytest.approx(57.26, rel=1e-3)
        assert back["line_total"] == 0.0

    def test_backing_present_no_bevel_three_passes_cost(self):
        qi = {
            "intake_source": "intake_v4",
            "backing_present": True,
            "back_bevel_enabled": False,
            "back_material": "FOREX_10MM",
            "cnc_cutting_perimeter_ml": PERIM_ML,
            "letter_perimeter_m": PERIM_ML,
        }
        back = _op_by_code(_build_iv4_quote(qi), "back_cut")
        assert back is not None
        assert back.get("skipped") is not True
        assert back["line_total"] == pytest.approx(57.2625, rel=1e-3)

    def test_backing_present_bevel_seven_mm_five_passes_cost(self):
        qi = {
            "intake_source": "intake_v4",
            "backing_present": True,
            "back_bevel_enabled": True,
            "back_material": "FOREX_10MM",
            "cnc_cutting_perimeter_ml": PERIM_ML,
            "letter_perimeter_m": PERIM_ML,
        }
        back = _op_by_code(_build_iv4_quote(qi), "back_cut")
        assert back is not None
        assert back["line_total"] == pytest.approx(95.4375, rel=1e-3)
