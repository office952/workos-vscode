"""TPL-VOLUMETRIC-FACE-BACK-PREP V1 — CNC-only production cost draft."""

from __future__ import annotations

import pytest

from schemas.intake_v4 import TPL_VOLUMETRIC_FACE_BACK_PREP_TEMPLATE_CODE
from services.tpl_volumetric_face_back_prep_cost_draft_service import (
    build_tpl_volumetric_face_back_prep_cost_draft_v1,
)
from services.tpl_volumetric_face_back_prep_productsystem_contract import (
    BACK_FOREX_CNC_CUT_PASS_COUNT,
    BACK_FOREX_CNC_SHANFREN_PASS_COUNT,
    CNC_RATE_EUR_PER_ML,
    FACE_CNC_CUT_PASS_COUNT,
    FACE_CNC_SHANFREN_PASS_COUNT,
    OP_CNC_CUT_BACK,
    OP_CNC_CUT_FACE,
    OP_CNC_SHANFREN_BACK,
    OP_CNC_SHANFREN_FACE,
    REGISTRY_FOREX_BACK_CODE,
    REGISTRY_PLEXI_FACE_CODE,
    TASK_CUT_BACK,
    TASK_PACKAGE,
    TASK_PREPARE_CNC,
    TASK_SHANFREN_BACK,
    TASK_SHANFREN_FACE,
)


def _perimeter_payload(
    *,
    p_face: float = 10.0,
    p_back: float = 10.0,
    backing_mode: str = "forex_10_no_bevel",
) -> dict:
    return {
        "quote_geometry": {
            "face_area_m2": 1.0,
            "backing_area_m2": 1.0,
            "cnc_cutting_perimeter_ml": p_face,
            "backing_cnc_cutting_perimeter_ml": p_back,
        },
        "finish_setup": {"backing_mode": backing_mode},
    }


def _base_payload(*, backing_mode: str = "forex_10_no_bevel") -> dict:
    payload = _perimeter_payload(
        p_face=12.725,
        p_back=12.725,
        backing_mode=backing_mode,
    )
    payload["quote_geometry"]["face_area_m2"] = 1.5
    payload["quote_geometry"]["backing_area_m2"] = 1.2
    return payload


def _op_by_key(draft, key: str):
    return next((row for row in draft.operations if row.operation_key == key), None)


def _material_by_registry(draft, code: str):
    return next((row for row in draft.materials if row.registry_code == code), None)


def _face_cnc_total(draft) -> float:
    cut = _op_by_key(draft, OP_CNC_CUT_FACE)
    shanfren = _op_by_key(draft, OP_CNC_SHANFREN_FACE)
    assert cut is not None and shanfren is not None
    assert cut.cost is not None and shanfren.cost is not None
    return cut.cost + shanfren.cost


