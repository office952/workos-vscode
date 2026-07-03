"""quote_input_line_gate — paint_finish / volume_finish applicability."""

from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.quote_input_line_gate import should_skip_quote_input_gated_line  # noqa: E402


class TestQuoteInputLineGatePaintFinish(unittest.TestCase):
    def _paint_material(self) -> dict:
        return {
            "material_code": "MAT-VOPSEA-RAL",
            "formula_id": "ceil_quote_input_quantity",
            "formula_params": {
                "conditional": "paint_finish",
                "gate": {"volume_finish": "paint_after_face_miter_bond"},
                "quote_input_key": "paint_tube_count",
            },
        }

    def test_stock_cant_skips_paint_material_without_tubes(self) -> None:
        reason = should_skip_quote_input_gated_line(
            self._paint_material(),
            {"volume_finish": "none", "return_color": "white"},
        )
        self.assertEqual(reason, "gate:paint_finish_inactive")

    def test_paint_mode_requires_active_line(self) -> None:
        reason = should_skip_quote_input_gated_line(
            self._paint_material(),
            {"volume_finish": "paint_after_face_miter_bond"},
        )
        self.assertIsNone(reason)

    def test_stale_paint_tubes_stock_mode_still_skips(self) -> None:
        reason = should_skip_quote_input_gated_line(
            self._paint_material(),
            {
                "volume_finish": "none",
                "paint_tube_count": 3,
                "return_color": "black",
            },
        )
        self.assertEqual(reason, "gate:paint_finish_inactive")


class TestQuoteInputLineGateBackingPresent(unittest.TestCase):
    def _back_cut_op(self) -> dict:
        return {
            "code": "back_cut",
            "formula_id": "perimeter_pass_linear_meter",
            "formula_params": {
                "gate": {"backing_present": True},
                "perimeter_quote_input_key": "cnc_cutting_perimeter_ml",
            },
        }

    def test_back_cut_skipped_when_v4_backing_absent(self) -> None:
        reason = should_skip_quote_input_gated_line(
            self._back_cut_op(),
            {
                "intake_source": "intake_v4",
                "backing_present": False,
                "cnc_cutting_perimeter_ml": 12.725,
            },
        )
        self.assertEqual(reason, "gate:backing_absent")

    def test_back_cut_active_when_v4_backing_present(self) -> None:
        reason = should_skip_quote_input_gated_line(
            self._back_cut_op(),
            {
                "intake_source": "intake_v4",
                "backing_present": True,
                "cnc_cutting_perimeter_ml": 12.725,
            },
        )
        self.assertIsNone(reason)

    def test_legacy_v2_quote_without_backing_present_still_runs(self) -> None:
        reason = should_skip_quote_input_gated_line(
            self._back_cut_op(),
            {"letter_perimeter_m": 18.0, "cnc_cutting_perimeter_ml": 18.0},
        )
        self.assertIsNone(reason)


if __name__ == "__main__":
    unittest.main()