class TestTplVolumetricFaceBackPrepCostDraftV1:
    def test_face_plexi_pass_counts_and_cost(self):
        draft = build_tpl_volumetric_face_back_prep_cost_draft_v1(
            _perimeter_payload(p_face=10.0, p_back=10.0),
            plexi_unit_price=16.0,
            forex_unit_price=16.0,
        )

        cut = _op_by_key(draft, OP_CNC_CUT_FACE)
        shanfren = _op_by_key(draft, OP_CNC_SHANFREN_FACE)
        assert cut is not None
        assert shanfren is not None
        assert cut.quantity == pytest.approx(10.0)
        assert shanfren.quantity == pytest.approx(10.0)
        assert cut.pass_count == FACE_CNC_CUT_PASS_COUNT
        assert shanfren.pass_count == FACE_CNC_SHANFREN_PASS_COUNT
        assert cut.cost == pytest.approx(10.0 * 1 * CNC_RATE_EUR_PER_ML)
        assert shanfren.cost == pytest.approx(10.0 * 1 * CNC_RATE_EUR_PER_ML)
        assert _face_cnc_total(draft) == pytest.approx(30.0)
        assert cut.perimeter_confidence == "high"
        assert cut.is_vector_perimeter_source is True

    def test_back_forex_without_shanfren_three_passes(self):
        draft = build_tpl_volumetric_face_back_prep_cost_draft_v1(
            _perimeter_payload(p_face=10.0, p_back=10.0, backing_mode="forex_10_no_bevel"),
            plexi_unit_price=16.0,
            forex_unit_price=16.0,
        )

        assert draft.components.back_forex.shanfren_enabled is False
        assert _op_by_key(draft, OP_CNC_SHANFREN_BACK) is None

        back_cut = _op_by_key(draft, OP_CNC_CUT_BACK)
        assert back_cut is not None
        assert back_cut.pass_count == BACK_FOREX_CNC_CUT_PASS_COUNT
        assert back_cut.cost == pytest.approx(10.0 * 3 * CNC_RATE_EUR_PER_ML)

        task_keys = [task.task_key for task in draft.task_drafts]
        assert TASK_SHANFREN_BACK not in task_keys
        assert TASK_CUT_BACK in task_keys

    def test_back_forex_with_shanfren_five_total_passes(self):
        draft = build_tpl_volumetric_face_back_prep_cost_draft_v1(
            _perimeter_payload(p_face=10.0, p_back=10.0, backing_mode="forex_10_with_bevel"),
            plexi_unit_price=16.0,
            forex_unit_price=16.0,
        )

        back_cut = _op_by_key(draft, OP_CNC_CUT_BACK)
        shanfren_back = _op_by_key(draft, OP_CNC_SHANFREN_BACK)
        assert back_cut is not None
        assert shanfren_back is not None
        assert back_cut.pass_count == 3
        assert back_cut.cost == pytest.approx(45.0)
        assert shanfren_back.pass_count == BACK_FOREX_CNC_SHANFREN_PASS_COUNT
        assert shanfren_back.cost == pytest.approx(10.0 * 2 * CNC_RATE_EUR_PER_ML)
        assert back_cut.cost + shanfren_back.cost == pytest.approx(75.0)

    def test_vector_perimeter_missing_no_fallback_cost(self):
        draft = build_tpl_volumetric_face_back_prep_cost_draft_v1(
            {
                "quote_geometry": {
                    "face_area_m2": 1.0,
                    "backing_area_m2": 1.0,
                },
                "finish_setup": {"backing_mode": "forex_10_no_bevel"},
            },
            plexi_unit_price=16.0,
            forex_unit_price=16.0,
        )

        cut = _op_by_key(draft, OP_CNC_CUT_FACE)
        back_cut = _op_by_key(draft, OP_CNC_CUT_BACK)
        assert cut is not None
        assert back_cut is not None
        assert cut.status == "manual_required"
        assert cut.cost is None
        assert back_cut.status == "manual_required"
        assert back_cut.cost is None
        assert any(w.code == "vector_perimeter_missing_or_low_confidence" for w in draft.warnings)
        assert draft.totals.total_internal_cost is None

    def test_no_face_perimeter_fallback_for_back_cnc(self):
        """Face vector perimeter present must not substitute missing back vector perimeter."""
        draft = build_tpl_volumetric_face_back_prep_cost_draft_v1(
            {
                "quote_geometry": {
                    "face_area_m2": 1.0,
                    "backing_area_m2": 1.0,
                    "cnc_cutting_perimeter_ml": 10.0,
                },
                "finish_setup": {"backing_mode": "forex_10_no_bevel"},
            },
            plexi_unit_price=16.0,
            forex_unit_price=16.0,
        )

        face_cut = _op_by_key(draft, OP_CNC_CUT_FACE)
        back_cut = _op_by_key(draft, OP_CNC_CUT_BACK)
        assert face_cut is not None and face_cut.status == "calculated"
        assert back_cut is not None and back_cut.status == "manual_required"
        assert back_cut.cost is None

    def test_no_real_side_effects(self):
        draft = build_tpl_volumetric_face_back_prep_cost_draft_v1(
            _base_payload(),
            plexi_unit_price=16.0,
            forex_unit_price=16.0,
        )

        assert draft.creates_real_tasks is False
        assert draft.consumes_stock is False
        assert draft.creates_quote is False
        assert draft.preview_only is True
        for task in draft.task_drafts:
            assert task.creates_real_task is False
            assert task.preview_only is True

    def test_missing_material_price_blocks_total(self):
        draft = build_tpl_volumetric_face_back_prep_cost_draft_v1(
            _base_payload(),
            plexi_unit_price=None,
            plexi_price_source="missing",
            forex_unit_price=16.0,
        )

        plexi = _material_by_registry(draft, REGISTRY_PLEXI_FACE_CODE)
        assert plexi is not None
        assert plexi.status == "missing_price"
        assert REGISTRY_PLEXI_FACE_CODE in draft.missing_prices
        assert draft.totals.total_internal_cost is None

    def test_task_draft_order_without_back_shanfren(self):
        draft = build_tpl_volumetric_face_back_prep_cost_draft_v1(
            _base_payload(backing_mode="forex_10_no_bevel"),
            plexi_unit_price=16.0,
            forex_unit_price=16.0,
        )
        ordered = sorted(draft.task_drafts, key=lambda t: t.order_index)
        assert ordered[0].task_key == TASK_PREPARE_CNC
        assert ordered[-1].task_key == TASK_PACKAGE
        assert ordered[-2].task_key == "CLEAN_AND_CHECK_PARTS"

    def test_shanfren_forex_query_override(self):
        draft = build_tpl_volumetric_face_back_prep_cost_draft_v1(
            _base_payload(backing_mode="forex_10_no_bevel"),
            shanfren_forex_override=True,
            plexi_unit_price=16.0,
            forex_unit_price=16.0,
        )
        assert draft.components.back_forex.shanfren_enabled is True
        shanfren_back = _op_by_key(draft, OP_CNC_SHANFREN_BACK)
        assert shanfren_back is not None
        assert shanfren_back.pass_count == 2

    def test_cnc_face_contour_operational_cost_is_sum_of_pass_rows(self):
        draft = build_tpl_volumetric_face_back_prep_cost_draft_v1(
            _base_payload(),
            plexi_unit_price=16.0,
            forex_unit_price=16.0,
        )
        assert _face_cnc_total(draft) == pytest.approx(12.725 * CNC_RATE_EUR_PER_ML * 2)

    def test_legacy_default_payload_material_and_back_three_pass_cost(self):
        draft = build_tpl_volumetric_face_back_prep_cost_draft_v1(
            _base_payload(),
            plexi_unit_price=16.0,
            forex_unit_price=16.0,
        )

        assert draft.template_key == TPL_VOLUMETRIC_FACE_BACK_PREP_TEMPLATE_CODE
        plexi = _material_by_registry(draft, REGISTRY_PLEXI_FACE_CODE)
        assert plexi is not None
        assert plexi.cost == pytest.approx(24.0)

        back_cut = _op_by_key(draft, OP_CNC_CUT_BACK)
        assert back_cut is not None
        assert back_cut.cost == pytest.approx(12.725 * 3 * CNC_RATE_EUR_PER_ML)
